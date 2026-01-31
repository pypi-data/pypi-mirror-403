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

import copy
import shlex
from abc import ABC, abstractmethod
from base64 import b64encode
from typing import Any


class SignalHandler(ABC):
    def __init__(self, status_log_prefix: str):
        self.log_prefix = status_log_prefix
        super().__init__()

    @abstractmethod
    def get_init_commands(self) -> list[str]:
        pass

    @abstractmethod
    def get_files(self) -> list[dict[str, Any]]:
        pass

    @abstractmethod
    def get_status_log_commands(self, status: str) -> list[str]:
        pass

    @abstractmethod
    def get_config_complete_commands(self) -> list[str]:
        pass


class SimpleSignalHandler(SignalHandler):

    _ERROR_HANDLER = """\
set -e
function error_handler {
    read line file <<<$(caller)
    echo \"An error occurred in line $line of $file: exit code '$1' while running: '$2'\"
    exit 1
}
trap 'error_handler $? "$BASH_COMMAND"' ERR
"""

    def get_init_commands(self) -> list[str]:
        return [
            self._ERROR_HANDLER,
        ]

    def get_files(self) -> list[dict[str, Any]]:
        return []

    def get_config_complete_commands(self) -> list[str]:
        return self.get_status_log_commands("cloud-init: Complete.")

    def get_status_log_commands(self, status: str) -> list[str]:
        escaped_status = shlex.quote(f"{self.log_prefix} {status}")
        return [f"echo {escaped_status}"]


class CloudConfig(dict):  # type: ignore
    def __init__(self, signal_handler: SignalHandler) -> None:
        self.signal_handler = signal_handler
        self["write_files"] = []
        self["bootcmd"] = []
        self["runcmd"] = signal_handler.get_init_commands()
        self["disable_ec2_metadata"] = False
        for file in signal_handler.get_files():
            self.add_file(file["path"], file["content"])

    def add_status_commands(self, status: str) -> None:
        self.add_commands(self.signal_handler.get_status_log_commands(status))

    def add_config_complete_commands(self) -> None:
        self.add_commands(self.signal_handler.get_config_complete_commands())

    def enable_metadata(self, enable_metadata: bool) -> None:
        self["disable_ec2_metadata"] = not enable_metadata

    def add_file(self, path: str, content: bytes | str | dict[str, Any], base64: bool = False,
                 permissions: str | None = None) -> None:
        write_file: dict[str, Any] = {
            "path": path
        }

        if base64:
            write_file["encoding"] = "base64"
            write_file["content"] = b64encode(content)  # type: ignore
        else:
            write_file["content"] = content

        if permissions is not None:
            write_file["permissions"] = permissions

        self["write_files"].append(write_file)

    def add_boot_command(self, command: str) -> None:
        self["bootcmd"].append(command)

    def add_boot_commands(self, commands: list[str]) -> None:
        self["bootcmd"] += commands

    def add_command(self, command: str) -> None:
        self["runcmd"].append(command)

    def add_commands(self, commands: list[str]) -> None:
        self["runcmd"] += commands

    def to_dict(self) -> dict[str, Any]:
        result = copy.deepcopy(self)
        return dict(result)
