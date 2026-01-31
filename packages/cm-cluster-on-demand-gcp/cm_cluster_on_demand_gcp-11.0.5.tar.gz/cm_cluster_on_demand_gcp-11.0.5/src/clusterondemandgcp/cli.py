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
    imagelist
)

log = logging.getLogger("cluster-on-demand")


gcp_commands = clusterondemandconfig.CommandContext("cm-cod-gcp")
gcp_commands.add_group("cm-cod-gcp cluster", "Manage clusters", aliases=["c"])
gcp_commands.add_command(
    "cm-cod-gcp cluster create",
    clustercreate,
    "Create a new cluster",
    aliases=["c"],
    important_help_sections=[
        clustercreate.config_ns,
        configuration.gcpcredentials_ns,
        clusterondemand.configuration.clustercreatepassword_ns,
        clusterondemand.configuration.clustercreatelicense_ns,
    ]
)
gcp_commands.add_command(
    "cm-cod-gcp cluster delete",
    clusterdelete,
    "Delete clusters",
    aliases=["d"],
    important_help_sections=[
        clusterdelete.config_ns,
        configuration.gcpcredentials_ns,
    ]
)
gcp_commands.add_command(
    "cm-cod-gcp cluster list",
    clusterlist,
    "List clusters",
    aliases=["l"],
    important_help_sections=[
        clusterlist.config_ns,
        configuration.gcpcredentials_ns,
    ]
)
gcp_commands.add_command(
    "cm-cod-gcp cluster start",
    clusterstart,
    "Start the head node instances for clusters",
    important_help_sections=[
        clusterlist.config_ns,
        configuration.gcpcredentials_ns,
    ]
)
gcp_commands.add_command(
    "cm-cod-gcp cluster stop",
    clusterstop,
    "Stop all instances for clusters",
    important_help_sections=[
        clusterlist.config_ns,
        configuration.gcpcredentials_ns,
    ]
)

gcp_commands.add_group("cm-cod-gcp image", "Manage images", aliases=["i"])
gcp_commands.add_command(
    "cm-cod-gcp image list",
    imagelist,
    "List images",
    aliases=["l"],
    important_help_sections=[
        imagelist.config_ns,
        configuration.gcpcredentials_ns,
    ]
)
gcp_commands.add_group("cm-cod-gcp config", "Configuration operations")
gcp_commands.add_command(
    "cm-cod-gcp config dump",
    configdump,
    configdump.COMMAND_HELP_TEXT,
    require_eula=False
)
gcp_commands.add_command(
    "cm-cod-gcp config show",
    configshow,
    configshow.COMMAND_HELP_TEXT,
    require_eula=False
)


def cli_main() -> None:
    run_invoked_command(gcp_commands)
