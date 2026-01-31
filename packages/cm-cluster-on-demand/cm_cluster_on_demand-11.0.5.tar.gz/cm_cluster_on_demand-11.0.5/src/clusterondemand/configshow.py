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

from itertools import chain

from clusterondemandconfig import (
    CommandContext,
    ConfigNamespace,
    config,
    human_readable_config_dump,
    load_configuration_for_parameters
)
from clusterondemandconfig.parameter import Parameter

from . import configuration
from .import_utils import load_module_attribute

config_ns = ConfigNamespace("config.show")
config_ns.import_namespace(configuration.common_ns)


COMMAND_HELP_TEXT = """
Display the entire configuration within a table. Note that this command takes into account any existing
config files, and environment variables, both of which which might impact the values in the generated config;
to avoid that, use '--no-system-config', which will generate a config from only the hardcoded defaults and
the config files specified with --config.
"""


def _load_module_parameters(module_name: str, commands_name: str) -> list[Parameter]:
    commands: CommandContext = load_module_attribute(module_name, commands_name)
    return [] if commands is None else commands.parameters()


def run_command() -> None:
    aws_parameters = _load_module_parameters("clusterondemandaws.cli", "aws_commands")
    azure_parameters = _load_module_parameters("clusterondemandazure.cli", "azure_commands")
    openstack_parameters = _load_module_parameters("clusterondemandopenstack.cli", "openstack_commands")
    oci_parameters = _load_module_parameters("clusterondemandoci.cli", "oci_commands")
    forge_parameters = _load_module_parameters("clusterondemandforge.cli", "forge_commands")
    gcp_parameters = _load_module_parameters("clusterondemandgcp.cli", "gcp_commands")

    config_to_dump = load_configuration_for_parameters(
        chain(aws_parameters, azure_parameters, openstack_parameters, oci_parameters,
              forge_parameters, gcp_parameters),
        system_config_files=configuration.get_system_config_files(),
        enforcing_config_files=configuration.get_enforcing_config_files()
    )

    print(human_readable_config_dump(config_to_dump, show_secrets=config["show_secrets"]))  # type: ignore
