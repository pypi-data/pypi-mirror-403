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

import clusterondemandconfig

from . import configdump, configshow, tabcompletion_generate
from .command_runner import run_invoked_command

cod_commands = clusterondemandconfig.CommandContext("cm-cod")
cod_commands.add_group("cm-cod config", "Configuration operations")
cod_commands.add_command(
    "cm-cod config show",
    configshow,
    configdump.COMMAND_HELP_TEXT,
    require_eula=False
)
cod_commands.add_command(
    "cm-cod config dump",
    configdump,
    configdump.COMMAND_HELP_TEXT,
    require_eula=False
)

cod_commands.add_group("cm-cod tabcompletion", "Tab completion utilities")
cod_commands.add_command(
    "cm-cod tabcompletion generate",
    tabcompletion_generate,
    tabcompletion_generate.COMMAND_HELP_TEXT,
    require_eula=False
)


def cli_main() -> None:
    run_invoked_command(cod_commands)
