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

import os
import re
import subprocess
from typing import Any

from clusterondemandconfig.configuration import ConfigurationView
from clusterondemandconfig.parameter import Parameter

from .exceptions import CODException

SSH_KEYGEN_REGEX = r"(?P<length>[0-9]+) [^:]+:(?P<fingerprint>\S+) .* \((?P<type>[^\)]+)\)$"


class CODSSHPrivateKeys:

    def __init__(self) -> None:

        self.keys = {}

        default_keyfiles = [
            "id_dsa",
            "id_ecdsa",
            "id_ed25519",
            "id_rsa"
        ]

        fingerprint_hash = "md5"

        for keyfile_basename in default_keyfiles:
            keyfile = os.path.expanduser(f"~/.ssh/{keyfile_basename}")
            self._add_key_to_dict(keyfile, fingerprint_hash)

        agent_keys = self._get_ssh_agent_keys(fingerprint_hash)
        if agent_keys:
            self.keys.update(agent_keys)

    def fingerprint_exists(self, check_fingerprint: str) -> bool:
        return check_fingerprint in self.keys

    def _add_key_to_dict(self, keyfile: str, fingerprint_hash: str) -> None:
        if os.path.exists(keyfile):
            ssh_keygen_output = _run_ssh_keygen(keyfile, fingerprint_hash)

            if ssh_keygen_output:
                key_length, key_fingerprint, key_type = ssh_keygen_output
                self.keys[key_fingerprint] = {
                    "type": key_type,
                    "length": int(key_length)
                }

    @staticmethod
    def _get_ssh_agent_keys(fingerprint_hash: str) -> dict[str, Any] | None:
        if "SSH_AUTH_SOCK" not in os.environ:
            return None

        ssh_agent_keys = {}

        ssh_add_proc = subprocess.Popen(["ssh-add", "-E", fingerprint_hash, "-l"],
                                        stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        stdout, stderr = ssh_add_proc.communicate()
        if stdout:
            lines = stdout.decode("utf-8").split("\n")
            for line in lines:
                ssh_add_match = re.match(SSH_KEYGEN_REGEX, line)
                if ssh_add_match:
                    key_length = ssh_add_match.group("length")
                    key_fingerprint = ssh_add_match.group("fingerprint")
                    key_type = ssh_add_match.group("type")
                    ssh_agent_keys[key_fingerprint] = {
                        "type": key_type,
                        "length": int(key_length)
                    }

        return ssh_agent_keys


class CODSSHPubKey:

    def __init__(self, keyfile: str, fingerprint: str = "sha256") -> None:

        self.ssh_keygen_success = False
        self.key_length = None
        self.key_fingerprint = None
        self.key_type = None

        ssh_keygen_output = _run_ssh_keygen(keyfile, fingerprint)

        if ssh_keygen_output:
            self.ssh_keygen_success = True
            self.key_length, self.key_fingerprint, self.key_type = ssh_keygen_output

    def is_valid(self) -> bool:
        return self.ssh_keygen_success


def _run_ssh_keygen(keyfile: str, fingerprint: str) -> tuple[int, str, str] | None:
    ssh_keygen_proc = subprocess.Popen(["ssh-keygen", "-E", fingerprint, "-l", "-f", keyfile],
                                       stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    stdout, stderr = ssh_keygen_proc.communicate()
    if stdout:
        ssh_keygen_match = re.match(SSH_KEYGEN_REGEX, stdout.decode("utf-8"))
        if ssh_keygen_match:
            key_length = ssh_keygen_match.group("length")
            key_fingerprint = ssh_keygen_match.group("fingerprint")
            key_type = ssh_keygen_match.group("type")
            return int(key_length), key_fingerprint, key_type

    return None


def validate_ssh_pub_key(parameter: Parameter, configuration: ConfigurationView,
                         allowed_types: dict[str, int] | None = None) -> None:
    keyfile = configuration[parameter.key]

    if not keyfile:
        return

    if not os.path.exists(keyfile):
        raise CODException(f"SSH key file {keyfile} does not exist")

    pubkey = CODSSHPubKey(keyfile)

    if not pubkey.is_valid():
        raise CODException(f"SSH key file {keyfile} is not a valid key file")

    if allowed_types and (pubkey.key_type not in allowed_types
                          or pubkey.key_length is not None and pubkey.key_length < allowed_types[pubkey.key_type]):
        allowed_types_list = [f"{key}:{key_type or 'any'}" for key, key_type in allowed_types.items()]
        raise CODException(
            "SSH key file {} is of type {} and bitsize {}, "
            "permitted types and minimum bitsize are {}".format(
                keyfile,
                pubkey.key_type,
                pubkey.key_length,
                ", ".join(allowed_types_list),
            )
        )
