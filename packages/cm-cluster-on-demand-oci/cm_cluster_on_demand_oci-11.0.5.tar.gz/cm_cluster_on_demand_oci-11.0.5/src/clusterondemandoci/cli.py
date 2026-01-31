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

# isort: skip_file

import logging

import clusterondemand.configuration
import clusterondemandconfig
from clusterondemand.command_runner import run_invoked_command

from . import (
    clustercreate,
    clusterdelete,
    clusterlist,
    configdump,
    configshow,
    configuration,
    clusterstop,
    clusterstart,
    imagelist
)
from .images import findimages_ns

log = logging.getLogger("cluster-on-demand")

oci_commands = clusterondemandconfig.CommandContext("cm-cod-oci")
oci_commands.add_group("cm-cod-oci cluster", "Manage clusters", aliases=["c"])
oci_commands.add_command(
    "cm-cod-oci cluster create",
    clustercreate,
    "Create a new cluster",
    aliases=["c"],
    important_help_sections=[
        clustercreate.config_ns,
        findimages_ns,
        clusterondemand.configuration.clustercreatepassword_ns,
        clusterondemand.configuration.clustercreatelicense_ns,
        configuration.ocicredentials_ns
    ]
)
oci_commands.add_command(
    "cm-cod-oci cluster list",
    clusterlist,
    "List all of the recognized clusters (VCNs)",
    aliases=["l"],
    important_help_sections=[clusterlist.config_ns, configuration.ocicredentials_ns]
)
oci_commands.add_command(
    "cm-cod-oci cluster delete",
    clusterdelete,
    "Delete all resources in a cluster",
    aliases=["d", "r", "remove"],
    important_help_sections=[clusterdelete.config_ns, configuration.ocicredentials_ns]
)
oci_commands.add_command(
    "cm-cod-oci cluster start",
    clusterstart,
    "Start the head node instances for clusters",
    important_help_sections=[clusterstart.config_ns, configuration.ocicredentials_ns]
)
oci_commands.add_command(
    "cm-cod-oci cluster stop",
    clusterstop,
    "Stop all instances for clusters",
    important_help_sections=[clusterstop.config_ns, configuration.ocicredentials_ns]
)
oci_commands.add_group("cm-cod-oci image", "Manage images", aliases=["i"])
oci_commands.add_command(
    "cm-cod-oci image list",
    imagelist,
    "List available Bright head node images",
    aliases=["l"],
    important_help_sections=[imagelist.config_ns, findimages_ns, configuration.ocicredentials_ns]
)
# oci_commands.add_group("cm-cod-oci instancetype", "Instance types")
# oci_commands.add_command(
#     "cm-cod-oci instancetype list",
#     instancetypelist,
#     "List available instance types",
#     aliases=["l"],
#     important_help_sections=[instancetypelist.config_ns, configuration.ocicredentials_ns]
# )
oci_commands.add_group("cm-cod-oci config", "Configuration operations")
oci_commands.add_command(
    "cm-cod-oci config dump",
    configdump,
    configdump.COMMAND_HELP_TEXT,
    require_eula=False
)
oci_commands.add_command(
    "cm-cod-oci config show",
    configshow,
    configshow.COMMAND_HELP_TEXT,
    require_eula=False
)
#


def cli_main():
    run_invoked_command(oci_commands)
