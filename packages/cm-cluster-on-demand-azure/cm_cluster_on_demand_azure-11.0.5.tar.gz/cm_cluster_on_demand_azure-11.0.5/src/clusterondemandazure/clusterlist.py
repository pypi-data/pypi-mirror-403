# Copyright (c) 2004-2026 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from __future__ import annotations

import logging
from collections import defaultdict
from dataclasses import dataclass
from functools import cache
from typing import TYPE_CHECKING, Any

from azure.core.exceptions import HttpResponseError, ResourceNotFoundError
from azure.mgmt.compute.models import VirtualMachine

if TYPE_CHECKING:
    from azure.mgmt.compute import ComputeManagementClient
    from azure.mgmt.resource.resources.models import ResourceGroup

import clusterondemand.clustercreate
from clusterondemand.clusternameprefix import clusterprefix_ns
from clusterondemand.codoutput.sortingutils import ClusterIPs, SortableData
from clusterondemand.exceptions import CODException
from clusterondemand.utils import log_no_clusters_found
from clusterondemandazure.azure_actions.credentials import AzureApiHelper
from clusterondemandazure.base import ClusterCommand
from clusterondemandazure.cluster import Cluster
from clusterondemandazure.utils import get_vm_power_state
from clusterondemandconfig import ConfigNamespace, config

from .configuration import azurecommon_ns

log = logging.getLogger("cluster-on-demand")

ALL_COLUMNS = [
    ("cluster_name", "Cluster Name"),
    ("head_node_name", "Head Node Name"),
    ("resource_group_name", "Resource group"),
    ("ip", "IP"),
    ("power_state", "State"),
    ("location", "Location"),
    ("head_node_vmsize", "Head Node VM Size"),
    ("head_node_cpu", "Head Node CPU Cores"),
    ("head_node_ram", "Head Node RAM (MB)"),
    ("created", "Image Created"),
    ("image_name", "Image Name"),
]

DEFAULT_COLUMNS = [
    "cluster_name",
    "resource_group_name",
    "ip",
    "power_state",
    "location",
    "head_node_vmsize",
    "created",
    "image_name",
]

_HA_NODE_A_SUFFIX = "-a"
_HA_NODE_B_SUFFIX = "-b"
_HA_IP_SUFFIX = "-shared-ip"

config_ns = ConfigNamespace("azure.cluster.list", help_section="list output parameters")
config_ns.import_namespace(clusterondemand.configuration.clusterlist_ns)
config_ns.import_namespace(clusterprefix_ns)
config_ns.import_namespace(azurecommon_ns)
config_ns.add_enumeration_parameter(
    "sort",
    choices=[column[0] for column in ALL_COLUMNS],
    default=["created"],
    help="Sort results by one (or two) of the columns",
)
config_ns.add_enumeration_parameter(
    "columns",
    choices=[column[0] for column in ALL_COLUMNS],
    default=DEFAULT_COLUMNS,
    help="Provide space separated set of columns to be displayed",
)
config_ns.add_repeating_positional_parameter(
    "filters",
    default=["*"],
    require_value=True,
    help="Cluster names or patterns to be listed. Default: all clusters. Wildcards are supported (e.g: \\*)",
)


def run_command() -> None:
    ClusterList().run()


class ClusterList(ClusterCommand):

    def run(self) -> None:
        try:
            self._validate_params()
        except HttpResponseError as e:
            if e.error and e.error.code and "SubscriptionNotFound" in e.error.code:
                raise CODException(str(e))
            AzureApiHelper.log_error_details(e)
            raise e

        rows = []

        clusters = list(Cluster.find_clusters(self.azure_api, config["filters"]))
        if not clusters:
            log_no_clusters_found("list")
            return

        for cluster in clusters:
            rows.append(
                get_cluster_data(self.azure_api, cluster)
            )

        cols_id = config["columns"]
        if not cols_id:
            cols_id = DEFAULT_COLUMNS

        table = SortableData(all_headers=ALL_COLUMNS, requested_headers=cols_id, rows=rows)
        table.sort(*config["sort"])

        print(table.output(output_format=config["output_format"]))

    def _validate_params(self) -> None:
        self._validate_access_credentials()


@dataclass(frozen=True)
class NodeInfo:
    name: str
    vm: VirtualMachine
    vm_size: str | None
    vm_power_state: str | None
    cpu_cores: int | None
    ram_in_mb: int | None
    image_creation_date: str | None
    image_name: str | None


