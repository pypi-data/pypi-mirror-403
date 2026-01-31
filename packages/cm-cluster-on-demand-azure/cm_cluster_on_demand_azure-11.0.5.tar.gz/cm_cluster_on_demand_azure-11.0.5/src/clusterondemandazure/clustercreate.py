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

import base64
import json
import logging
import os
import random
import shlex
import string
from datetime import datetime
from typing import TYPE_CHECKING, Any

import yaml

if TYPE_CHECKING:
    from azure.mgmt.resource import ResourceManagementClient
    from clusterondemandconfig.configuration import ConfigurationView
    from clusterondemand.images.find import CODImage
    from clusterondemandconfig.parameter.parameter import Parameter

from azure.core.exceptions import HttpResponseError
from azure.mgmt.compute.models import (
    HyperVGenerationTypes,
    Image,
    ImageOSDisk,
    ImageStorageProfile,
    OperatingSystemStateTypes,
    OperatingSystemTypes
)
from azure.mgmt.resource.resources.models import Deployment, DeploymentMode, DeploymentProperties
from msrestazure.tools import parse_resource_id
from passlib.hash import sha512_crypt

import clusterondemand.clustercreate
from clusterondemand import utils
from clusterondemand.bcm_version import BcmVersion
from clusterondemand.cidr import cidr, must_be_within_cidr
from clusterondemand.cloudconfig.headcommands import get_ssh_auth_key_commands
from clusterondemand.clustercreate import (
    enable_cmd_debug_commands,
    generate_random_cluster_password,
    validate_inbound_rules
)
from clusterondemand.clusternameprefix import must_start_with_cod_prefix
from clusterondemand.exceptions import CODException
from clusterondemand.inbound_traffic_rule import InboundTrafficRule
from clusterondemand.node_definition import NodeDefinition
from clusterondemand.ssh import clusterssh_ns
from clusterondemand.ssh_key import validate_ssh_pub_key
from clusterondemand.summary import SummaryType
from clusterondemand.tags import tags_ns
from clusterondemand.wait_helpers import clusterwaiters_ns, wait_for_cluster
from clusterondemandazure.azure_actions.credentials import AzureApiHelper
from clusterondemandazure.azure_actions.storage import StorageAction
from clusterondemandazure.base import ClusterCommand
from clusterondemandazure.brightsetup import generate_bright_setup
from clusterondemandazure.inbound_traffic_rule import generate_arm_nsg_security_rule
from clusterondemandazure.summary import AzureSummaryGenerator
from clusterondemandazure.utils import validate_vmsizes_arch
from clusterondemandconfig import ConfigNamespace, config
from clusterondemandconfig.configuration_validation import may_not_equal_none, requires_other_parameters_to_be_set

from .configuration import azurecommon_ns
from .constants import disk_setup
from .images import AzureImageSource, findimages_ns
from .template_builder import TemplateBuilder
from .vmsizelist import VMSizesList

config_ns = ConfigNamespace("azure.cluster.create", "cluster creation parameters")
config_ns.import_namespace(clusterondemand.configuration.clustercreate_ns)
config_ns.override_imported_parameter(name="healthchecks_to_disable", default=["defaultgateway"])
config_ns.import_namespace(clusterondemand.configuration.clustercreatename_ns)
config_ns.import_namespace(clusterondemand.configuration.timezone_ns)
config_ns.import_namespace(findimages_ns)
config_ns.override_imported_parameter("version", default="11.0")
config_ns.import_namespace(clusterondemand.configuration.cmd_debug_ns)
config_ns.import_namespace(clusterssh_ns)
config_ns.import_namespace(clusterwaiters_ns)
config_ns.import_namespace(azurecommon_ns)
config_ns.import_namespace(tags_ns)
config_ns.remove_imported_parameter("name")
config_ns.add_parameter(
    "name",
    help="Name of the cluster to create",
    validation=[may_not_equal_none, must_start_with_cod_prefix])
config_ns.override_imported_parameter("head_node_root_volume_size", default=42)
config_ns.add_parameter(
    "azure_availability_zone",
    env="AZURE_AVAILABILITY_ZONE",
    help=("Name of the Azure availability zone in which all of the VMs"
          " will be created. When not specified, a random availability zone will be used."
          " Useful when your chosen VM type is not available in all availability zones.")
)
config_ns.add_parameter(
    "head_node_root_volume_type",
    advanced=True,
    default="StandardSSD_LRS",
    help="Storage type to use for Azure root volume")
config_ns.override_imported_parameter(
    "node_type",
    default="Standard_D1_v2",
    help="The instance type of compute nodes. It must exist in the region you use. "
    "Can be suffixed with ':V1' or ':V2', meaning the Hyper-V generation. The default is V1.",
)
config_ns.override_imported_parameter(
    "head_node_type",
    default="Standard_D1_v2",
    help="The instance type must exist in the region you use. "
    "Can be suffixed with ':V1' or ':V2', meaning the Hyper-V generation. The default is V1.",
)
config_ns.override_imported_parameter(
    "ssh_pub_key_path", validation=lambda p, c: validate_ssh_pub_key(p, c, allowed_types={"RSA": 2048, "ED25519": 256})
)
config_ns.add_parameter(
    "head_node_image",
    help=("Single image selector statement for the head node image. Can either be an image "
          "URL, the name of that image or the name of the image set."),
)
config_ns.add_parameter(
    "network_cidr",
    default=cidr("10.142.0.0/16"),
    help="CIDR range of the VNet. The VNet Subnets must fall within this range. "
    "The widest allowed range is /16.",
    parser=cidr)
