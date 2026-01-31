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

import fnmatch
import logging
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from azure.mgmt.compute.models import VirtualMachine
    from azure.mgmt.resource.resources.models import ResourceGroup

from azure.core.exceptions import ResourceNotFoundError

from clusterondemand.bcm_version import BcmVersion
from clusterondemand.clusternameprefix import clusterprefix_ns, ensure_cod_prefix
from clusterondemand.utils import confirm, confirm_ns, log_no_clusters_found, multithread_run
from clusterondemandazure.base import ClusterCommand
from clusterondemandazure.cluster import Cluster
from clusterondemandazure.utils import COD_RESOURCE_GROUP_SUFFIX
from clusterondemandconfig import ConfigNamespace, config
from clusterondemandconfig.configuration_validation import cannot_use_together

from .configuration import azurecommon_ns

log = logging.getLogger("cluster-on-demand")


HR = "---------------------------------------------------------------------"

AZURE_STD_NAME_FOR_PDNS_ZONE_FOR_PRIVATE_STORAGE_ACCOUNTS = "privatelink.blob.core.windows.net"

config_ns = ConfigNamespace("azure.cluster.delete", "cluster delete parameter")
config_ns.import_namespace(azurecommon_ns)
config_ns.import_namespace(clusterprefix_ns)
config_ns.import_namespace(confirm_ns)
config_ns.add_repeating_positional_parameter(
    "filters",
    help="Cluster names or patterns. Wildcards are supported (e.g: \\*)",
)
config_ns.add_parameter(
    "resource_group",
    help="Name of resource group to delete cluster resources from. "
    "Only the resources created by COD will be deleted. Useful to clean up "
    "resources from failed deployments, or otherwise broken clusters",
)
config_ns.add_switch_parameter(
    "partial",
    help="Perform a partial removal which removes everything within the resource group except for "
         "the storage account and the images stored within (both head node and node-installer images) "
         "but not the resource group itself. "
         "This enables creating clusters more quickly by reusing existing resource groups."
)
config_ns.add_switch_parameter(
    "dry_run",
    help="Do not actually delete the resources."
)

config_ns.add_validation(cannot_use_together("filters", "resource_group"))


def run_command() -> None:
    ClusterDelete().run()


