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
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from azure.core.polling import LROPoller
    from azure.mgmt.compute.models import VirtualMachine

from clusterondemand.bcm_version import BcmVersion
from clusterondemand.clusternameprefix import clusterprefix_ns
from clusterondemand.utils import confirm, confirm_ns, log_no_clusters_found, multithread_run
from clusterondemandazure.azure_actions.credentials import AzureApiHelper
from clusterondemandazure.cluster import Cluster
from clusterondemandazure.utils import filter_vms_by_state
from clusterondemandconfig import ConfigNamespace, config
from clusterondemandconfig.configuration_validation import cannot_use_together

from .configuration import azurecommon_ns

config_ns = ConfigNamespace("azure.cluster.stop")
config_ns.import_namespace(azurecommon_ns)
config_ns.import_namespace(clusterprefix_ns)
config_ns.import_namespace(confirm_ns)

config_ns.add_repeating_positional_parameter(
    "filters",
    help="Cluster names or patterns. Wildcards are supported (e.g: \\*)",
)
config_ns.add_parameter(
    "resource_group",
    help="Name of resource group where cluster VMs will be stopped. Only the VMs created by COD will be stopped",
)
config_ns.add_switch_parameter("dry_run", help="Do not actually stop the resources")
config_ns.add_switch_parameter(
    "force",
    help="Stop cluster VMs disregarding their power state. Useful if VM power state cannot be determined, "
    "or unexpected state found",
)

config_ns.add_validation(cannot_use_together("filters", "resource_group"))

log = logging.getLogger("cluster-on-demand")

# https://learn.microsoft.com/en-us/azure/virtual-machines/states-billing
STATES_TO_STOP = [
    "creating",
    "starting",
    "stopping",
    "stopped",
    "running",
]


def run_command() -> None:
    azure_api_client = AzureApiHelper.from_config(config)

    clusters = list(Cluster.find_clusters(azure_api_client, config["filters"]))

    if not clusters:
        log_no_clusters_found("stop")
        return

    if not confirm(
        f"This will stop (deallocate) all cluster VMs in resource groups: "
        f"{', '.join(cluster.name for cluster in clusters)}. Continue?"
    ):
        return

    clusters_to_stop: list[Cluster] = []
    vms_to_stop: list[VirtualMachine] = []
    if config["force"]:
        vms_to_stop = [vm for cluster in clusters for vm in cluster.head_nodes + cluster.compute_nodes]
    else:
        for cluster in clusters:
            assert cluster.resource_group.name is not None, "Resource group name cannot be None"
            vms = filter_vms_by_state(
                azure_api_client=azure_api_client,
                vms=cluster.head_nodes + cluster.compute_nodes,
                resource_group_name=cluster.resource_group.name,
                power_states=STATES_TO_STOP,
            )
            if not vms:
                log.info(
                    f"No running VMs were found for cluster: {cluster.name}"
                )
                continue
            vms_to_stop += vms
            clusters_to_stop.append(cluster)

    # Warn users trying to stop pre-v11 clusters, deployed in pre-existing RGs. Cnodes of such clusters
    # are not tagged with "BCM Cluster" tag
    pre_v11_clusters = [
        cluster for cluster in clusters_to_stop
        if cluster.version and BcmVersion(cluster.version).release < (11, 0)
    ]
    for cluster in pre_v11_clusters:
        assert cluster.resource_group.name is not None, "Resource group name cannot be None"
        has_vms_in_rg = any(
            vm for vm in vms_to_stop
            if vm.id and vm.id.split("/")[4].lower() == cluster.resource_group.name.lower()
        )
        if has_vms_in_rg:
            log.warning(
                f"Cluster {cluster.name} seems to be running an older version of BCM. "
                f"Since older clusters were not fully tagged, we "
                f"can't reliably link all BCM resources to the cluster, so *all* compute nodes in "
                f"the resource group {cluster.resource_group.name!r} (including other clusters' nodes in any)"
                f" will be stopped"
            )

    if vms_to_stop:
        log.info(
            f"Stopping all VMs for clusters: "
            f" {', '.join(cluster.name for cluster in clusters_to_stop)}"
        )
        deallocate_vms(azure_api_client, vms_to_stop, dry_run=config["dry_run"])


def deallocate_vms(azure_api_client: AzureApiHelper, vms: list[VirtualMachine], dry_run: bool) -> None:
    vm_names: list[str] = []
    for vm in vms:
        if vm.name is not None:  # Somehow the exact same logic in list comprehension doesn't satisfy mypy
            vm_names.append(vm.name)

    log.debug(f"Deallocating VMs {', '.join(vm_names)}")
    if dry_run:
        return

    async_deallocate_promises: list[LROPoller[Any]] = []
    for vm in vms:
        assert vm.id is not None, "VM ID cannot be None"
        assert vm.name is not None, "VM name cannot be None"
        promise = azure_api_client.compute_client.virtual_machines.begin_deallocate(
            resource_group_name=vm.id.split("/")[4],
            vm_name=vm.name,
        )
        async_deallocate_promises.append(promise)

    multithread_run(lambda p: p.wait(), async_deallocate_promises, config["max_threads"])

    log.debug(f"Deallocated VMs {', '.join(vm_names)}")