config_ns.add_parameter(
    "subnet_cidr",
    default=cidr("10.142.128.0/17"),
    help="CIDR range of the subnet. It must fall within the range specified by --network-cidr. ",
    parser=cidr,
    validation=must_be_within_cidr("network_cidr"))
config_ns.add_parameter(
    "head_node_ip",
    advanced=True,
    help="The private IP address of the head node",
    help_varname="IP")
config_ns.add_switch_parameter(
    "skip_permission_verifications",
    help="Whether or not to skip verifying the credentials' access.")
config_ns.add_switch_parameter(
    "keep_image",
    help="Do not delete image resource after the head node is deployed.")
config_ns.add_switch_parameter(
    "partial",
    help="Perform a partial cluster creation which relies on the resource group, storage account, "
         "and head node image to be already available")
config_ns.add_parameter(
    "storage_account",
    advanced=True,
    help="Storage account to use. By default it's generated or the existing one is used (if it's the only one)")

config_ns.add_parameter(
    "vnet_resource_group",
    advanced=True,
    help="Resource Group where the existing VNet is located",
    validation=requires_other_parameters_to_be_set(["vnet_network_name", "vnet_subnet_name"]),
)
config_ns.add_parameter(
    "vnet_network_name",
    advanced=True,
    help="Name of the Virtual Network to be used.",
    validation=requires_other_parameters_to_be_set(["vnet_resource_group", "vnet_subnet_name"]),
)
config_ns.add_parameter(
    "vnet_subnet_name",
    advanced=True,
    help="Name of the subnet to use.",
    validation=requires_other_parameters_to_be_set(["vnet_resource_group", "vnet_network_name"]),
)

config_ns.add_switch_parameter(
    "accept_azure_terms",
    advanced=True,
    help="Accept the most recent Azure marketplace terms and skip the dialog"
)
config_ns.add_parameter(
    "head_node_role_definition_id",
    advanced=True,
    help="Azure ID of a (custom) Role definition. The Role will be assigned to a System Assigned Managed Identity for "
         "the head node instance. The role assignment will have a scope of the cluster Resource Group. The CMDaemon on "
         "the head node will not store any static Azure credentials.")
config_ns.add_switch_parameter(
    "encrypt_storage_infrastructure",
    advanced=True,
    default=True,
    help="Require infrastructure encryption when creating a storage account. "
         "This configuration cannot be changed after the storage account creation."
)
config_ns.add_switch_parameter(
    "configure_nat_gateway",
    default=False,
    advanced=True,
    help="Configure a NAT Gateway for the cluster. "
)


AZURE_MAX_RESOURCE_NAME_LENGTH = 64
AZURE_RANDOM_NAME_PART_LENGTH = 10


def shorten_name(
    name: str, total_len: int, random_part_len: int = AZURE_RANDOM_NAME_PART_LENGTH
) -> str:
    if len(name) > total_len:
        name = name[:(total_len - random_part_len)]
        random_resource_name = "".join(
            random.choice(string.ascii_uppercase + string.digits) for _ in
            range(random_part_len)
        )
        name = f"{name}{random_resource_name}"
    return name


def internal_subnet_id_validation(
    subnet_id_param: Parameter, config: ConfigurationView
) -> None:
    assert subnet_id_param.key == "internal_subnet_id"

    value = config[subnet_id_param.key]
    if value:
        try:
            parsed = parse_resource_id(value)
            config["vnet_resource_group"] = parsed["resource_group"]  # type: ignore[index]
            config["vnet_network_name"] = parsed["name"]  # type: ignore[index]
            config["vnet_subnet_name"] = parsed["child_name_1"]  # type: ignore[index]
        except Exception as e:
            raise CODException(f"'{value}' is not a valid Azure subnet ID") from e


config_ns.add_parameter(
    "internal_subnet_id",
    advanced=True,
    help="Azure ID for the existing subnet to be used. If set, a new VNet *will not* be created for this cluster. "
         "Instead, the head node will be attached to this existing subnet. This parameter combines "
         "--vnet-resource-group, --vnet-network-name and --vnet-subnet-name. See also --head-node-ip",
    validation=internal_subnet_id_validation,
)

config_ns.add_parameter(
    "resource_group",
    advanced=True,
    default=lambda _, config: ClusterCreate.default_resource_group_name(config["name"]),
    validation=must_start_with_cod_prefix,
    help="Resource group to use. All resources will be created in this resource group.",
)
config_ns.add_switch_parameter(
    "existing_rg",
    advanced=True,
    default=False,
    help="If set, COD will not try to create a resource group but instead just find the existing one. "
         "Use --resource-group to set a name.",
)

config_ns.add_switch_parameter(
    "create_public_ip",
    advanced=True,
    default=True,
    help="Create a public IP for the head node. Use --no-create-public-ip to skip creating one. In that case, to "
    "have access to the cluster, it will need to be created within an existing network that is accessible "
    "by the user. See --vnet-resource-group, --vnet-network-name and --vnet-subnet-name",
)

