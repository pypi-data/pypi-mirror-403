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

import json
import logging
import typing
from functools import cached_property
from typing import Any

import clusterondemand
import clusterondemand.configuration
from clusterondemand.codoutput.sortingutils import SortableData
from clusterondemand.exceptions import CODException
from clusterondemandconfig import ConfigNamespace, config

from .azure_actions.credentials import AzureApiHelper
from .configuration import azurecommon_ns
from .utils import get_resource_skus

if typing.TYPE_CHECKING:
    from azure.mgmt.compute.models import ResourceSku

VMCapabilitiesMap = dict[str, Any]  # Maps capability to value.
VMSpecsMap = dict[str, VMCapabilitiesMap]  # Maps VM flavor/size to capabilities map.
LocationToVMSizeMap = dict[str, list[str]]  # Maps location to VM types in location.

columns = [
    ("location", "Location"),
    ("vmsizes", "VMSizes"),
    ("ram", "Ram (GB)"),
    ("cpu", "CPU Cores"),
    ("max_disks", "Max Data Disk"),
    ("accelerated_networking", "Accelerated Networking"),
    ("premium_storage", "Premium Storage"),
]
log = logging.getLogger("cluster-on-demand")


HR = "---------------------------------------------------------------------"


config_ns = ConfigNamespace("azure.vmsize.list", "list output parameters")
config_ns.import_namespace(clusterondemand.configuration.clusterlist_ns)
config_ns.import_namespace(azurecommon_ns)
config_ns.add_enumeration_parameter(
    "sort",
    default=["location"],
    choices=[col[0] for col in columns],
    help="Column according to which the table should be sorted (asc order)."
)
config_ns.add_parameter(
    "location",
    help="Only show vmsizes for this location."
)
config_ns.override_imported_parameter(
    "output_format",
    choices=["table", "json"],
    help_varname=None,
)


def run_command() -> None:
    return VMSizesList().run()


class VMSizesList:

    @staticmethod
    def list_locations(azure_api: AzureApiHelper) -> list[str]:
        """Return list of available locations in an Azure subscription."""
        locations = []
        paged_location = azure_api.subscription_client.subscriptions.list_locations(azure_api.subscription_id)

        next_page = next(paged_location)
        while next_page:
            if not isinstance(next_page, list):
                next_page = [next_page]
            for location in next_page:
                locations.append(location.name)
            try:
                next_page = next(paged_location)
            except (GeneratorExit, StopIteration):
                break
        return locations

    @staticmethod
    def is_valid_location(azure_api: AzureApiHelper, location: str) -> bool:
        """
        Check whether or not the provided location is a valid Azure location.

        :param azure_api: instance of AzureApiHelper
        :param location: Location provided via CLI arg
        :return: True if location is valid, False otherwise
        """
        return location in VMSizesList.list_locations(azure_api)

    @staticmethod
    def get_vm_specs(resource: ResourceSku) -> VMCapabilitiesMap:
        """
        Get the hardware specs of a virtual machine from a Resource SKU.
        """
        accelerated_networking_enabled = False
        premium_storage_enabled = False

        if resource.capabilities is None:
            raise CODException(f"Unable to retrieve capabilities for VM size '{resource.name}'")

        for capability in resource.capabilities:
            if capability.name == "vCPUs":
                number_of_cores = capability.value
            elif capability.name == "MemoryGB":
                memory_in_gb = capability.value
            elif capability.name == "MaxDataDiskCount":
                max_data_disk_count = capability.value
            elif capability.name == "AcceleratedNetworkingEnabled":
                accelerated_networking_enabled = (capability.value == "True")
            elif capability.name == "PremiumIO":
                premium_storage_enabled = (capability.value == "True")

        return {
            "Cpu cores": number_of_cores,
            "Ram (GB)": memory_in_gb,
            "Max disk count": max_data_disk_count,
            "Accelerated networking": accelerated_networking_enabled,
            "Premium storage": premium_storage_enabled,
        }

    @cached_property
    def azure_api(self) -> AzureApiHelper:
        return AzureApiHelper.from_config(config)

    def __init__(self) -> None:
        self.location_to_vmsize_mapping: LocationToVMSizeMap = {}
        self.vmsize_to_specs_mapping: VMSpecsMap = {}

    def get_location_vmsizes(self, location: str) -> tuple[list[str], VMSpecsMap]:
        """
        Create location<->vmsizes mapping as well as vmsizes<->specs one.
        This function modifies object state, but also returns the modified state, in order to make the side effect
        clear.

        :param location: Azure location/region
        :return: List of VMSizes available in the given Location
        """
        vmsizes: list[str] = []

        resource_skus = get_resource_skus(self.azure_api, location, "virtualMachines")

        for resource in resource_skus:
            if resource.name:
                vmsizes.append(resource.name)
                if resource.name not in self.vmsize_to_specs_mapping:
                    self.vmsize_to_specs_mapping[resource.name] = VMSizesList.get_vm_specs(resource)

        return sorted(vmsizes), self.vmsize_to_specs_mapping

    def generate_location_to_vmsize_mapping(self) -> tuple[LocationToVMSizeMap, VMSpecsMap]:
        """
        Generate a dictionary mapping vmsizes available in the given location.

        :param location:
        :return:
        """
        location = config["azure_location"]
        self.validate_location(location)

        if location:
            log.info("Listing available VMSizes in %s", location)
            self.location_to_vmsize_mapping[location], self.vmsize_to_specs_mapping = (
                self.get_location_vmsizes(location)
            )
        else:
            log.info("Listing available VMSizes for all locations")
            for location in self.list_locations(self.azure_api):
                (
                    self.location_to_vmsize_mapping[location],
                    self.vmsize_to_specs_mapping,
                ) = self.get_location_vmsizes(location)
        return self.location_to_vmsize_mapping, self.vmsize_to_specs_mapping

    def output_json_file(self) -> None:
        """Print all mappings in a json file."""
        json_mapping = json.dumps(
            {"size": self.vmsize_to_specs_mapping, "regions": self.location_to_vmsize_mapping},
            indent=4,
            sort_keys=True,
        )
        print(json_mapping)

    def output_prettytable(self, all_columns: list[tuple[str, str]]) -> None:
        """Print all mappings in a Table."""
        location_to_vmsize = []
        for key, value in self.location_to_vmsize_mapping.items():
            for val in value:
                location_to_vmsize.append([
                    key,
                    val,
                    self.vmsize_to_specs_mapping[val]["Ram (GB)"],
                    self.vmsize_to_specs_mapping[val]["Cpu cores"],
                    self.vmsize_to_specs_mapping[val]["Max disk count"],
                    self.vmsize_to_specs_mapping[val]["Accelerated networking"],
                    self.vmsize_to_specs_mapping[val]["Premium storage"]
                ])
        cols_id = [column[0] for column in all_columns]
        table = SortableData(
            all_headers=all_columns,
            requested_headers=cols_id,
            rows=location_to_vmsize
        )
        table.sort(*config["sort"])
        print(table.output(output_format=config["output_format"]))

    def validate_location(self, location: str) -> None:
        if location and not self.is_valid_location(self.azure_api, location):
            raise CODException(
                "Location [%s] is not a valid azure location "
                "or is not available for this subscription"
                "Available locations are : "
                "%s " % (location, ", ".join(self.list_locations(self.azure_api)))
            )

    def run(self) -> None:
        (self.location_to_vmsize_mapping, self.vmsize_to_specs_mapping) = self.generate_location_to_vmsize_mapping()

        if config["output_format"] == "json":
            self.output_json_file()
        elif config["output_format"] == "table":
            self.output_prettytable(columns)
