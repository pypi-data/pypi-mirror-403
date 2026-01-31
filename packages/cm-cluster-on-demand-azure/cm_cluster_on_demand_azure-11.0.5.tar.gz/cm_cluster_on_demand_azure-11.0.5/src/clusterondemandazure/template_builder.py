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
import os
import string
from typing import Any, cast

from clusterondemandconfig import config

log = logging.getLogger("cluster-on-demand")


class TemplateBuilder:

    def __init__(
        self,
        cluster_name: str,
        head_node_name: str,
        head_node_flavour: str,
        storage_account: str,
        region: str,
        availability_zone: str | None,
        user_random_password: str,
        custom_data: str,
        accelerated_networking_enabled_for_head_node: bool,
        head_node_ip: str | None,
        network_cidr: str,
        subnet_cidr: str,
        head_node_root_volume_size: int,
        head_node_root_volume_type: str,
        image_name: str,
        image_creation_date: str,
        inbound_rules: Any,
        vnet_name: str,
        nat_gateway_name: str,
        nat_gateway_public_ip_name: str,
        configure_nat_gateway: str,  # "true"/"false", but can't be bool. With True in azure template, gw won't deploy
    ) -> None:

        self.data = {
            "cluster_name": cluster_name,
            "head_node_name": head_node_name,
            "head_node_flavour": head_node_flavour,
            "storage_account_name": storage_account,
            "region": region,
            "user_random_password": user_random_password,
            "custom_data": custom_data,
            "network_cidr": network_cidr,
            "accelerated_networking_enabled_for_head_node": accelerated_networking_enabled_for_head_node,
            "subnet_cidr": subnet_cidr,
            "head_node_root_volume_size": str(head_node_root_volume_size),
            "head_node_root_volume_type": head_node_root_volume_type,
            "image_name": image_name,
            "image_creation_date": image_creation_date,
            "inbound_rules": inbound_rules,
            "vnet_name": vnet_name,
            "nat_gateway_name": nat_gateway_name,
            "nat_gateway_public_ip_name": nat_gateway_public_ip_name,
            "configure_nat_gateway": configure_nat_gateway,
        }

        # By default, Azure assigns head node's private IP dynamically. If IP was specified, we populate it here
        if head_node_ip:
            self.data["head_node_ip"] = head_node_ip

        if availability_zone:
            self.data["availability_zone"] = availability_zone

    @property
    def variables(self) -> dict[str, Any]:
        # Head node tags should include cluster tags by default.
        head_node_tags = dict(config.get("cluster_tags", {}))
        # Explicitly defined head node tags may override cluster tags
        head_node_tags.update(
            {str(k): str(v) for k, v in config.get("head_node_tags", [])}
        )
        # Default BCM tags always have precedence (they identify the cluster)
        head_node_tags.update(
            {
                "BCM Image name": self.data["image_name"],
                "BCM Image created at": self.data["image_creation_date"],
                "BCM Resource": True,
                "BCM Type": "Head node",
                "BCM Cluster": self.data["cluster_name"],
            }
        )
        ret = {
            "head_node_tags": head_node_tags,
            "headNodeAvailabilitySetName": "avset-head-nodes-"
            + self.data["cluster_name"],
        }

        if config["head_node_tags"]:
            ret["head_node_tags"].update(config["head_node_tags"])

        return ret

    def fill_template(self, template: str) -> str:
        return string.Template(template).safe_substitute(self.data)

    def get_resource(self, type: str) -> dict[str, Any]:
        template = open(os.path.join(os.path.dirname(__file__), "resources/%s.json") % type)
        return cast(dict[str, Any], json.load(template))

    def get_head_node_resource(self) -> dict[str, Any]:
        head_node_resource = self.get_resource("head-node")
        if config["head_node_role_definition_id"]:
            head_node_resource["identity"] = {"type": "SystemAssigned"}
        return head_node_resource

    def get_head_node_nic_resource(self) -> dict[str, Any]:
        nic_resource = self.get_resource("head-node-nic")
        if not config["create_public_ip"]:
            # TODO CM-28902 should handle this in a better way. It's a bit annoying to modify the templates (why have
            # them in separate files if we modify?)
            # Once it's unified in a single template.json, then I think one way of achieving would be to define two
            # sorts of "head-node-nic" and they are deployed conditionally depending on parameter "create_public_ip"
            del nic_resource["properties"]["ipConfigurations"][0]["properties"]["publicIPAddress"]
        if config["existing_public_ip"]:
            nic_resource["properties"]["ipConfigurations"][0]["properties"]["publicIPAddress"] = {
                "id": f"[resourceId('Microsoft.Network/publicIPAddresses', '{config['existing_public_ip']}')]"
            }
        # In case if a specific IP was requested, we need to set "privateIPAllocationMethod": "Static", otherwise a
        # random IP will be provisioned
        if config["head_node_ip"]:
            nic_resource["properties"]["ipConfigurations"][0]["properties"]["privateIPAllocationMethod"] = "Static"

        nic_resource["properties"]["enableAcceleratedNetworking"] = self.data[
            "accelerated_networking_enabled_for_head_node"]

        return nic_resource

    def get_pub_ip_resource(self) -> dict[str, Any]:
        return self.get_resource("pub-ip")

    def get_sec_group_resource(self) -> dict[str, Any]:
        return self.get_resource("sec-group")

    def get_vpc_resource(self) -> dict[str, Any]:
        return self.get_resource("vpc")

    def get_avset_resource(self) -> dict[str, Any]:
        return self.get_resource("cnode-rdma-avset")

    def get_head_node_avset_resource(self) -> dict[str, Any]:
        return self.get_resource("head_node_avset")

    def get_head_node_role_assignment(self) -> dict[str, Any]:
        role = self.get_resource("role")
        role["properties"]["roleDefinitionId"] = config["head_node_role_definition_id"]
        return role

    def get_nat_gateway_resource(self) -> dict[str, Any]:
        return self.get_resource("nat-gateway")

    def get_nat_gateway_public_ip_resource(self) -> dict[str, Any]:
        return self.get_resource("nat-gateway-public-ip")

    def build(self) -> dict[str, Any]:
        with open(os.path.join(os.path.dirname(__file__), "template.json")) as tmpl_file:
            template = cast(dict[str, Any], json.loads(self.fill_template(tmpl_file.read())))

        # TODO (CM-28902): Move everything to inside template.json then we don't need this
        head_node_resource = self.get_head_node_resource()
        pub_ip_resource = self.get_pub_ip_resource()
        if not self.data.get("availability_zone"):
            head_node_resource.pop("zones")
            pub_ip_resource.pop("zones")

        template["resources"].append(head_node_resource)
        template["resources"].append(pub_ip_resource)
        template["resources"].append(self.get_head_node_nic_resource())
        template["resources"].append(self.get_sec_group_resource())
        template["resources"].append(self.get_vpc_resource())
        template["resources"].append(self.get_avset_resource())
        template["resources"].append(self.get_head_node_avset_resource())
        template["resources"].append(self.get_nat_gateway_public_ip_resource())
        template["resources"].append(self.get_nat_gateway_resource())
        template["variables"] = self.variables
        if config["head_node_role_definition_id"]:
            template["resources"].append(self.get_head_node_role_assignment())
        return template
