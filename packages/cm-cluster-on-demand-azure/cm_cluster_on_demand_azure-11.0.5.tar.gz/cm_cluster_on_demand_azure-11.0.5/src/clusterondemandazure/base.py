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
from functools import cached_property
from typing import TYPE_CHECKING

from azure.core.exceptions import ClientAuthenticationError, ResourceNotFoundError

from clusterondemand.exceptions import CODException
from clusterondemand.paramvalidation import ParamValidator
from clusterondemandazure.azure_actions.credentials import AzureApiHelper
from clusterondemandazure.paramvalidation import AZUREParamValidator
from clusterondemandazure.utils import get_resource_skus
from clusterondemandconfig import config

if TYPE_CHECKING:
    from azure.mgmt.compute.models import ResourceSku

log = logging.getLogger("cluster-on-demand")


class ClusterCommand:
    """Base class for all Azure cluster commands.

    This class only contains non-public validator methods that are intended to be used by
    descendant classes to validate user input. The general contract for all these methods is
    to perform various input sanitization checks, raising an Exception in the case of a failed
    check. If the check passes the _validate_xxx methods will simply return control to the
    caller with no return value.
    """

    def __init__(self) -> None:
        self.azure_api = AzureApiHelper.from_config(config)

    @cached_property
    def vm_skus(self) -> list[ResourceSku]:
        return get_resource_skus(self.azure_api, config["azure_location"], "virtualMachines")

    @cached_property
    def disk_skus(self) -> list[ResourceSku]:
        return get_resource_skus(self.azure_api, config["azure_location"], "disks")

    def _validate_cluster_name(self) -> None:
        validate_max_name_len = config["validate_max_cluster_name_length"]
        ParamValidator.validate_cluster_name(config["name"], validate_max_name_len)

    def _validate_cluster_password(self) -> None:
        if (isinstance(config["cluster_password"], str) and
                not AZUREParamValidator.validate_password(config["cluster_password"])):
            raise CODException(
                "Cluster Password '%s' does not match proper format, the password should "
                "be at least 8 characters long." % config["cluster_password"]
            )

    def _validate_access_credentials(self) -> None:
        ParamValidator.validate_uuid_format(
            config["azure_tenant_id"],
            "Azure Tenant ID does not match the proper format",
        )
        ParamValidator.validate_uuid_format(
            config["azure_client_id"],
            "Azure Client ID does not match the proper format",
        )
        ParamValidator.validate_uuid_format(
            config["azure_subscription_id"],
            "Azure Subscription ID does not match the proper format",
        )

        try:
            self.azure_api.get_credential()
            # We only validate the credentials once we call the API.
            # This means that we need to make an actual API call in which we use the results.
            self.azure_api.subscription_client.subscriptions.get(config["azure_subscription_id"])
        except ClientAuthenticationError:
            raise CODException(
                "Azure API Authentication failed: Provided credentials are invalid"
            )
        except ResourceNotFoundError:
            raise CODException(
                "Azure API Authentication failed: Provided subscription ID "
                f"{config['azure_subscription_id']} is invalid"
            )

    def _validate_location(self) -> None:
        if not AZUREParamValidator.validate_location(
                self.azure_api,
                config["azure_location"]
        ):
            raise CODException(
                "Region %s does not exist." % config["azure_location"]
            )

    def _validate_vmsizes_in_region(self, head_node_type: str, node_type: str) -> None:
        vm_sizes = [sku.name.lower() for sku in self.vm_skus if sku.name]  # type: ignore

        if head_node_type.lower() not in vm_sizes:
            raise CODException(
                "VMSize '%s' does not exist in location '%s'." %
                (head_node_type, config["azure_location"]))

        if node_type.lower() not in vm_sizes:
            raise CODException(
                "VMSize '%s' does not exist in location '%s'." %
                (node_type, config["azure_location"])
            )

    def _validate_vmsizes_in_az(self, head_node_type: str, node_type: str) -> None:
        vm_sizes: list[str] = []
        for sku in self.vm_skus:
            if sku.location_info and len(sku.location_info) != 1:
                sku_name = sku.name or "<unknown>"
                log.debug(f"Received unexpected location info for SKU {sku_name}, ignoring")

            if (
                sku.location_info
                and sku.location_info[0].zones
                and config["azure_availability_zone"] in sku.location_info[0].zones
                and sku.name
            ):
                vm_sizes.append(sku.name.lower())

        if head_node_type.lower() not in vm_sizes:
            raise CODException(
                "VMSize '%s' does not exist in availability zone '%s'." %
                (head_node_type, config["azure_availability_zone"]))

        if node_type.lower() not in vm_sizes:
            raise CODException(
                "VMSize '%s' does not exist in availability zone '%s'." %
                (head_node_type, config["azure_availability_zone"]))

    @staticmethod
    def _validate_vm_gen(head_node_vm_gen: str, node_vm_gen: str) -> None:

        def is_valid_hyperv_gen(g: str) -> bool:
            return g.upper() in ("V1", "V2")

        if not is_valid_hyperv_gen(head_node_vm_gen):
            raise CODException(
                "Invalid head node Hyper-V generation: %r. Supported values: 'V1', 'V2'." % head_node_vm_gen)
        if not is_valid_hyperv_gen(node_vm_gen):
            raise CODException(
                "Invalid node Hyper-V generation: %r. Supported values: 'V1', 'V2'." % node_vm_gen)

    def _validate_blob(self) -> None:
        if (config["head_node_image"] and config["head_node_image"].startswith("http") and
                not AZUREParamValidator.validate_custom_blob(config["head_node_image"])):
            raise CODException("VHD Blob specified does not exist or is unreachable.")

    @staticmethod
    def _validate_az_number() -> None:
        if az := config["azure_availability_zone"]:
            # There is no Azure region with more than 3 AZ-s
            if az not in ["1", "2", "3"]:
                raise CODException(f"'{az}' is not a valid Azure availability zone")

    def _validate_storage_type_in_location(self, storage_type: str) -> None:
        available_disk_skus = {str(sku.name) for sku in self.disk_skus if sku and sku.name}
        if storage_type not in available_disk_skus:
            raise CODException(
                f"Storage type '{storage_type}' is not available in region '{config['azure_location']}'. "
                f"Available types: {', '.join(available_disk_skus)}"
            )

    def _validate_vm_storage_compatibility(self, vm_size: str, storage_type: str) -> None:
        # Standard storage works with all VMs
        if storage_type.startswith('Standard'):
            return

        # head node root volume (OS disk in Azure terms) cannot be Ultra SSD
        # https://learn.microsoft.com/en-us/azure/virtual-machines/disks-enable-ultra-ssd?tabs=azure-portal
        if storage_type.startswith('Ultra'):
            raise CODException(
                "Ultra Disks can't be used as an OS disk. Please use Standard or Premium storage type"
            )

        vm_sku = next((sku for sku in self.vm_skus if sku.name == vm_size), None)
        if not vm_sku or not vm_sku.capabilities:
            log.warning(f"Could not verify storage compatibility for VM size '{vm_size}'")
            return

        if storage_type.startswith('Premium'):
            if not next(
                (cap for cap in vm_sku.capabilities
                 if cap.name == "PremiumIO" and cap.value.lower() == "true"), None
            ):
                raise CODException(
                    f"VM size '{vm_size}' does not support Premium Storage ({storage_type}). "
                    f"Please choose a Premium Storage-capable VM size, or use Standard storage. "
                    "VM sizes that support Premium storage can be found with `cm-cod-azure vmsizes list`."
                )
        else:
            log.warning("Unhandled storage type, cluster creation may fail")