def _get_node_info(azure_api: AzureApiHelper, r_group: ResourceGroup, vm: VirtualMachine) -> NodeInfo | None:
    assert vm.name is not None, "VM name cannot be None"
    assert r_group.name is not None, "Resource group name cannot be None"

    specs = defaultdict(lambda: "N/A")

    if "head_node_cpu" in config["columns"] or "head_node_ram" in config["columns"]:
        specs = _get_location_vmsize_details(
            azure_api.compute_client,
            r_group.location,
            vm.hardware_profile.vm_size,
        )

    return NodeInfo(
        name=vm.name,
        vm=vm,
        vm_size=vm.hardware_profile.vm_size,
        vm_power_state=get_vm_power_state(azure_api, r_group.name, vm),
        cpu_cores=specs["number_of_cores"],
        ram_in_mb=specs["memory_in_mb"],
        image_creation_date=vm.tags.get(
            "BCM Image created at", vm.tags.get("image_creation_date", None)
        ),
        image_name=vm.tags.get("BCM Image name", vm.tags.get("image_name", None)),
    )


def _get_vm_ips(
    azure_api: AzureApiHelper,
    r_group: ResourceGroup,
    vm: VirtualMachine,
    ip_names: list[str],
) -> tuple[str | None, str | None]:
    assert r_group.name, "Resource group name cannot be None"
    public_ip, private_ip = None, None
    for ip_name in ip_names:
        try:
            public_ip = azure_api.network_client.public_ip_addresses.get(
                r_group.name, ip_name
            ).ip_address
        except ResourceNotFoundError:
            pass
        if public_ip is not None:
            break
    if public_ip is None:
        log.debug(f"Failed getting public ip for head node: {vm.name}")

    # There are 2 reasons why Public IP might be missing:
    # 1. Azure malfunction or user error, removed public IP (bad case)
    # 2. Cluster was created without public IP, as customer has infrastructure to reach Azure cloud (E.g. on-site VPN)
    # In either case, we need to get private IP to log something for the user. But as we can't tell if we're dealing
    # with a bad case, we log warning in any case
    if (
        not public_ip
        and vm
        and vm.network_profile
        and vm.network_profile.network_interfaces
    ):
        try:
            # cod interface and ip configuration is primary, even if user manually added interfaces
            interfaces = vm.network_profile.network_interfaces
            cod_interface = next(i for i in interfaces if i.primary)
            if cod_interface.id:
                nic_name = " ".join(cod_interface.id.split("/")[-1:])
                network_interface = azure_api.network_client.network_interfaces.get(
                    r_group.name, nic_name
                )
                if network_interface.ip_configurations:
                    private_ip = next(
                        ip_conf.private_ip_address
                        for ip_conf in network_interface.ip_configurations
                        if ip_conf.primary
                    )
        except Exception as e:
            log.debug(f"Failed getting head node private ip: {e}")
    return public_ip, private_ip