class ClusterDelete(ClusterCommand):
    def delete_virtual_machines(self, resource_group_name: str, cluster_name: str | None = None) -> None:
        vms = list(self.azure_api.compute_client.virtual_machines.list(resource_group_name))
        regexes = [
            fnmatch.translate(rf"{ensure_cod_prefix(pattern)}")
            for pattern in [cluster_name or "*"]
        ]
        head_nodes = Cluster.filter_cluster_head_nodes(regexes=regexes, vms=vms)
        head_node_names = [vm.name for vm in head_nodes]

        removal_ops = []
        for entity in vms:
            if self._match_bcm_tags(entity, cluster_name):
                if entity.name in head_node_names:
                    self.delete_role_assignments(entity, resource_group_name)
                log.info(f"Deleting virtual machine {entity.name}")
                if not config["dry_run"]:
                    async_removal = self.azure_api.compute_client.virtual_machines.begin_delete(resource_group_name,
                                                                                                entity.name)
                    removal_ops.append(async_removal)

        for removal in removal_ops:
            removal.wait()

    def delete_role_assignments(self, vm: VirtualMachine, resource_group_name: str) -> None:
        if not (vm.identity and vm.identity.type == "SystemAssigned" and vm.identity.principal_id is not None):
            return
        auth_client = self.azure_api.authorization_management_client
        for role_assignment in auth_client.role_assignments.list_for_resource_group(
                resource_group_name=resource_group_name, filter=f"principalid eq '{vm.identity.principal_id}'"):
            log.info(f"Deleting role assignment {role_assignment.name} of virtual machine {vm.name}")
            if not config["dry_run"]:
                auth_client.role_assignments.delete(role_assignment.scope, role_assignment.name)

    def delete_network_interfaces(self, resource_group_name: str, cluster_name: str | None = None) -> None:
        removal_ops: list[Any] = []
        for entity in self.azure_api.network_client.network_interfaces.list(resource_group_name):
            if self._match_bcm_tags(entity, cluster_name):
                log.info(f"Deleting network interface {entity.name}")
                if not config["dry_run"]:
                    assert entity.name, "Network interface name cannot be None"
                    async_removal = self.azure_api.network_client.network_interfaces.begin_delete(resource_group_name,
                                                                                                  entity.name)
                    removal_ops.append(async_removal)
        for removal in removal_ops:
            removal.wait()

    def delete_private_endpoints(self, resource_group_name: str, cluster_name: str | None = None) -> None:
        removal_ops: list[Any] = []
        for entity in self.azure_api.network_client.private_endpoints.list(resource_group_name):
            if self._match_bcm_tags(entity, cluster_name):
                log.info(f"Deleting private endpoint {entity.name}")
                if not config["dry_run"]:
                    assert entity.name, "Private endpoint name cannot be None"
                    async_removal = self.azure_api.network_client.private_endpoints.begin_delete(resource_group_name,
                                                                                                 entity.name)
                    removal_ops.append(async_removal)
        for removal in removal_ops:
            removal.wait()

    def delete_virtual_networks(self, resource_group_name: str, cluster_name: str | None = None) -> None:
        removal_ops: list[Any] = []
        for entity in self.azure_api.network_client.virtual_networks.list(resource_group_name):
            if self._match_bcm_tags(entity, cluster_name):
                log.info(f"Deleting virtual network {entity.name}")
                if not config["dry_run"]:
                    assert entity.name, "Virtual network name cannot be None"
                    async_removal = self.azure_api.network_client.virtual_networks.begin_delete(resource_group_name,
                                                                                                entity.name)
                    removal_ops.append(async_removal)
        for removal in removal_ops:
            removal.wait()

    def delete_public_ips(self, resource_group_name: str, cluster_name: str | None = None) -> None:
        removal_ops: list[Any] = []
        for entity in self.azure_api.network_client.public_ip_addresses.list(resource_group_name):
            if self._match_bcm_tags(entity, cluster_name):
                log.info(f"Deleting public ip address {entity.name}")
                if not config["dry_run"]:
                    assert entity.name, "Public IP address name cannot be None"
                    async_removal = self.azure_api.network_client.public_ip_addresses.begin_delete(resource_group_name,
                                                                                                   entity.name)
                    removal_ops.append(async_removal)
        for removal in removal_ops:
            removal.wait()

    def delete_security_groups(self, resource_group_name: str, cluster_name: str | None = None) -> None:
        removal_ops: list[Any] = []
        for entity in self.azure_api.network_client.network_security_groups.list(resource_group_name):
            if self._match_bcm_tags(entity, cluster_name):
                log.info(f"Deleting network security group {entity.name}")
                if not config["dry_run"]:
                    assert entity.name, "Network security group name cannot be None"
                    async_removal = self.azure_api.network_client.network_security_groups.begin_delete(
                        resource_group_name, entity.name)
                    removal_ops.append(async_removal)
        for removal in removal_ops:
            removal.wait()

    def delete_availability_sets(self, resource_group_name: str, cluster_name: str | None = None) -> None:
        for entity in self.azure_api.compute_client.availability_sets.list(resource_group_name):
            if self._match_bcm_tags(entity, cluster_name):
                log.info(f"Deleting availability set {entity.name}")
                if not config["dry_run"]:
                    assert entity.name, "Availability set name cannot be None"
                    self.azure_api.compute_client.availability_sets.delete(
                        resource_group_name, entity.name)

    def delete_disks(self, resource_group_name: str, cluster_name: str | None = None) -> None:
        removal_ops: list[Any] = []
        for entity in self.azure_api.compute_client.disks.list_by_resource_group(resource_group_name):
            if self._match_bcm_tags(entity, cluster_name):
                log.info(f"Deleting disk {entity.name}")
                if not config["dry_run"]:
                    assert entity.name, "Disk name cannot be None"
                    async_removal = self.azure_api.compute_client.disks.begin_delete(resource_group_name, entity.name)
                    removal_ops.append(async_removal)
        for removal in removal_ops:
            removal.wait()

    def delete_snapshots(self, resource_group_name: str, cluster_name: str | None = None) -> None:
        removal_ops: list[Any] = []
        for entity in self.azure_api.compute_client.snapshots.list_by_resource_group(resource_group_name):
            if self._match_bcm_tags(entity, cluster_name):
                log.info(f"Deleting snapshot {entity.name}")
                if not config["dry_run"]:
                    assert entity.name, "Snapshot name cannot be None"
                    async_removal = self.azure_api.compute_client.snapshots.begin_delete(resource_group_name,
                                                                                         entity.name)
                    removal_ops.append(async_removal)
        for removal in removal_ops:
            removal.wait()

    def delete_storage_accounts(self, resource_group_name: str, cluster_name: str | None = None) -> None:
        for entity in self.azure_api.storage_client.storage_accounts.list_by_resource_group(resource_group_name):
            if self._match_bcm_tags(entity, cluster_name):
                log.info(f"Deleting storage account {entity.name}")
                if not config["dry_run"]:
                    assert entity.name, "Storage account name cannot be None"
                    self.azure_api.storage_client.storage_accounts.delete(resource_group_name, entity.name)

    def delete_images(self, resource_group_name: str, cluster_name: str | None = None) -> None:
        removal_ops: list[Any] = []
        for entity in self.azure_api.compute_client.images.list_by_resource_group(resource_group_name):
            if self._match_bcm_tags(entity, cluster_name):
                log.info(f"Deleting image {entity.name}")
                if not config["dry_run"]:
                    assert entity.name, "Image name cannot be None"
                    async_removal = self.azure_api.compute_client.images.begin_delete(resource_group_name, entity.name)
                    removal_ops.append(async_removal)
        for removal in removal_ops:
            removal.wait()

    def delete_nat_gateways(self, resource_group_name: str, cluster_name: str | None = None) -> None:
        removal_ops: list[Any] = []
        for nat_gateway in self.azure_api.network_client.nat_gateways.list(resource_group_name):
            if self._match_bcm_tags(nat_gateway, cluster_name):
                log.info(f"Deleting NAT gateway {nat_gateway.name}")
                if not config["dry_run"]:
                    assert nat_gateway.name, "NAT gateway name cannot be None"
                    # First, we need to disassociate the NAT gateway from the subnet
                    nat_gateway.subnets = []
                    nat_gw_future = self.azure_api.network_client.nat_gateways.begin_create_or_update(
                        resource_group_name, nat_gateway.name, nat_gateway)
                    nat_gw_future.wait()
                    async_removal = self.azure_api.network_client.nat_gateways.begin_delete(
                        resource_group_name, nat_gateway.name)
                    removal_ops.append(async_removal)
        for removal in removal_ops:
            removal.wait()

    def delete_storage_account_plink_privdns_zones(self, resource_group_name: str) -> None:
        """Delete PDNS zone (if unused)

        In a pre-existing resource groups, the PDNS zone for the private link/private endpoint to the cluster storage
        account is shared. I.e. each cluster has its own storage account, but shares PDNS zone with other clusters in
        the same resource group.

        This function deletes the privdns zone if it is unused, i.e. no more vnet links to it.

        Args:
            resource_group_name: The name of the resource group containing the
                                 private DNS zone.
        """

        entities = self.azure_api.privdns_management_client.private_zones.list_by_resource_group(
            resource_group_name)
        for entity in entities:
            # Look for the standard name,
            # see https://learn.microsoft.com/en-us/azure/private-link/private-endpoint-dns:
            if entity.name != AZURE_STD_NAME_FOR_PDNS_ZONE_FOR_PRIVATE_STORAGE_ACCOUNTS:
                continue
            # From https://learn.microsoft.com/en-us/azure/dns/private-dns-virtual-network-links
            # "When you delete a virtual network, all the virtual network links and autoregistered DNS records
            # associated with it in different private DNS zones are automatically deleted."
            #
            # If there are still vnet links left at this point, they should belong to other clusters in the same
            # resource group.
            assert entity.name, "Private DNS zone name cannot be None"
            vnet_links = list(self.azure_api.privdns_management_client.virtual_network_links.list(
                resource_group_name, entity.name))
            if vnet_links:
                log.info(f"Private DNS zone {entity.name} still has virtual network links, not deleting it")
                return

            log.info(
                f"Deleting private DNS zone {entity.name} in resource group {resource_group_name}"
            )
            if config["dry_run"]:
                return

            async_removal = self.azure_api.privdns_management_client.private_zones.begin_delete(
                resource_group_name, entity.name)
            async_removal.wait()

            return  # There is only one privdns zone per cluster
        log.warning(f"No private DNS zone found in resource group {resource_group_name}")

    @classmethod
    def _match_bcm_tags(cls, entity: Any, cluster_name: str | None) -> bool:
        bcm_cluster_tag_match = entity.tags and entity.tags.get("BCM Cluster", False) == cluster_name
        bcm_resource_tag_match = entity.tags and entity.tags.get("BCM Resource", False)
        return (cluster_name and bcm_cluster_tag_match) or (not cluster_name and bcm_resource_tag_match)

    def delete_resources(self, resource_group: ResourceGroup, cluster_name: str | None = None) -> None:
        """
        Specifying "cluster_name" forces delete_* functions to only delete resources tagged with "BCM Cluster" tag
        This function can be called with cluster_name=None to revert to old behavior of deleting all resources
        tagged with "BCM Resource" tag. This is needed when working with old clusters without full tagging
        """
        assert resource_group.name, "Resource group name cannot be None"
        resource_group_name = resource_group.name
        # For clusters older than 9.0, cmaemon doesn't tag the VMs. So they don't get deleted and
        # delete_virtual_networks fails. So, if the RG is going to get deleted, let's do the
        # whole thing at once so the deletion will work in any cluster
        if (
            not config["resource_group"]  # --resource-group is used to *clean* the RG, not delete it
            and not config["partial"]  # --partial is used to keep the RG with the images and storage account
            and resource_group.tags
            and resource_group.tags.get("BCM Resource", False)
        ):
            log.info(f"Deleting resource group {resource_group_name}")
            if not config["dry_run"]:
                async_removal = self.azure_api.resource_client.resource_groups.begin_delete(resource_group_name)
                async_removal.wait()
        else:
            log.info(f"Deleting resources in resource group {resource_group_name}")

            self.delete_virtual_machines(resource_group_name, cluster_name=cluster_name)
            self.delete_private_endpoints(resource_group_name, cluster_name=cluster_name)
            self.delete_network_interfaces(resource_group_name, cluster_name=cluster_name)
            self.delete_virtual_networks(resource_group_name, cluster_name=cluster_name)
            self.delete_security_groups(resource_group_name, cluster_name=cluster_name)
            self.delete_disks(resource_group_name, cluster_name=cluster_name)
            self.delete_snapshots(resource_group_name, cluster_name=cluster_name)
            self.delete_availability_sets(resource_group_name, cluster_name=cluster_name)
            self.delete_nat_gateways(resource_group_name, cluster_name=cluster_name)
            self.delete_public_ips(resource_group_name, cluster_name=cluster_name)
            self.delete_storage_account_plink_privdns_zones(resource_group_name)

            if not config["partial"]:
                self.delete_images(resource_group_name, cluster_name=cluster_name)
                self.delete_storage_accounts(resource_group_name, cluster_name=cluster_name)

        log.info("Resources deleted successfully")

    def get_resource_group(self, rg_name: str) -> ResourceGroup | None:
        try:
            return self.azure_api.resource_client.resource_groups.get(rg_name)  # type: ignore[no-any-return]
        except ResourceNotFoundError as e:
            if e.error:
                log.error(f"Code: {e.error.code}, {e.error.message}")
            else:
                log.error(f"Resource not found: {e}")
            return None

    def run(self) -> None:
        self._validate_params()
        if not config["filters"] and not config["resource_group"]:
            log.error(
                "Need to specify either cluster name, or resource group name of clusters to be deleted"
            )
            return

        if config["dry_run"]:
            log.warning("Running in dry run mode. The resources will not be deleted.")

        if config["resource_group"]:
            resource_group = self.get_resource_group(config["resource_group"])
            if not resource_group:
                return

            if not confirm(
                f"This will delete the all BCM resources from the resource group: "
                f"{config['resource_group']} continue?"
            ):
                return

            self.delete_resources(resource_group)
            return

        clusters = list(Cluster.find_clusters(self.azure_api, config["filters"]))
        if not clusters:
            log_no_clusters_found("delete")
            return

        # We started tagging cnodes, their nics, storage accounts, etc. with "BCM Cluster" tag from v11
        pre_v11_clusters = [
            cluster
            for cluster in clusters
            if cluster.version is None or BcmVersion(cluster.version).release < (11, 0)
        ]
        for c in pre_v11_clusters:
            if c.resource_group.name != c.name + COD_RESOURCE_GROUP_SUFFIX:
                log.warning(f"Cluster {c.name!r} seems to run older BCM version and is deployed in a pre-existing "
                            f"resource group {c.resource_group.name!r}. Since older clusters were not fully tagged, we "
                            f"can't reliably link all BCM resources to the cluster, so *all* BCM resources will be "
                            f"deleted (any cluster that was deployed in {c.resource_group.name!r}). Continue only if "
                            f"this is the desired outcome."
                            )

        if not confirm(
            f"This will delete the clusters {' '.join(cluster.name for cluster in clusters)}, continue?"
        ):
            return

        multithread_run(
            self.delete_resources, [
                # If BCM version > 11, we are guaranteed to have cluster name tag, linking a resource to the cluster
                # Otherwise, we want to fall back to the old logic, remove resources without specifying name
                (
                    c.resource_group,
                    c.name if c.version and BcmVersion(c.version).release >= (11, 0) else None
                ) for c in clusters
            ], config["max_threads"]
        )

    def _validate_params(self) -> None:
        self._validate_access_credentials()
