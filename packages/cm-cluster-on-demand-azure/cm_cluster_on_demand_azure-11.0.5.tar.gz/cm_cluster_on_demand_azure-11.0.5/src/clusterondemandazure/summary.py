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

import typing

from clusterondemand.summary import SummaryGenerator, SummaryType

if typing.TYPE_CHECKING:
    from prettytable import PrettyTable

    from clusterondemand.images.find import CODImage
    from clusterondemand.node_definition import NodeDefinition
    from clusterondemandconfig.configuration import ConfigurationView


class AzureSummaryGenerator(SummaryGenerator):
    """Generate the summary for creation of Azure clusters and nodes."""

    def __init__(self,
                 config: ConfigurationView,
                 summary_type: SummaryType,
                 region: str | None = None,
                 head_node_definition: NodeDefinition | None = None,
                 head_image: CODImage | None = None,
                 instance_id: str | None = None,
                 node_definition: NodeDefinition | None = None,
                 public_ip: str | None = None) -> None:
        super().__init__(
            config["name"] if config else "",
            region=region,
            config=config,
            summary_type=summary_type,
            primary_head_node_definition=head_node_definition,
            head_image=head_image,
            node_definitions=[node_definition] if node_definition else None,
        )
        self._instance_id = instance_id
        self._public_ip = public_ip

    def _add_rows(self, table: PrettyTable) -> None:
        if self._type == SummaryType.Proposal:
            self._add_resource_group(table)
            self._add_region(table)

        if self._type == SummaryType.Overview:
            self._add_deployment_details(table)

    def _add_deployment_details(self, table: PrettyTable) -> None:
        table.add_row(["Head node ID:", self._instance_id])
        table.add_row(["Public IP:", self._public_ip])

    def _add_resource_group(self, table: PrettyTable) -> None:
        if self._config and "resource_group" in self._config:
            table.add_row(["Resource Group:", self._config["resource_group"]])
