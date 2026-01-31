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
import re
from collections import defaultdict
from typing import TYPE_CHECKING, Generator

if TYPE_CHECKING:
    from azure.mgmt.compute.models import VirtualMachine
    from azure.mgmt.resource.resources.models import ResourceGroup

from clusterondemand.bcm_version import BcmVersion
from clusterondemand.clusternameprefix import ensure_cod_prefix
from clusterondemand.exceptions import CODException
from clusterondemandazure.azure_actions.credentials import AzureApiHelper
from clusterondemandazure.images import parse_image_or_blob_name
from clusterondemandazure.utils import name_from_r_group
from clusterondemandconfig import config

log = logging.getLogger("cluster-on-demand")


class Cluster:
    def __init__(
        self,
        name: str,
        resource_group: ResourceGroup,
        head_nodes: list[VirtualMachine] | None = None,
        compute_nodes: list[VirtualMachine] | None = None,
        image_name: str | None = None,
        version: str | None = None,
    ) -> None:
        self.name: str = name
        self.azure_client = AzureApiHelper.from_config(config)
        self.head_nodes = head_nodes or []
        self.resource_group = resource_group
        assert self.head_nodes or self.resource_group, "Cluster should have either a head node or resource_group"
        self.primary_head_node: VirtualMachine | None = None
        self.secondary_head_node: VirtualMachine | None = None
        self._set_primary_secondary_head_nodes()
        self.is_ha = bool(self.secondary_head_node)
        self.compute_nodes = compute_nodes or []
        self.image_name = image_name
        self.version = version

    @classmethod
    def find_clusters(cls, azure_client: AzureApiHelper, filters: list[str]) -> Generator[Cluster]:
        all_rgs = azure_client.resource_client.resource_groups.list()
        log.debug("Listing all VMs")
        all_vms = list(azure_client.compute_client.virtual_machines.list_all())

        regexes = [fnmatch.translate(ensure_cod_prefix(pattern)) for pattern in filters]
        head_nodes = cls.filter_cluster_head_nodes(all_vms, regexes)
        rgs = cls._filter_cluster_rgs(all_rgs, regexes)

        # We find a cluster name by:
        # 1. Looking at the BCM Cluster tag of the head node
        # 2. Looking at the BCM Cluster tag of the resource group
        # 3. If the head node is not tagged, we assume the cluster name is the first part of the head node name
        cluster_names = (
            set(
                cn for hn in head_nodes if (cn := cls._get_cluster_name_from_tags(hn))
            )
            | set(
                cn for rg in rgs if (cn := cls._get_cluster_name_from_tags(rg))
            )
            # TODO: Consider checking name only (not tags) since head node name is always cluster_name[a|b]
            | set(str(head_node.name)[:-2] for head_node in head_nodes if head_node.name)
        )

        # Construct dictionaries to map cluster names to head nodes and resource groups
        cluster_names_to_head_nodes: defaultdict[str, list[VirtualMachine]] = defaultdict(list)
        cluster_names_to_rgs: dict[str, ResourceGroup] = dict()

        for head_node in head_nodes:
            if tag_name := cls._get_cluster_name_from_tags(head_node):
                cluster_names_to_head_nodes[tag_name].append(head_node)
            else:
                # TODO: Consider checking name only (not tags) since head node name is always cluster_name[a|b]
                cluster_names_to_head_nodes[head_node.name[:-2]].append(head_node)  # type: ignore[index]

        for rg in rgs:
            if rg_cluster_name := cls._get_cluster_name_from_tags(rg):
                cluster_names_to_rgs[rg_cluster_name] = rg

        # Iterate over the cluster names, find data needed to create Cluster object
        # and yield a Cluster for each cluster name
        for cluster_name in cluster_names:
            cluster_head_nodes = cluster_names_to_head_nodes[cluster_name]
            cluster_resource_group = cluster_names_to_rgs.get(
                cluster_name
            ) or cls._find_rg_of_vm(azure_client, cluster_head_nodes[0])

            # Extract image name from head nodes, falling back to resource group
            image_name = next(
                (
                    hn.tags.get("BCM Image name")
                    for hn in cluster_head_nodes
                    if hn.tags
                ),
                None,
            ) or (
                cluster_resource_group.tags.get("BCM Image name")
                if cluster_resource_group.tags
                else None
            )

            version = (
                str(parse_image_or_blob_name(image_name)["version"]) if image_name else None
            )

            # Below logic is needed to find cluster compute nodes. We need several steps, as filtering
            # VMs of the clusters that are deployed in pre-existing RGs is not straightforward.

            # All VMs in the cluster RG
            vms_in_rg = [
                vm
                for vm in all_vms
                if (
                    cluster_resource_group.name
                    and vm.id.split("/")[4].lower() == cluster_resource_group.name.lower()
                )
            ]
            # If cluster is deployed in own RG, then the RG name will be based on the cluster name
            if (
                cluster_resource_group.name
                and name_from_r_group(cluster_resource_group.name) == cluster_name
            ):
                cluster_compute_nodes = [
                    vm
                    for vm in vms_in_rg
                    if vm not in cluster_head_nodes
                ]
            # In any other case, cluster is deployed in a pre-existing RG
            else:
                cluster_compute_nodes = [
                    vm
                    for vm in vms_in_rg
                    if vm not in cls.filter_cluster_head_nodes(
                        vms=vms_in_rg,
                        regexes=[fnmatch.translate(ensure_cod_prefix("*"))]
                    )
                ]
                # Filter further if cluster version > 10.0, when we started tagging nodes with "BCM Cluster"
                if version and BcmVersion(version).release >= (11, 0):
                    cluster_compute_nodes = [
                        vm
                        for vm in cluster_compute_nodes
                        if vm.tags and vm.tags.get("BCM Cluster") == cluster_name
                    ]

            yield cls(
                name=cluster_name,
                head_nodes=cluster_head_nodes,
                resource_group=cluster_resource_group,
                compute_nodes=cluster_compute_nodes,
                image_name=image_name,
                version=version,
            )

    @staticmethod
    def _find_rg_of_vm(azure_client: AzureApiHelper, vm: VirtualMachine) -> ResourceGroup:
        assert vm.id, "VirtualMachine object has no id"
        return azure_client.resource_client.resource_groups.get(vm.id.split("/")[4])

    @staticmethod
    def _get_cluster_name_from_tags(resource: VirtualMachine | ResourceGroup) -> str | None:
        return resource.tags.get("BCM Cluster") if resource.tags else None

    @classmethod
    def filter_cluster_head_nodes(cls, vms: list[VirtualMachine], regexes: list[str]) -> list[VirtualMachine]:
        """
        It's a head node if:
        1. It has BCM Type tag set to "Head node" and the cluster name matches one of the regexes
        2. It doesn't have BCM Type tag set and the name matches one of the regexes
           (this is needed for <11 clusters, as they're not tagged)
        """
        filtered_head_nodes = [
            vm
            for vm in vms
            if (
                vm.tags
                and vm.tags.get("BCM Type") == "Head node"
                and (cluster_name := cls._get_cluster_name_from_tags(vm))
                and any(
                    re.match(regex, cluster_name)
                    for regex in regexes
                )
            )
            # TODO: Consider checking name only (not tags) since head node name is always cluster_name[a|b]
            or vm.tags
            and "BCM Type" not in vm.tags
            and vm.name
            # Head nodes end with -a or -b. A wild VM may match to the regex, but we can't prevent the customer
            # from creating such VM, as well as tagging a non-BCM VM with our tags
            and any(re.match(f"{regex}-[ab]", vm.name) for regex in regexes if vm.name)
        ]

        return filtered_head_nodes

    @classmethod
    def _filter_cluster_rgs(cls, rgs: list[ResourceGroup], regexes: list[str]) -> list[ResourceGroup]:
        cod_rgs = [rg for rg in rgs if (rg.tags and rg.tags.get("BCM Bursting") == "on-demand")]
        filtered_rgs = [
            rg
            for rg in cod_rgs
            if (cluster_name := cls._get_cluster_name_from_tags(rg))
            and any(
                re.match(regex, cluster_name)
                for regex in regexes
            )
        ]

        return filtered_rgs

    def _set_primary_secondary_head_nodes(self) -> None:
        if not self.head_nodes:
            return
        try:
            if len(self.head_nodes) == 1:
                self.primary_head_node, self.secondary_head_node = self.head_nodes[0], None
            elif len(self.head_nodes) == 2:
                first_hn_ha_tag = self.head_nodes[0].tags.get("BCM HA") if self.head_nodes[0].tags else None
                second_hn_ha_tag = self.head_nodes[1].tags.get("BCM HA") if self.head_nodes[1].tags else None
                ha_tags = [first_hn_ha_tag, second_hn_ha_tag]

                for tag, node in zip(ha_tags, self.head_nodes):
                    if tag == "Primary":
                        self.primary_head_node = node
                    elif tag == "Secondary":
                        self.secondary_head_node = node

                if not (self.primary_head_node and self.secondary_head_node):
                    raise CODException(
                        f"Not all expected HA tags were found for the cluster {self.name}, cannot reliably "
                        f"determine primary and secondary head nodes"
                    )
            else:
                raise CODException(f"More than two head nodes found for cluster {self.name}")
        except CODException as e:
            log.warning(f"Unable to determine primary/secondary headnodes for cluster {self.name}: {e}")