config_ns.add_parameter(
    "existing_public_ip",
    advanced=True,
    help="Name of an existing public IP resource to use for the head node. Only the resource name should be specified "
    "not the full resource ID. The resource should be created in the cluster resource group. Implies "
    "--no-create-public-ip.",
)

config_ns.add_switch_parameter(
    "create_network_security_group",
    advanced=True,
    default=True,
    help="Create a network security group and add rules as specified by --inbound-rule. Use "
    "--no-create-network-security-group to skip creating one. In that case a network security group should be created "
    "separately. This should usually be combined with specifying existing virtual network and subnet resources.",
)


def run_command() -> None:
    ClusterCreate().run()


log = logging.getLogger("cluster-on-demand")


HR = "---------------------------------------------------------------------"


class ClusterCreate(ClusterCommand):
    cluster_name: str
    head_node_name: str
    nat_gateway_name: str
    nat_gateway_public_ip_name: str
    accelerated_networking_enabled_for_head_node: bool
    _storage_account: StorageAccount | None
    resource_group: str
    deployment_name: str
    location: str
    head_node_image: CODImage
    use_existing_vnet: bool
    existing_subnet_id: str | None  # Can be None if not using existing subnet

    @property
    def storage_account(self) -> StorageAccount:
        if not self._storage_account:
            raise CODException(
                "Storage account not initialized. "
                "Storage account should be set before accessing methods that rely on it."
            )
        return self._storage_account

    @storage_account.setter
    def storage_account(self, value: StorageAccount | None) -> None:
        self._storage_account = value

    @staticmethod
    def _get_instance_type(instance_type_and_vm_gen: str) -> str:
        """ Extracts the instance type from a string like '<type>[:V<gen>]'. """
        return instance_type_and_vm_gen.split(":")[0]

    @staticmethod
    def _get_vm_gen(instance_type_and_vm_gen: str) -> str:
        """ Extracts the Hyper-V generation from a string like '<type>[:V<gen>]',
            where <gen> is either 1 or 2. If the generation is missing, it defaults to 1. """
        tokens = instance_type_and_vm_gen.split(":")
        return tokens[1].upper() if len(tokens) > 1 else "V1"

    @property
    def head_node_type(self) -> str:
        return self._get_instance_type(config["head_node_type"])

    @property
    def head_node_vm_gen(self) -> str:
        return self._get_vm_gen(config["head_node_type"])

    @property
    def node_type(self) -> str:
        return self._get_instance_type(config["node_type"])

    @property
    def node_vm_gen(self) -> str:
        return self._get_vm_gen(config["node_type"])

    @property
    def vnet_name(self) -> str:
        return f"{self.cluster_name}-vnet"

    @property
    def vnet_subnet_name(self) -> str:
        return f"{self.cluster_name}-vnet-subnet"

    def _create_storage_account(self) -> None:
        """
        Create a storage account and containers.

        The containers are used for saving image data and need to
        exist prior to server side copy and template deployment.
        """

        storage_action = StorageAction(self.azure_api, self.cluster_name)
        storage_action.create_storage_account(
            self.resource_group, self.storage_account.name, self.location, config["encrypt_storage_infrastructure"]
        )
        for container in ["images", "vhds"]:
            storage_action.create_container(container, self.storage_account.name, self.resource_group)

    def _change_public_access_for_storage_account(self, **kwargs: Any) -> None:
        """
        Remove public access.
        """

        storage_action = StorageAction(self.azure_api, self.cluster_name)
        storage_action.change_public_access_for_storage_account(
            self.resource_group, self.storage_account.name, self.location, config["encrypt_storage_infrastructure"],
            **kwargs
        )

    @staticmethod
    def default_resource_group_name(cluster_name: str) -> str:
        return "%s_cod_resource_group" % cluster_name

    @staticmethod
    def _shell_escape(text: str) -> str:
        return text.replace("'", "'\\''")

    def cloud_init_script(self) -> str:
        """
        Generate the cloud-init script to be ran on the head node.

        :return: String containing the cloud-init bash script
        """
        log.info("generating cloud-init script")

        bright_conf = self._shell_escape(
            yaml.dump(
                generate_bright_setup(
                    cluster_name=self.cluster_name,
                    head_node_image=self.head_node_image,
                    location=self.location,
                    resource_group=self.resource_group,
                    storage_account_name=self.storage_account.name,
                    node_type=self.node_type,
                    node_vm_gen=self.node_vm_gen,
                    use_existing_vnet=self.use_existing_vnet,
                    vnet_name=self.vnet_name,
                    vnet_subnet_name=self.vnet_subnet_name,
                    head_node_ip=config["head_node_ip"],
                )
            )
        )

        cloud_init_script = """#!/bin/bash

        mkdir -p /root/cm

        echo '%s' > /root/cm/cm-bright-setup.conf
        echo '%s' > /root/cm/disk-setup.xml

        hostnamectl set-hostname %s
        """ % (bright_conf, disk_setup, shlex.quote(self.cluster_name))

        auth_key_commands = get_ssh_auth_key_commands()
        if auth_key_commands:
            log.info("Public key specified")
            cloud_init_script += "mkdir -p /root/.ssh/\n"
            cloud_init_script += "\n".join(auth_key_commands)
            cloud_init_script += "\n"

        encrypted_root_password = sha512_crypt.hash(config["cluster_password"])
        cloud_init_script += """
            echo %s | chpasswd -e
            """ % shlex.quote("root:" + encrypted_root_password)

        if config["ssh_password_authentication"]:
            cloud_init_script += """
            sed -i 's/PasswordAuthentication no/PasswordAuthentication yes/g' /etc/ssh/sshd_config
            if ! systemctl try-reload-or-restart sshd; then
              echo 'Old systemd, using different reload command.'
              systemctl reload-or-try-restart sshd
            fi
            """

        if config["cmd_debug"]:
            subsystems = config["cmd_debug_subsystems"]
            log.debug(f"Setting debug mode on CMDaemon for subsystems: '{subsystems}'")
            for command in enable_cmd_debug_commands(subsystems):
                cloud_init_script += command + "\n"

        if config["run_cm_bright_setup"]:
            if config["prebs"]:
                cloud_init_script += "\n".join(["echo 'Starting custom prebs commands'", *config["prebs"], ""])

            if BcmVersion(config["version"]).release < (8, 2):
                cloud_init_script += "/cm/local/apps/cluster-tools/bin/cm-bright-setup " \
                                     "-c /root/cm/cm-bright-setup.conf --on-error-action abort\n"
            else:
                cloud_init_script += "/cm/local/apps/cm-setup/bin/cm-bright-setup " \
                                     "-c /root/cm/cm-bright-setup.conf --on-error-action abort\n"

            if config["postbs"]:
                cloud_init_script += "\n".join(["echo 'Starting custom postbs commands'", *config["postbs"], ""])

        return cloud_init_script

    def generate_inbound_traffic_rules(
        self, config_inbound_rules: list[InboundTrafficRule], start_priority: int
    ) -> list[dict[str, Any]]:
        return [
            generate_arm_nsg_security_rule(
                priority=start_priority + i,
                protocol=rule.protocol,
                src_port=rule.src_port,
                dst_port=rule.dst_port,
                src_cidr=rule.src_cidr,
            )
            for i, rule in enumerate(
                InboundTrafficRule.process_inbound_rules(config_inbound_rules)
            )
        ]

    def generate_icmp_rules(
        self, config_icmp_rules: list[str], start_priority: int
    ) -> list[dict[str, Any]]:
        return [
            generate_arm_nsg_security_rule(
                priority=start_priority + i,
                protocol="icmp",
                src_port="*",
                dst_port="*",
                src_cidr=str(rule),
            )
            for i, rule in enumerate(config_icmp_rules)
        ]

    def _validate_params(self) -> None:
        if config["create_network_security_group"]:
            validate_inbound_rules(inbound_rules=config["inbound_rule"])
        self._validate_storage_type_in_location(storage_type=config["head_node_root_volume_type"])
        self._validate_vm_storage_compatibility(self.head_node_type, config["head_node_root_volume_type"])
        self._validate_cluster_name()
        self._validate_cluster_password()
        self._validate_az_number()
        self._validate_access_credentials()
        self._validate_location()
        self._validate_vmsizes_in_region(self.head_node_type, self.node_type)
        if config["azure_availability_zone"]:
            self._validate_vmsizes_in_az(self.head_node_type, self.node_type)
        self._validate_vm_gen(self.head_node_vm_gen, self.node_vm_gen)
        self._validate_blob()

    def on_error(self, r_client: ResourceManagementClient) -> None:
        if config["on_error"] == "cleanup":
            async_removal = r_client.resource_groups.begin_delete(self.resource_group)
            log.info("Resource group removal initiated.")
            async_removal.wait()
        else:
            log.info("Failed environment was kept and will have to be deleted manually.")

    def verify_api_credentials(self) -> None:
        """
         Creates a temporary resource group and virtual network in order to make sure the provided API
         credentials have all required permissions.
        """
        random_resource_name = "".join(
            random.choice(string.ascii_uppercase + string.digits) for _ in
            range(20)
        )
        log.info("Temporary azure resources will be created (resource group: %s) in order"
                 " to verify that the API credentials have the required permissions, this"
                 " can take a few minutes. You can skip this step by specifying the following"
                 " flag: '--skip-permission-verifications'", random_resource_name)
        try:
            self.azure_api.resource_client.resource_groups.create_or_update(
                random_resource_name,
                {"location": config["azure_location"]}
            )

            try:
                self.azure_api.network_client.virtual_networks.begin_create_or_update(  # type: ignore[call-overload]
                    random_resource_name,
                    random_resource_name,
                    {"location": config["azure_location"],
                     "properties": {
                         "addressSpace": {"addressPrefixes": ["10.10.10.0/24"]}}
                     }
                )
                # The IP address here is arbitrary and was just added to satisfy Azure API
                # requirements.
            except HttpResponseError as e:
                AzureApiHelper.log_error_details(e)
                raise CODException(
                    "Insufficient write access: Not enough permissions to create a virtual network."
                )

            log.info(
                "Credentials are valid and have read/write authorizations.")
            async_removal = self.azure_api.resource_client.resource_groups.begin_delete(
                random_resource_name)
            log.debug("Cleanup removal initiated.")
            async_removal.wait()

        except HttpResponseError as e:
            AzureApiHelper.log_error_details(e)
            raise CODException(
                "Insufficient write access: unable to create a resource group."
            )

    def create_resource_group(self) -> None:
        utils.cod_log(log, "Creating resource group %s" % self.resource_group, 2)
        try:
            if not self.azure_api.resource_client.resource_groups.check_existence(self.resource_group):
                tags = dict(config.get("cluster_tags", {}))
                tags.update(
                    {
                        "BCM Resource": True,
                        "BCM Created at": datetime.utcnow().isoformat()
                        + "Z",  # fix missing timezone
                        "BCM Created by": utils.get_user_at_fqdn_hostname(),
                        "BCM Cluster": self.cluster_name,
                        "BCM Bursting": "on-demand",
                        "BCM Image name": self.head_node_image.name,
                    }
                )
                self.azure_api.resource_client.resource_groups.create_or_update(
                    self.resource_group,
                    {
                        "location": self.location,
                        "tags": tags
                    }
                )
            else:
                raise CODException(
                    "The resource group '%s' already exists." % self.resource_group
                )
        except CODException as e:
            raise e
        except HttpResponseError as e:
            AzureApiHelper.log_error_details(e)
            self.on_error(self.azure_api.resource_client)
            raise CODException("Template deployment failed: %s" % str(e), caused_by=e)
        except Exception as e:
            self.on_error(self.azure_api.resource_client)
            raise CODException("Template deployment failed: %s" % str(e), caused_by=e)

    def _head_node_image_name(self) -> str:
        return f"{self.cluster_name}-os-disk-image"

    def _head_node_image_blob_name(self) -> str:
        return f"{self.cluster_name}-os-disk-image.vhd"

    def server_side_copy_head_node_image_blob(self) -> str:
        """
        Copy disk image from public bright storage account to the cluster's storage account.

        :return: The blob URL
        """

        container = "images"
        blob_name = self._head_node_image_blob_name()
        vhd_url = self.head_node_image.uuid
        utils.cod_log(log, "Copying head node image from " + vhd_url, 7)
        storage_action = StorageAction(self.azure_api, self.cluster_name)
        storage_action.copy_blob(
            vhd_url,
            self.resource_group,
            self.storage_account.name,
            container,
            blob_name,
        )
        return f"https://{self.storage_account.name}.blob.core.windows.net/images/{blob_name}"

    def delete_head_node_image_blob(self) -> None:

        storage_action = StorageAction(self.azure_api, self.cluster_name)
        storage_action.delete_blob(self.resource_group,
                                   self.storage_account.name,
                                   "images",
                                   self._head_node_image_blob_name())

    def create_head_node_image_from_blob(self, blob_url: str) -> None:
        """
        Creates an image from a azure disk (VHD) given its url
        """
        img_name = self._head_node_image_name()
        img_params = Image(
            location=self.location,
            tags={"BCM Resource": "True", "BCM Cluster": self.cluster_name},
            storage_profile=ImageStorageProfile(
                os_disk=ImageOSDisk(
                    os_type=OperatingSystemTypes.LINUX,
                    os_state=OperatingSystemStateTypes.GENERALIZED,
                    blob_uri=blob_url,
                    caching="ReadOnly",
                )
            ),
            hyper_v_generation=(HyperVGenerationTypes.V2
                                if self.head_node_vm_gen == "V2"
                                else HyperVGenerationTypes.V1)
        )

        creation_successful = False
        current_attempt = 0
        MAX_ATTEMPTS = 3
        log.info("Creating image resource '%s' (Hyper-V gen %s) from blob %s",
                 img_name, self.head_node_vm_gen, blob_url)
        while current_attempt < MAX_ATTEMPTS and not creation_successful:
            try:
                create_img_future = self.azure_api.compute_client.images.begin_create_or_update(
                    resource_group_name=self.resource_group,
                    image_name=img_name,
                    parameters=img_params)
                future = create_img_future
                future.wait()
                creation_successful = True
            except HttpResponseError as e:
                if blob_url in e.message:
                    log.debug("Failed to create the headnode image, retrying...")
                    current_attempt += 1
                    continue
                AzureApiHelper.log_error_details(e)
                raise CODException("Failed to create the headnode image", caused_by=e)

    def check_resource_group_usability(self) -> None:
        """
        Verifies the presence of a reusable resource group
        """
        if self.azure_api.resource_client.resource_groups.check_existence(self.resource_group):
            # Checking whether a storage account already exists or not
            rg_storage_accs = [a.name for a in (self.azure_api.storage_client.storage_accounts.
                               list_by_resource_group(self.resource_group))]
            if self._storage_account is None:
                if not rg_storage_accs:
                    raise CODException(
                        f"Resource group '{self.resource_group}' doesn't have any storage accounts."
                        f" If you want to create a cluster in the existing resource group use"
                        f" '--existing-rg --resource-group {self.resource_group}' parameters"
                    )
                if len(rg_storage_accs) > 1:
                    raise CODException(
                        f"Resource group '{self.resource_group}' has multiple storage accounts:"
                        f"{', '.join(rg_storage_accs)}. Please, specify which one you want to use"
                        f" using --storage-account parameter"
                    )
                self.storage_account = StorageAccount(rg_storage_accs[0])
                log.debug(f"Found the only storage account '{self.storage_account.name}'"
                          f" associated with resource group '{self.resource_group}'")

            if self.storage_account.name not in rg_storage_accs:
                raise CODException(f"Resource group '{self.resource_group}' doesn't have specified"
                                   f" storage account '{self.storage_account.name}")

            head_node_image_name = self._head_node_image_name()
            try:
                self.azure_api.compute_client.images.get(self.resource_group, head_node_image_name)
            except HttpResponseError as e:
                AzureApiHelper.log_error_details(e)
                raise CODException(f"Resource group '{self.resource_group}' doesn't have"
                                   f" the head node image '{head_node_image_name}'", caused_by=e)
        else:
            raise CODException(f"The resource group for the Cluster '{config['name']}' does not exist")

    def deploy_private_endpoint_for_storage_account(self) -> None:

        log.info(f"Deploying private endpoint for storage account {self.storage_account.name}")

        with open(os.path.join(os.path.dirname(__file__), "resources/plink_template.json"), "r") as template_file:
            template_body = json.load(template_file)

        vnet_resource_group = config['vnet_resource_group'] or self.resource_group
        vnet_network_name = config['vnet_network_name'] or self.vnet_name
        vnet_subnet_name = config['vnet_subnet_name'] or self.vnet_subnet_name

        resource_base_path = (
            f"/subscriptions/{config['azure_subscription_id']}/resourceGroups/{self.resource_group}/providers"
        )
        network_resource_base_path = (
            f"/subscriptions/{config['azure_subscription_id']}/resourceGroups"
            f"/{vnet_resource_group}/providers"
        )

        plink_deployment_parameters = {}
        plink_deployment_parameters = {
            "cluster_name": {"value": self.cluster_name},
            "location": {"value": self.location},
            "azure_subscription_id": {"value": f"{config['azure_subscription_id']}"},
            "private_endpoint_name": {"value": f"{self.cluster_name}-pe"},
            "virtual_network_link_name": {"value": f"{self.cluster_name}-vnet-link"},
            "private_link_service_connection_name": {"value": f"{self.cluster_name}-plink-service-connection"},
            "private_link_resource":
            {
                "value":
                f"{resource_base_path}/Microsoft.Storage/storageAccounts/{self.storage_account.name}"
            },
            "target_sub_resource": {"value": ["blob"]},
            "request_message": {"value": ""},
            "subnet":
            {
                "value":
                f"{network_resource_base_path}/Microsoft.Network/virtualNetworks"
                f"/{vnet_network_name}/subnets/{vnet_subnet_name}"
            },
            "virtual_network_id":
            {
                "value":
                f"{network_resource_base_path}/Microsoft.Network/virtualNetworks/{vnet_network_name}"
            },
            "virtual_network_deployment_name": {"value": f"{self.cluster_name}-vnet-deployment"},
            "custom_network_interface_name": {"value": f"{self.cluster_name}-pe-nic"},
            "resource_group": {"value": f"{self.resource_group}"},
            "virtual_network_resource_group": {"value": f"{vnet_resource_group}"},
            "private_dns_deployment_name": {"value": f"{self.cluster_name}-privdns"},
            "private_dns_zone_name": {"value": f"{self.cluster_name}-privdns-zone"},
            "dns_zone_group_name": {"value": f"{self.cluster_name}-dns-zone-group"},
            "private_dns_zone_config_name": {"value": f"{self.cluster_name}-privdns-zone_config"},
        }

        plink_deployment_properties = DeploymentProperties(
            mode=DeploymentMode.INCREMENTAL,
            template=template_body,
            parameters=plink_deployment_parameters  # type: ignore[arg-type]
        )

        try:
            deployment_name = f"{self.deployment_name}-plink"
            deployment_name = shorten_name(deployment_name, AZURE_MAX_RESOURCE_NAME_LENGTH)

            deployment_async_operation = self.azure_api.resource_client.deployments.begin_create_or_update(
                resource_group_name=self.resource_group,
                deployment_name=deployment_name,
                parameters=Deployment(properties=plink_deployment_properties))
            deployment_async_operation.wait()

        except HttpResponseError as e:
            AzureApiHelper.log_error_details(e, azure_api=self.azure_api, resource_group=self.resource_group,
                                             deployment_name=deployment_name)
            self.on_error(self.azure_api.resource_client)
            raise CODException("Private link deployment failed: %s" % e.message, caused_by=e)
        except Exception as e:
            self.on_error(self.azure_api.resource_client)
            raise CODException("Private link deployment failed: %s" % str(e), caused_by=e)

    def run(self) -> None:
        self._storage_client = None
        self._compute_client = None
        self._resource_client = None
        self._network_client = None

        self.cluster_name = config["name"]
        self.head_node_name = f"{self.cluster_name}-a"
        self.nat_gateway_name = f"{self.cluster_name}-nat-gateway"
        self.nat_gateway_public_ip_name = f"{self.cluster_name}-nat-gateway-public-ip"
        self._validate_params()

        vmszlist = VMSizesList()

        _, vm_size_to_specs_map = vmszlist.generate_location_to_vmsize_mapping()

        config['arch'] = validate_vmsizes_arch(config['arch'], self.vm_skus, self.head_node_type, "head node")
        validate_vmsizes_arch(config['arch'], self.vm_skus, self.node_type, "compute node")

        self.accelerated_networking_enabled_for_head_node = vm_size_to_specs_map[
            self.head_node_type]["Accelerated networking"]
        log.info(f"Head node type is {self.head_node_type}. Head node supports accelerated networking: "
                 f"{self.accelerated_networking_enabled_for_head_node!r}")

        self.storage_account = None
        if config["storage_account"]:
            self.storage_account = StorageAccount(config["storage_account"])
        elif not config["partial"]:
            self.storage_account = StorageAccount.storage_account_for_cluster(config["name"])

        self.resource_group = config["resource_group"]
        self.deployment_name = "%s-az-depl" % config["name"]

        self.location = config["azure_location"]

        # Let ICMP rules start at prio 100 and other inbound rules start at 150 to keep them apart
        icmp_rules = self.generate_icmp_rules(config["ingress_icmp"] or [], start_priority=100)
        inbound_rules = self.generate_inbound_traffic_rules(config["inbound_rule"] or [], start_priority=150)

        # Combine the ICMP and inbound rules and format them for the ARM template
        all_inbound_rules = ",\n".join(json.dumps(rule, indent=4) for rule in icmp_rules + inbound_rules)

        self.head_node_image = AzureImageSource.pick_head_node_image_using_options(config)
        if not self.head_node_image.version and config["run_cm_bright_setup"]:
            log.warning(
                f"Using custom image: {self.head_node_image.uuid} with parameter run_cm_bright_setup set to 'yes'."
                f" Probably it was set by mistake because a custom image might not have necessary files"
                f" to run cm-bright-setup. Consider using --run-cm-bright-setup=no to "
            )

        if BcmVersion(config["version"]).release >= (9, 0):
            default_vnet_name = self.vnet_name
        else:
            default_vnet_name = f"vpc-{self.location}"

        self.use_existing_vnet = False
        if config["vnet_resource_group"]:
            if BcmVersion(config["version"]).release >= (9, 0):
                self.use_existing_vnet = True
            else:
                parameter_values = ", ".join(
                    f"{config.item_repr(key)}"
                    for key in ["vnet_resource_group", "vnet_network_name", "vnet_subnet_name"]
                )
                log.warning(
                    f"Bright versions below 9.0 don't support using an existing VNet. "
                    f"The parameters {parameter_values} will be ignored. "
                )

        generator = AzureSummaryGenerator(config,
                                          SummaryType.Proposal,
                                          head_node_definition=NodeDefinition(
                                              1, self.head_node_type + ":" + self.head_node_vm_gen),
                                          head_image=self.head_node_image,
                                          node_definition=NodeDefinition(
                                              config["nodes"], self.node_type + ":" + self.node_vm_gen),
                                          region=self.location)
        generator.print_summary(log.info)

        if self.use_existing_vnet:
            subnet = self.azure_api.network_client.subnets.get(
                config["vnet_resource_group"],
                config["vnet_network_name"],
                config["vnet_subnet_name"],
            )

            log.info(
                f"Cluster will use existing Virtual Network {config['vnet_network_name']}/{config['vnet_subnet_name']} "
                f"on resource group {config['vnet_resource_group']}"
            )

            self.existing_subnet_id = subnet.id
            if subnet.address_prefix is not None:
                config["subnet_cidr"] = cidr(subnet.address_prefix)
            elif subnet.address_prefixes:
                config["subnet_cidr"] = cidr(subnet.address_prefixes[0])
            else:
                raise CODException(f"Can't determine CIDR for subnet with ID {subnet.id}")

        if config["head_node_ip"] and config["head_node_ip"] not in config["subnet_cidr"]:
            # We can't put this validation on the parameters because we have to check if it's an existing VPC first
            raise CODException(
                f"Parameter {config.item_repr('head_node_ip')} is not in the specified subnet. "
                f"Available range: {config['subnet_cidr']}."
            )

        if not config["create_network_security_group"]:
            log.info("Will not create a network security group.")

        if config["existing_public_ip"]:
            log.info(f"Will use public IP {config['existing_public_ip']} instead of creating one.")
            config["create_public_ip"] = False

        if config["ask_to_confirm_cluster_creation"]:
            utils.confirm_cluster_creation(num_clusters=1)

        if not config["skip_permission_verifications"]:
            self.verify_api_credentials()

        if (
            config["existing_rg"] and
            not self.azure_api.resource_client.resource_groups.check_existence(self.resource_group)
        ):
            raise CODException(
                f"Resource group {self.resource_group} does not exist. "
                f"Unset --existing-rg if you wish that COD creates it."
            )

        if not config["partial"]:
            if not config["existing_rg"]:
                self.create_resource_group()
            self._create_storage_account()
            blob_url = self.server_side_copy_head_node_image_blob()
            self.create_head_node_image_from_blob(blob_url)
            self.delete_head_node_image_blob()
        else:
            self.check_resource_group_usability()
            self._change_public_access_for_storage_account(public_access_for_cod_ip=True)

        utils.cod_log(log, "Building deployment template", 45)

        tb = TemplateBuilder(
            cluster_name=self.cluster_name,
            head_node_name=self.head_node_name,
            head_node_flavour=self.head_node_type,
            storage_account=self.storage_account.name,
            region=self.location,
            availability_zone=config["azure_availability_zone"],
            custom_data=_b64encode(self.cloud_init_script()),
            user_random_password=generate_random_cluster_password(length=50),
            accelerated_networking_enabled_for_head_node=self.accelerated_networking_enabled_for_head_node,
            head_node_ip=config["head_node_ip"] or None,
            network_cidr=str(config["network_cidr"]),
            subnet_cidr=str(config["subnet_cidr"]),
            head_node_root_volume_size=config["head_node_root_volume_size"],
            head_node_root_volume_type=config["head_node_root_volume_type"],
            image_name=self.head_node_image.name,
            image_creation_date=str(self.head_node_image.created_at),
            inbound_rules=all_inbound_rules,
            vnet_name=default_vnet_name,
            nat_gateway_name=self.nat_gateway_name,
            nat_gateway_public_ip_name=self.nat_gateway_public_ip_name,
            configure_nat_gateway=str(config["configure_nat_gateway"]).lower(),
        )
        template = tb.build()

        deployment_parameters = {}
        if self.use_existing_vnet:
            deployment_parameters["subnet_id"] = {"value": self.existing_subnet_id}
            deployment_parameters["create_new_vnet"] = {"value": "false"}

        deployment_parameters["create_public_ip"] = {"value": str(config["create_public_ip"]).lower()}

        if not config["create_network_security_group"]:
            deployment_parameters["create_new_nsg"] = {"value": "false"}

        deployment_properties = DeploymentProperties(
            mode=DeploymentMode.INCREMENTAL,
            template=template,
            parameters=deployment_parameters  # type: ignore[arg-type]
        )

        utils.cod_log(log, "Creating and deploying Head node", 85)

        try:
            deployment_async_operation = self.azure_api.resource_client.deployments.begin_create_or_update(
                resource_group_name=self.resource_group,
                deployment_name=self.deployment_name,
                parameters=Deployment(properties=deployment_properties)
            )
            deployment_async_operation.wait()
        except HttpResponseError as e:
            if "StaticPublicIPCountLimitReached" in e.message:
                raise CODException(e.message)
            if "SkuNotAvailable" in e.message:
                raise CODException(
                    "The requested vmsize: '{vmsize}' is not available in the location: "
                    "'{location}' temporarily, please select a different region or vmsize.".format(
                        vmsize=self.head_node_type,
                        location=config["azure_location"]
                    )
                )
            AzureApiHelper.log_error_details(e, azure_api=self.azure_api, resource_group=self.resource_group,
                                             deployment_name=self.deployment_name)
            self.on_error(self.azure_api.resource_client)
            raise CODException("Template deployment failed: %s" % e.message, caused_by=e)
        except Exception as e:
            self.on_error(self.azure_api.resource_client)
            raise CODException("Template deployment failed: %s" % str(e), caused_by=e)

        self.deploy_private_endpoint_for_storage_account()

        if not config["keep_image"]:
            # Try to delete the head node image, if it is managed by COD.
            head_node_image = self.azure_api.compute_client.images.get(
                self.resource_group, self._head_node_image_name()
            )
            # In "partial" mode, the existing image resource may not be a "BCM Resource".
            if head_node_image.tags and head_node_image.tags.get("BCM Resource", False):
                log.debug(f"Deleting image resource {head_node_image.name}")
                self.azure_api.compute_client.images.begin_delete(
                    self.resource_group, head_node_image.name
                ).wait()

        instance_id = self.azure_api.compute_client.virtual_machines.get(
            self.resource_group, "%s" % self.head_node_name
        ).vm_id

        public_ip_resource_name = config["existing_public_ip"] or f"{self.head_node_name}-ip"
        if config["create_public_ip"] or config["existing_public_ip"]:
            public_ip = self.azure_api.network_client.public_ip_addresses.get(
                self.resource_group, public_ip_resource_name
            ).ip_address
            log.info("Head node IP: %s" % public_ip)

            if config["run_cm_bright_setup"] and public_ip:
                # Normally disabling run_cm_bright_setup automatically disables waiting for cluster,
                # but in case of custom vhd url this parameter is overridden after validation.
                wait_for_cluster(config, public_ip)
        else:
            public_ip = "N/A"
            log.info("Cluster was created without a public IP. COD cannot wait for cmdaemon to be ready.")
            log.info(f"Head node private IP: {config['head_node_ip']}")

        utils.cod_log(log, "Deployment finished successfully.", 100)

        generator = AzureSummaryGenerator(config,
                                          SummaryType.Overview,
                                          instance_id=instance_id,
                                          public_ip=public_ip)
        generator.print_summary(log.info)


def _b64encode(string: str) -> str:
    return base64.b64encode(string.encode("utf-8")).decode("utf-8")


class StorageAccount:
    """Represents an Azure Storage account."""

    N_RANDOM_CHARS = 6
    MAX_STORAGE_ACCOUNT_NAME_LEN = 24
    ALLOWED_NAME_CHARACTERS = string.ascii_lowercase + string.digits

    @classmethod
    def storage_account_for_cluster(cls, cluster_name: str) -> StorageAccount:
        """Factory method that generates an instance with the proper name."""
        return cls(cls._name_for_storage_account(cluster_name))

    def __init__(self, name: str) -> None:
        self.name = name

    @classmethod
    def _name_for_storage_account(cls, cluster_name: str) -> str:
        full_name = cluster_name + "storageaccount"
        clean_name_chars = [ch for ch in full_name.lower() if ch in cls.ALLOWED_NAME_CHARACTERS]
        random_chars = [random.choice(cls.ALLOWED_NAME_CHARACTERS) for _ in range(cls.N_RANDOM_CHARS)]
        return "".join(clean_name_chars[:cls.MAX_STORAGE_ACCOUNT_NAME_LEN - cls.N_RANDOM_CHARS] + random_chars)
