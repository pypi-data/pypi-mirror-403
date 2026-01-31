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
    imagelist,
    instancetypelist
)
from .images import findimages_ns

log = logging.getLogger("cluster-on-demand")


aws_commands = clusterondemandconfig.CommandContext("cm-cod-aws")
aws_commands.add_group("cm-cod-aws cluster", "Manage clusters", aliases=["c"])
aws_commands.add_command(
    "cm-cod-aws cluster create",
    clustercreate,
    "Create a new cluster",
    aliases=["c"],
    important_help_sections=[
        clustercreate.config_ns,
        findimages_ns,
        clusterondemand.configuration.clustercreatepassword_ns,
        clusterondemand.configuration.clustercreatelicense_ns,
        configuration.awscredentials_ns
    ]
)
aws_commands.add_command(
    "cm-cod-aws cluster list",
    clusterlist,
    "List all of the recognized clusters (VPCs)",
    aliases=["l"],
    important_help_sections=[clusterlist.config_ns, configuration.awscredentials_ns]
)
aws_commands.add_command(
    "cm-cod-aws cluster delete",
    clusterdelete,
    "Delete all resources in a cluster",
    aliases=["d", "r", "remove"],
    important_help_sections=[clusterdelete.config_ns, configuration.awscredentials_ns]
)
aws_commands.add_command(
    "cm-cod-aws cluster start",
    clusterstart,
    "Start the head node instances for clusters",
    important_help_sections=[clusterstart.config_ns, configuration.awscredentials_ns]
)
aws_commands.add_command(
    "cm-cod-aws cluster stop",
    clusterstop,
    "Stop all instances for clusters",
    important_help_sections=[clusterstop.config_ns, configuration.awscredentials_ns]
)
aws_commands.add_group("cm-cod-aws image", "Manage images", aliases=["i"])
aws_commands.add_command(
    "cm-cod-aws image list",
    imagelist,
    "List available Bright head node images",
    aliases=["l"],
    important_help_sections=[imagelist.config_ns, findimages_ns, configuration.awscredentials_ns]
)
aws_commands.add_group("cm-cod-aws instancetype", "Instance types")
aws_commands.add_command(
    "cm-cod-aws instancetype list",
    instancetypelist,
    "List available instance types",
    aliases=["l"],
    important_help_sections=[instancetypelist.config_ns, configuration.awscredentials_ns]
)
aws_commands.add_group("cm-cod-aws config", "Configuration operations")
aws_commands.add_command(
    "cm-cod-aws config dump",
    configdump,
    configdump.COMMAND_HELP_TEXT,
    require_eula=False
)
aws_commands.add_command(
    "cm-cod-aws config show",
    configshow,
    configshow.COMMAND_HELP_TEXT,
    require_eula=False
)


def cli_main() -> None:
    run_invoked_command(aws_commands)
