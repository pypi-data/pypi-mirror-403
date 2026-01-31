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
from typing import TYPE_CHECKING

from clusterondemand.clusternameprefix import clusterprefix_ns

if TYPE_CHECKING:
    from typing import Any
    from azure.core.polling import LROPoller
    from azure.mgmt.compute.models import VirtualMachine
from clusterondemand.utils import confirm, confirm_ns, log_no_clusters_found, multithread_run
from clusterondemandazure.azure_actions.credentials import AzureApiHelper
from clusterondemandazure.cluster import Cluster
from clusterondemandazure.utils import filter_vms_by_state
from clusterondemandconfig import ConfigNamespace, config

from .configuration import azurecommon_ns

config_ns = ConfigNamespace("azure.cluster.start")
config_ns.import_namespace(azurecommon_ns)
config_ns.import_namespace(clusterprefix_ns)
config_ns.import_namespace(confirm_ns)

config_ns.add_repeating_positional_parameter(
    "filters",
    require_value=True,
    help="Cluster names or patterns. Wildcards are supported (e.g: \\*)",
)
config_ns.add_switch_parameter("dry_run", help="Do not actually start the VMs")
config_ns.add_switch_parameter(
    "force",
    help="start cluster VMs disregarding their power state. Useful if VM power state cannot be determined, "
    "or unknown state found",
)

log = logging.getLogger("cluster-on-demand")

# https://learn.microsoft.com/en-us/azure/virtual-machines/states-billing
STATES_TO_START = [
    "creating",
    "stopping",
    "stopped",
    "deallocated",
    "deallocating",
]


def run_command() -> None:
    azure_api_client = AzureApiHelper.from_config(config)

    clusters = list(Cluster.find_clusters(azure_api_client, config["filters"]))
    if not clusters:
        log_no_clusters_found("start")
        return

    if not confirm(
        f"This will start head nodes for clusters: "
        f"{', '.join(cluster.name for cluster in clusters)}. "
        f"Continue?"
    ):
        return

    clusters_to_start: list[Cluster] = []
    vms_to_start: list[VirtualMachine] = []
    if config["force"]:
        vms_to_start = [vm for cluster in clusters for vm in cluster.head_nodes]
    else:
        for cluster in clusters:
            assert cluster.resource_group.name is not None, f"Resource group name is None for cluster {cluster.name}"
            vms = filter_vms_by_state(
                azure_api_client=azure_api_client,
                vms=cluster.head_nodes,
                resource_group_name=cluster.resource_group.name,
                power_states=STATES_TO_START,
            )
            if not vms:
                log.info(f"No stopped head nodes were found for cluster: {cluster.name}")
            else:
                vms_to_start += vms
                clusters_to_start.append(cluster)

    if not vms_to_start:
        return

    log.info(
        f"Starting head nodes for clusters: "
        f"{', '.join(cluster.name for cluster in clusters_to_start)}"
    )

    start_vms(azure_api_client, vms_to_start, dry_run=config["dry_run"])


def start_vms(azure_api_client: AzureApiHelper, vms: list[VirtualMachine], dry_run: bool) -> None:
    log.debug(f"Starting VMs: {', '.join(vm.name for vm in vms if vm and vm.name)}")  # type: ignore
    if dry_run:
        return

    async_start_promises: list[LROPoller[Any]] = []
    for vm in vms:
        assert vm.id is not None, "VM id is None"
        async_start_promises.append(
            azure_api_client.compute_client.virtual_machines.begin_start(
                resource_group_name=vm.id.split("/")[4],
                vm_name=vm.name,
            )
        )

    multithread_run(lambda p: p.wait(), async_start_promises, config["max_threads"])
    log.debug(f"Started VMs: {', '.join(vm.name for vm in vms if vm and vm.name)}")  # type: ignore