def get_cluster_data(azure_api: AzureApiHelper, cluster: Cluster) -> list[str | ClusterIPs | None]:
    """
    Return list containing cluster information of a given resource group.

    :param azure_api: instance of AzureApiHelper
    :param r_group: resource group object
    :return: cluster information in the following format:
        [
            cluster_name,
            head_node_name,
            ip,
            location,
            resource_group_name,
            vm_size,
            cpu_cores,
            ram,
            image_creation_date,
            image_name,
        ]
    """
    missing_resources = []
    cluster_name = cluster.name

    head_node_a, head_node_b = None, None
    if cluster.primary_head_node:
        head_node_a = _get_node_info(
            azure_api, cluster.resource_group, cluster.primary_head_node
        )
    if cluster.secondary_head_node:
        head_node_b = _get_node_info(
            azure_api, cluster.resource_group, cluster.secondary_head_node,
        )

    public_ip_a, private_ip_a = None, None
    if head_node_a is not None:
        public_ip_a, private_ip_a = _get_vm_ips(
            azure_api, cluster.resource_group, head_node_a.vm, [f"{head_node_a.name}-ip", "head-node-public-ip"]
        )

    public_ip_b, private_ip_b = None, None
    if head_node_b is not None:
        public_ip_b, private_ip_b = _get_vm_ips(
            azure_api, cluster.resource_group, head_node_b.vm, [f"{head_node_b.name}-ip"]
        )

    shared_ip = None
    try:
        assert cluster.resource_group.name is not None, "Resource group name cannot be None"
        shared_ip = azure_api.network_client.public_ip_addresses.get(
            cluster.resource_group.name, cluster_name + _HA_IP_SUFFIX
        ).ip_address
    except Exception as e:
        log.debug(f"Failed getting public ip: {e}")

    is_ha = shared_ip is not None or head_node_b is not None

    if head_node_a is None or is_ha and head_node_b is None:
        missing_resources.append("head node")

    if public_ip_a is None or is_ha and (public_ip_b is None or shared_ip is None):
        missing_resources.append("public ip")

    head_node_a_name = head_node_a.name if head_node_a else "missing"
    head_node_b_name = head_node_b.name if head_node_b else "missing"
    head_node_a_vm_size = head_node_a.vm_size if head_node_a else "N/A"
    head_node_b_vm_size = head_node_b.vm_size if head_node_b else "N/A"
    head_node_a_power_state = head_node_a.vm_power_state if head_node_a else "N/A"
    head_node_b_power_state = head_node_b.vm_power_state if head_node_b else "N/A"
    head_node_a_cpu_cores = str(head_node_a.cpu_cores) if head_node_a else "N/A"
    head_node_b_cpu_cores = str(head_node_b.cpu_cores) if head_node_b else "N/A"
    head_node_a_ram_in_mb = str(head_node_a.ram_in_mb) if head_node_a else "N/A"
    head_node_b_ram_in_mb = str(head_node_b.ram_in_mb) if head_node_b else "N/A"
    head_node_a_image_creation_date = (
        head_node_a.image_creation_date if head_node_a else None
    ) or "N/A"
    head_node_b_image_creation_date = (
        head_node_b.image_creation_date if head_node_b else None
    ) or "N/A"
    head_node_a_image_name = head_node_a.image_name if head_node_a else "N/A"
    head_node_b_image_name = head_node_b.image_name if head_node_b else "N/A"

    if is_ha:
        head_node_name_col = "\n".join(
            [
                head_node_a_name + " (A)" if head_node_a is not None else "missing",
                head_node_b_name + " (B)" if head_node_b is not None else "missing",
            ]
        )
        head_node_state_col = "\n".join(
            [head_node_a_power_state or "N/A", head_node_b_power_state or "N/A"]
        )
        head_node_vm_size_col = "\n".join(
            [head_node_a_vm_size or "N/A", head_node_b_vm_size or "N/A"]
        )
        head_node_cpu_cores_col = "\n".join(
            [head_node_a_cpu_cores or "N/A", head_node_b_cpu_cores or "N/A"]
        )
        head_node_ram_in_mb_col = "\n".join(
            [head_node_a_ram_in_mb or "N/A", head_node_b_ram_in_mb or "N/A"]
        )
        head_node_image_creation_date_col = "\n".join(
            [head_node_a_image_creation_date or "N/A", head_node_b_image_creation_date or "N/A"]
        )
        head_node_image_name_col = "\n".join(
            [head_node_a_image_name or "N/A", head_node_b_image_name or "N/A"]
        )
    else:
        head_node_name_col = head_node_a_name or "N/A"
        head_node_state_col = head_node_a_power_state or "N/A"
        head_node_vm_size_col = head_node_a_vm_size or "N/A"
        head_node_cpu_cores_col = head_node_a_cpu_cores or "N/A"
        head_node_ram_in_mb_col = head_node_a_ram_in_mb or "N/A"
        head_node_image_creation_date_col = head_node_a_image_creation_date or "N/A"
        head_node_image_name_col = head_node_a_image_name or "N/A"

    cluster_ips = ClusterIPs(
        primary_ip=public_ip_a,
        primary_private_ip=private_ip_a,
        secondary_ip=public_ip_b,
        secondary_private_ip=private_ip_b,
        shared_ip=shared_ip,
    )

    if missing_resources:
        log.warning(
            f"Resource(s) {', '.join(missing_resources)!r} for cluster {cluster_name} cannot be found, "
            f"this could be a sign of a broken deployment. You can remove the cluster by running: "
            f"cm-cod-azure cluster delete {cluster_name}"
        )

    return [
        cluster_name,
        head_node_name_col,
        cluster.resource_group.name,
        cluster_ips,
        head_node_state_col,
        cluster.resource_group.location,
        head_node_vm_size_col,
        head_node_cpu_cores_col,
        head_node_ram_in_mb_col,
        head_node_image_creation_date_col,
        head_node_image_name_col,
    ]


@cache
def _get_location_vmsize_details(
    compute_client: ComputeManagementClient, location: str, vmsize_name: str
) -> dict[str, Any]:
    """
    Return details of virtual machine size.

    If vmsize is not cached by previous calls, it
    pulls all vmsizes, finds the one that matches the requested name
    and returns its properties

    :param compute_client: azure sdk compute client
    :param location: location of the given vmsize
    :param vmsize_name: name of the vmsize
    :return: a dictionary of the vmsize information in the following format :
        {
            "number_of_cores": number_of_cores,
            "memory_in_mb": memory_in_mb,
        }
    """
    paged_vmsizes = compute_client.virtual_machine_sizes.list(location=location)
    return next(
        (
            {
                "number_of_cores": vmsize.number_of_cores,
                "memory_in_mb": vmsize.memory_in_mb,
            }
            for vmsize in paged_vmsizes
            if vmsize.name and vmsize.name.lower() == vmsize_name.lower()
        ),
        {
            "number_of_cores": None,
            "memory_in_mb": None,
        },
    )
