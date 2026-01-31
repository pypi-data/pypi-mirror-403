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
from typing import Any

import clusterondemand.brightsetup
from clusterondemand.bcm_version import BcmVersion
from clusterondemand.configuration import CFG_NO_ADMIN_EMAIL, NO_WLM
from clusterondemand.images.find import CODImage
from clusterondemandconfig import config

log = logging.getLogger("cluster-on-demand")


def generate_bright_setup(
    cluster_name: str,
    head_node_image: CODImage,
    location: str,
    resource_group: str,
    storage_account_name: str,
    node_type: str,
    node_vm_gen: str,
    use_existing_vnet: bool,
    vnet_name: str,
    vnet_subnet_name: str,
    head_node_ip: str | None = None,
) -> dict[str, Any]:
    license_dict = clusterondemand.brightsetup.get_license_dict(cluster_name)
    admin_email = config["admin_email"] if config["admin_email"] != CFG_NO_ADMIN_EMAIL else None

    # Generic configuration
    brightsetup = clusterondemand.brightsetup.generate_bright_setup(
        cloud_type="azure",
        wlm=config["wlm"] if config["wlm"] != NO_WLM else "",
        hostname=cluster_name,
        head_node_image=head_node_image,
        node_count=config["nodes"],
        timezone=config["timezone"],
        admin_email=admin_email,
        license_dict=license_dict,
        node_disk_setup_path="/root/cm/disk-setup.xml"
    )

    # Storage account URL where cmdaemon should look up node-installer images when starting cnodes
    storage_acc = "brightimagesdev" if head_node_image.version.endswith(("-dev", "trunk")) else "brightimages"
    image_url = f"https://{storage_acc}.blob.core.windows.net/images/"

    # Azure-specific configuration
    brightsetup["modules"]["brightsetup"]["azure"] = {
        "availability_zone": config["azure_availability_zone"],
        "region": location,
        "resource_group": resource_group,
        "storage_account": storage_account_name,
        "node_type": node_type,
        "image_url": image_url,
        "subscription_id": config["azure_subscription_id"],
        "nodes": {
            "count": config["nodes"],
            "storage": {  # default storage profiles for cloud nodes
                "root-disk": 42,
                "node-installer-disk": 2,
            },
            "base_name": "cnode",
            "type": node_type,
        },
        "client_id": "",
        "client_secret": "",
        "tenant_id": "",
        "network_cidr": str(config["subnet_cidr"]),
        "default_hyperv_gen": node_vm_gen,
        # New versions of cm-setup don't require head_node_ip. We pass "0.0.0.0" for backward-compatibility for
        # old images, that require *some* value, otherwise break on None.
        "head_node_ip": head_node_ip or "0.0.0.0",
        "cluster_tags": dict(config.get("cluster_tags", {})) | {"BCM Resource": True},
    }

    # Handle credential configuration based on authentication method
    if not config["head_node_role_definition_id"]:
        # If we're not using a role, inject credentials.
        # If we're using a role, the fields should be present, but empty strings as defined above.
        brightsetup["modules"]["brightsetup"]["azure"].update({
            "client_id": config["azure_client_id"],
            "client_secret": config["azure_client_secret"],
            "tenant_id": config["azure_tenant_id"],
        })

    # TODO: Do we still support creation of such old clusters?
    if BcmVersion(config["version"]).release >= (9, 0):
        if use_existing_vnet:
            brightsetup["modules"]["brightsetup"]["azure"]["network"] = {
                "resource_group": config["vnet_resource_group"],
                "vnet": config["vnet_network_name"],
                "subnet": config["vnet_subnet_name"],
            }
        else:
            brightsetup["modules"]["brightsetup"]["azure"]["network"] = {
                "resource_group": resource_group,
                "vnet": vnet_name,
                "subnet": vnet_subnet_name,
            }

    return brightsetup
