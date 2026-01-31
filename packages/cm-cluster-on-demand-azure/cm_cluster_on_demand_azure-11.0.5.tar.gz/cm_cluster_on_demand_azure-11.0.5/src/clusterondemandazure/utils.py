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

import ipaddress
import logging
from typing import TYPE_CHECKING

from clusterondemand import utils

if TYPE_CHECKING:
    from azure.mgmt.compute.models import ResourceSku, VirtualMachine

    from .azure_actions.credentials import AzureApiHelper

log = logging.getLogger("cluster-on-demand")

COD_RESOURCE_GROUP_SUFFIX = "_cod_resource_group"


def get_resource_skus(azure_api: AzureApiHelper, location: str | None, resource_type: str) -> list[ResourceSku]:
    """
    Get Azure Resource SKUs filtered by location and resource type.

    :param azure_api: Azure API helper instance
    :param location: Azure location/region to filter by (None for all locations)
    :param resource_type: Type of resource (e.g., "virtualMachines", "disks")
    :return: List of filtered Resource SKUs
    """
    location_filter = f"location eq '{location}'" if location else None
    resource_skus = azure_api.compute_client.resource_skus.list(filter=location_filter)
    res_skus = [sku for sku in resource_skus if sku.resource_type == resource_type]
    return res_skus


def name_from_r_group(r_group_name: str) -> str:
    """
    Obtain name of resource group.

    :param r_group_name: resource group name
    :return: extracted cluster name from group name
    """
    return r_group_name.removesuffix(COD_RESOURCE_GROUP_SUFFIX)


def get_detailed_vm(azure_api_client: AzureApiHelper, resource_group_name: str, vm: VirtualMachine) -> VirtualMachine:
    """
    Unless explicitely requested, Azure API returns a VM object without "instanceView" data.
    Since we don't always need this data, we don't get it by default,
    but provide a helper function to fetch it here.
    """
    return azure_api_client.compute_client.virtual_machines.get(  # type: ignore
        resource_group_name=resource_group_name,
        vm_name=vm.name,
        expand="instanceView",
    )


def get_vm_power_state(azure_api_client: AzureApiHelper, resource_group_name: str, vm: VirtualMachine) -> str | None:
    if not vm.instance_view:
        vm = get_detailed_vm(azure_api_client, resource_group_name, vm)

    power_state_warning = (
        f"Unable to determine power state of VM {vm.name}."
        f"if trying to start/stop the cluster, try using --force flag."
    )

    if not vm.instance_view or not vm.instance_view.statuses:
        log.warning(power_state_warning)
        return None

    power_state = next(
        (
            status
            for status in vm.instance_view.statuses
            if status.code and status.code.startswith("PowerState")
        ),
        None,
    )
    if not power_state:
        # API may not fetch the power state of a VM that just changed the state VM, retrying virtual_machines.get()
        # is excessive for this use-case. Let's just warn the user instead
        log.warning(power_state_warning)
        return None

    if power_state.code:
        return power_state.code.split("/")[1].lower()
    return None


def filter_vms_by_state(
    azure_api_client: AzureApiHelper,
    vms: list[VirtualMachine],
    resource_group_name: str,
    power_states: list[str],
) -> list[VirtualMachine]:
    # We determine the power state based on VM -> instance_view -> statuses. There are 2 elements,
    # [PowerState, ProvisioningState]. Those states are found using list(), then get() methods.
    # Another method list_all() does not find all the information,
    # list_all(status_only=True) doesn't find tags, status_only=False doesn't find power state.
    detailed_vms = [  # next(detailed_vms).as_dict() has all VM properties
        get_detailed_vm(azure_api_client, resource_group_name, vm) for vm in vms
    ]

    filtered_vms = []
    for vm in detailed_vms:
        power_state_name = get_vm_power_state(azure_api_client, resource_group_name, vm)

        if power_state_name in power_states:
            filtered_vms.append(vm)
        else:
            log.debug(f"VM {vm.name} is in state '{power_state_name}', ignoring")

    if not filtered_vms:
        log.debug(
            f"Didn't find any VMs in resource group {resource_group_name} "
            f"in requested power states: {', '.join(power_states)}"
        )
        return []

    return filtered_vms


def get_vmsize_arch(vm_skus: list[ResourceSku], node_type: str) -> str | None:
    """
    Returns the COD machine architecture string for the given Azure VM size.
    :param node_type: The name of the Azure VM size.
    :return: The corresponding COD architecture string (e.g., 'aarch64', 'x86_64'), or None if not found.
    """

    def get_cod_machine_arch(vm_size: ResourceSku) -> str | None:
        azure_to_cod: dict[str | None, str] = {"Arm64": "aarch64", "x64": "x86_64"}
        # For a VMSize object, the CPU architecture is described in the "capabilities" name-value pair
        # with name == CpuArchitectureType
        vmsize_arch = [
            capability.value
            for capability in vm_size.capabilities  # type: ignore
            if capability.name == "CpuArchitectureType"
        ]
        assert len(vmsize_arch) == 1, (
            f"VM size {vm_size.name} has multiple CPU architectures: {vmsize_arch}"
        )
        return azure_to_cod.get(vmsize_arch[0])

    # Get the VM size object from the list of VM sizes
    vm_size = [vm_size for vm_size in vm_skus if vm_size.name == node_type]
    assert len(vm_size) == 1, f"VM size {node_type} not found in VM SKUs."
    # Get the VM size architecture in COD format
    return get_cod_machine_arch(vm_size[0])


def validate_vmsizes_arch(
    cod_arch: str, vm_skus: list[ResourceSku], vm_size: str, node_string: str
) -> str:
    machine_arch = get_vmsize_arch(vm_skus, vm_size)
    return utils.validate_arch_vs_machine_arch(
        cod_arch, machine_arch, vm_size, node_string
    )


def normalize_ip_addresses(whitelist_ips: list[str]) -> list[str]:
    """
    Handle small IPv4 prefixes by removing the /32 suffix and expanding the /31 suffix.
    This is necessary because IPRule does not support /31 and /32 prefixes.
    See also RFC3021 (https://datatracker.ietf.org/doc/html/rfc3021)

    Shorter prefixes are returned as-is.
    """
    # Split the whitelist into 3 parts: Prefix /32 ips, prefix /31 ips, and the rest.
    pref32_list = [ip for ip in whitelist_ips if ip.endswith("/32")]
    pref31_list = [ip for ip in whitelist_ips if ip.endswith("/31")]
    rest_list = [ip for ip in whitelist_ips if (not ip.endswith("/31") and not ip.endswith("/32"))]

    # Remove /32 from each IP address in the pref32_list
    modified_whitelist: list[str] = [ip[:-3] for ip in pref32_list]

    # Expand /31 prefixes
    pref31_networks: list[ipaddress.IPv4Network] = [ipaddress.IPv4Network(ip) for ip in pref31_list]
    pref31_list_expanded = [str(item) for net in pref31_networks for item in net]
    modified_whitelist += pref31_list_expanded

    # Finally, append the rest of the original whitelist prefixes unmodified
    modified_whitelist += rest_list

    return sorted(modified_whitelist)
