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

from clusterondemandconfig import ConfigNamespace, config, generate_tabcompletion_for_command_context

from . import configuration, exceptions, import_utils

TOOL_MAPPING = {
    "cm-cod": ("clusterondemand.cli", "cod_commands"),
    "cm-cod-os": ("clusterondemandopenstack.cli", "openstack_commands"),
    "cod": ("clusterondemandopenstack.cli", "openstack_commands"),
    "cm-cod-aws": ("clusterondemandaws.cli", "aws_commands"),
    "cm-cod-azure": ("clusterondemandazure.cli", "azure_commands"),
    "cm-cod-oci": ("clusterondemandoci.cli", "oci_commands"),
    "cm-cod-forge": ("clusterondemandforge.cli", "forge_commands"),
    "cm-cod-gcp": ("clusterondemandgcp.cli", "gcp_commands"),
}

COMMAND_HELP_TEXT = """
Generate a bash tab-completion script that can be loaded into your current bash session or stored as
a file in the sytem bash_completion.d folder. When this script is active, you can press <tab> to
have bash complete groups, commands, flags as well as certain possible values for certain parameters.

If bash cannot resolve the prefix to a single value, then all possible completions will be shown.

Examples:
  cm-cod-os cl<tab> -> cm-cod-os cluster,
  cm-cod-os cluster cr<tab> -> cm-cod-os cluster create,
  cm-cod-os cluster create --he<tab> -> cm-cod-os cluster create --help,
"""

config_ns = ConfigNamespace("tabcompletion.generate")
config_ns.import_namespace(configuration.common_ns)
config_ns.add_positional_parameter(
    "tool",
    # TODO: CM-25743, add choices attribute to positional parameter
    help="The tool for which the tab completion script is generated",
    require_value=True,
)


def run_command() -> None:
    if config["tool"] not in TOOL_MAPPING.keys():
        raise exceptions.CODException(f"{config['tool']} must be one of {', '.join(TOOL_MAPPING.keys())}")

    module, commands = TOOL_MAPPING[config["tool"]]
    command_context = import_utils.load_module_attribute(module, commands)

    if not command_context:
        raise exceptions.CODException(f"Could not import {module}")

    generate_tabcompletion_for_command_context(config["tool"], command_context)
