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

import clusterondemand.configuration
import clusterondemandconfig
from clusterondemand.command_runner import run_invoked_command

from . import (
    clustercreate,
    clusterdelete,
    clusterlist,
    clusterstart,
    clusterstop,
    configdump,
    configshow,
    configuration,
    eula,
    imagelist,
    vmsizelist
)

log = logging.getLogger("cluster-on-demand")

azure_commands = clusterondemandconfig.CommandContext("cm-cod-azure")
azure_commands.add_group("cm-cod-azure cluster", "Manage clusters", aliases=["c"])
azure_commands.add_command(
    "cm-cod-azure cluster create",
    clustercreate,
    "Create a new cluster",
    aliases=["c"],
    important_help_sections=[
        clustercreate.config_ns,
        configuration.azurecredentials_ns,
        clusterondemand.configuration.clustercreatepassword_ns,
        clusterondemand.configuration.clustercreatelicense_ns
    ]
)
azure_commands.add_command(
    "cm-cod-azure cluster delete",
    clusterdelete,
    "Delete an existing cluster",
    aliases=["d"],
    important_help_sections=[
        clusterdelete.config_ns,
        configuration.azurecredentials_ns,
    ]
)
azure_commands.add_command(
    "cm-cod-azure cluster list",
    clusterlist,
    "List existing azure clusters",
    aliases=["l"],
    important_help_sections=[
        clusterlist.config_ns,
        configuration.azurecredentials_ns,
    ]
)
azure_commands.add_command(
    "cm-cod-azure cluster start",
    clusterstart,
    "Start the head node instances for clusters",
    important_help_sections=[
        clusterstart.config_ns,
        configuration.azurecredentials_ns,
    ]
)
azure_commands.add_command(
    "cm-cod-azure cluster stop",
    clusterstop,
    "Stop (deallocate) all instances for clusters",
    important_help_sections=[
        clusterstop.config_ns,
        configuration.azurecredentials_ns,
    ]
)

azure_commands.add_group("cm-cod-azure vmsizes", "VM mappings")
azure_commands.add_command(
    "cm-cod-azure vmsizes list",
    vmsizelist,
    "List available VMSizes",
    aliases=["l"],
    important_help_sections=[
        vmsizelist.config_ns,
        configuration.azurecredentials_ns,
    ]
)
azure_commands.add_group("cm-cod-azure config", "Configuration operations")
azure_commands.add_command(
    "cm-cod-azure config dump",
    configdump,
    configdump.COMMAND_HELP_TEXT,
    require_eula=False
)
azure_commands.add_command(
    "cm-cod-azure config show",
    configshow,
    configshow.COMMAND_HELP_TEXT,
    require_eula=False
)

azure_commands.add_group("cm-cod-azure image", "Operations on cluster images", aliases=["i"])
azure_commands.add_command(
    "cm-cod-azure image list",
    imagelist,
    "list images",
    aliases=["l"],
    important_help_sections=[
        imagelist.config_ns,
        configuration.azurecredentials_ns,
    ]
)


def cli_main() -> None:
    run_invoked_command(azure_commands, pre_run_check=eula.check_azure_eula)
