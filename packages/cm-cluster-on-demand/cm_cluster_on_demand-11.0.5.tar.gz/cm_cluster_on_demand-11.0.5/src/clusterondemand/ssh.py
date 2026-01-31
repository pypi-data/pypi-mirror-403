#!/usr/bin/python
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
import os
import re
import shlex
import shutil
import subprocess
import tempfile
import textwrap
from dataclasses import dataclass
from io import TextIOWrapper
from typing import Any

from clusterondemand import localpath
from clusterondemand.codoutput.sortingutils import SSHAlias
from clusterondemand.contextmanagers import SmartLock
from clusterondemand.utils import (
    MAX_RFC3280_CN_LENGTH,
    is_valid_cluster_name,
    is_valid_ip_address,
    is_valid_positive_integer,
    is_writable_directory
)
from clusterondemandconfig import ConfigNamespace, config
from clusterondemandconfig.configuration_validation import must_be_nonnegative

clusterssh_ns = ConfigNamespace("cluster.ssh")

clusterssh_ns.add_parameter(
    "ssh_identity",
    advanced=True,
    default=None,
    help="Path to an ssh identity file key",
    help_varname="PATH_TO_FILE",
    parser=localpath.localpath,
    validation=[localpath.must_exist, localpath.must_be_readable]
)

clusterssh_ns.add_parameter(
    "ssh_password",
    advanced=True,
    default=None,
    help="SSH password to access the cluster",
    secret=True,
)

clusterssh_ns.add_parameter(
    "ssh_connect_timeout",
    advanced=True,
    default=30,
    help="Timeout for establishing an SSH connection with the cluster",
    validation=must_be_nonnegative,
)

clusterssh_ns.add_switch_parameter(
    "legacy_ssh_algo",
    advanced=True,
    help="Do not use rsa-sha2-512 and rsa-sha2-256 for SSH key verification",
)

log = logging.getLogger("cluster-on-demand")
tenacity_log = logging.getLogger("tenacity")


class SSHConfigManagerException(Exception):
    """SSH configuration manager specific exceptions base class."""
    pass


class MultipleCodTypesException(Exception):
    """"""
    pass


# ssh directives (cf. man ssh_config)
HOST_ = "Host "
HOSTNAME_ = "HostName "


class SSHConfigHostDescriptor:
    """
    :param host: the host name, must be a valid cluster name.
    :param index: the index used to build the alias.
    :param prefix: the prefix used to build the alias.
    :param ip: the host IP, must be a valid IPv4 address.
    """
    # Notice: this ctor does not perform any validation. This is intentional, the instance owner must
    # always check the `is_valid` property to decide whether the instance should be used or discarded.
    def __init__(self, host: str | None, index: int | None, prefix: str, ip: str | None) -> None:
        self._host = host
        self._index = index
        self._prefix = prefix
        self._ip = ip

    @property
    def is_valid(self) -> bool:
        return (is_valid_cluster_name(self.host, MAX_RFC3280_CN_LENGTH) and
                is_valid_ip_address(self.ip) and
                is_valid_positive_integer(self.index))

    @property
    def host(self) -> str | None:
        return self._host

    @property
    def index(self) -> int | None:
        return self._index

    @property
    def ip(self) -> str | None:
        return self._ip

    @property
    def alias(self) -> str:
        return "{prefix}{index}".format(
            prefix=self._prefix,
            index=self._index
        )

    @staticmethod
    def from_lines(lines: list[str], prefix: str) -> SSHConfigHostDescriptor:
        host, index, ip = (None, ) * 3
        try:
            for line in (li.strip() for li in lines):
                if line.startswith(HOST_):
                    line = line.replace(HOST_, "").strip()

                    tmp = line.split(" ")
                    host = tmp[0]
                    index = int(tmp[1].replace(prefix, ""))

                elif line.startswith(HOSTNAME_):
                    line = line.replace(HOSTNAME_, "").strip()
                    ip = line.split(" ")[0]
        except Exception:
            pass  # silence errors

        return SSHConfigHostDescriptor(host, index, prefix, ip)

    def __str__(self) -> str:
        return textwrap.dedent("""
        Host {host} {alias}
            HostName {ip}
            User root
            UserKnownHostsFile /dev/null
            StrictHostKeyChecking=no
            CheckHostIP=no
            LogLevel=error""".format(host=self.host, alias=self.alias, ip=self.ip))


class SSHConfigManager:
    """
    A helper class to manage cluster-related entries in local ssh_config file.

    :param cod_type: the type of cod clusters to be managed, i.e os or vmware.
    :param ssh_config: the path of the local ssh configuration file to use.
    :param prefix: the prefix used to build the cluster ssh aliases.
    :param parse: enable parsing the contents of the ssh_config file.
    :param mode: Either "match-hosts" or "replace-hosts". "match-hosts" preserves the contents of the
                 COD section or the ssh_config file; "replace-hosts" ignores currently defined hosts.
                 User-defined contents are always preserved.
    """
    def __init__(self, cod_type: str, ssh_config: str = "~/.ssh/config", prefix: str = "", parse: bool = True,
                 mode: str = "match-hosts") -> None:

        # params
        self._ssh_config = os.path.expanduser(ssh_config)
        self._prefix = prefix
        if mode not in ["match-hosts", "replace-hosts"]:
            raise SSHConfigManagerException("Programming error")
        self._mode = mode

        # internals
        self._begin_marker = f"#### BEGIN COD-{cod_type.upper()} SECTION"
        self._end_marker = f"#### END COD-{cod_type.upper()} SECTION"
        self._cod_type = cod_type
        self._hosts: list[SSHConfigHostDescriptor] = []
        self._cod_section: list[str] = []
        self._usr_section: list[str] = []

        self._parsed = False
        self._changed = False

        # disabling parsing of the local ssh config can be useful if the configuration is actually broken
        if parse:
            if not os.path.exists(self._ssh_config):
                # Non-existing config file is equivalent to empty config file
                log.warning("File '%s' was not found, continuing with an empty configuration.",
                            self._ssh_config)
                self._parsed = True
            else:
                try:
                    with open(self._ssh_config) as config:
                        self._parse_config(config)
                        self._parsed = True

                except OSError as ioe:
                    log.warning(str(ioe))

    @staticmethod
    def lock(ssh_config: str = "~/.ssh/config") -> Any:
        return SmartLock(os.path.expanduser(ssh_config) + ".lock")

    def _check_parsed(self) -> None:
        if not self._parsed:
            raise SSHConfigManagerException(
                "File '%s' not successfully parsed",
                self._ssh_config
            )

    @property
    def hosts(self) -> list[SSHConfigHostDescriptor]:
        """A list of host descriptors"""
        self._check_parsed()
        return self._hosts

    @property
    def user(self) -> list[str]:
        """Contents of the user section"""
        self._check_parsed()
        return self._usr_section

    def add_host(self, host: str, ip: str, override: bool = False) -> SSHConfigHostDescriptor:
        """
        Add a host descriptor to current configuration. Invalid descriptors are discarded.

        :param host: the hostname (string)
        :param ip: the host IPv4 or IPv6 address (string)
        :param override: (reserved for cluster create) if another host with the same name already exists, remove the
        the corresponding entry before adding this host. If override is False, trying to add an already existing host
        will raise an exception.

        :return: the host descriptor that has been added.
        """
        self._check_parsed()

        exists = next((h for h in self._hosts if h.host == host), None)
        if exists:
            if override:
                log.warning("Replacing local ssh config entry for host '%s'", host)
                self.remove_host(host)
            else:
                raise SSHConfigManagerException("A descriptor already exists for host '%s'" % host)

        next_index = max(h.index for h in self._hosts if h.index) + 1 if self._hosts else 1

        res = SSHConfigHostDescriptor(host, next_index, self._prefix, ip)
        self._safe_add_host_descriptor(res)

        return res

    def remove_host(self, host: str) -> None:
        """
        Remove a host descriptor from current configuration

        :param host: the hostname (string)
        """
        self._check_parsed()
        prev_hosts = self._hosts
        self._hosts = [h for h in prev_hosts if h.host != host]
        if self._hosts != prev_hosts:
            self._changed = True
        else:
            log.debug(
                "host descriptor for '%s' could not be found.", host)

    def write_configuration(self) -> None:
        """
        Write configuration to ssh config file.

        SSH clients give higher priority to entries towards the top of the config
        files. Therefore the COD section is put at the head of the local ssh config
        file. If no hosts are defined (i.e. no clusters), the section will be omitted.
        """
        msg = "cowardly refusing to write file '{ssh_config}'!".format(
            ssh_config=self._ssh_config
        )

        if not self._parsed:
            log.debug("%s (file was not parsed).", msg)
            return

        if not self._changed:
            log.debug("%s (no changes detected).", msg)
            return

        if not is_writable_directory(os.path.dirname(self._ssh_config)):
            log.debug("%s (directory is not writable).", msg)
            return

        assert self._parsed and self._changed
        log.debug("rewriting local ssh config file '%s' with %d COD %s.",
                  self._ssh_config, len(self._hosts),
                  "entry" if 1 == len(self._hosts) else "entries")

        try:
            # we go the extra mile of writing the new config to a temp file and only when we known
            # everything went smooth, we overwrite the pre-existing file by copying the new one onto it.

            with tempfile.NamedTemporaryFile(mode="wt") as fd:
                # Write COD section
                if self._hosts:
                    fd.write(self._begin_marker)
                    fd.write(textwrap.dedent(f"""
                    #### NOTICE: This section of the file is managed by cm-cod-{self._cod_type}. Manual changes to this section will be
                    #### overwritten next time cm-cod-{self._cod_type} cluster create, delete or list --update-ssh-config is executed."""))  # noqa

                    for descr in self._hosts:
                        # no point in keeping invalid entries here
                        if not descr.is_valid:
                            log.debug("Skipping invalid host descriptor for '%s'",
                                      descr.host or "?")
                            continue

                        fd.write(str(descr))
                        fd.write("\n")

                    fd.write(self._end_marker)
                    fd.write("\n")

                # Dump non-COD config as-is
                for line in self._usr_section:
                    fd.write(line)
                fd.flush()

                shutil.copy(fd.name, self._ssh_config)

                # issue warning if preservation of user contents semantics can not be guaranteed: we look for a
                # Host * directive, at the top of the ssh config file. If COD section exists and if this directive
                # can not be found, a warning is issued.
                if self._usr_section and self._hosts:
                    try:
                        if not re.match(r"%s\s+\*" % HOST_.lower().strip(),
                                        next(i for i in (i.strip() for i in self._usr_section if i.strip())
                                             if not i.startswith("#")).lower()):
                            log.warning(
                                "Possibly unsafe changes were made to '{config}'. To avoid this "
                                "warning, please add a 'Host *' directive right after the end of the "
                                "COD section.".format(
                                    config=self._ssh_config
                                ))
                    except StopIteration:
                        pass

        except OSError as ioe:
            log.warning("Could not write file '%s' (%s).", self._ssh_config, str(ioe))

    def get_host_index(self, host_name: str) -> int | None:
        try:
            return next(host.index for host in self._hosts if host.host == host_name)
        except StopIteration:
            raise SSHConfigManagerException(f"{host_name} not found in ssh config")

    def get_host_alias(self, host_name: str) -> SSHAlias:

        try:
            alias_string = next(host.alias for host in self._hosts if host.host == host_name)
            return SSHAlias(alias_string, self._prefix)
        except StopIteration:
            raise SSHConfigManagerException(f"{host_name} not found in ssh config")

    def _safe_add_host_descriptor(self, descriptor: SSHConfigHostDescriptor) -> None:
        """
        If a  valid descriptor is given, add it to the internal cache. Otherwise discard it.

        :param descriptor: An instance of class SSHConfigHostDescriptor
        """
        if descriptor.is_valid:
            self._hosts.append(descriptor)
            self._changed = True
            log.debug("added host descriptor for '%s'", descriptor.host)
        else:
            log.debug("discarding not well-formed descriptor for host '%s'",
                      descriptor.host or "?")

    def _parse_config(self, fd: TextIOWrapper) -> None:
        """
        Parse ssh config file.

        :param fd: An open file descriptor

        The ssh config file is logically divided in two sections: the COD section contains
        all host definitions for COD clusters, along with an alias than can be used with ssh
        -like tools, and the IP to reach the head-node and a few configuration options. It is
        enclosed between the begin and end markers; the other section (i.e. anything beyond
        the COD section) is reserved to the user and is preserved as-is.
        """
        if self._mode == "match-hosts":
            self._parse_config_aux(fd)

        elif self._mode == "replace-hosts":
            self._parse_config_aux(fd)
            log.debug("regenerating contents of {config}".format(
                config=self._ssh_config
            ))
            self._hosts = []
            self._changed = True

        else:
            assert False

    def _parse_config_aux(self, fd: TextIOWrapper) -> None:
        in_cod_section = False
        for line in fd:
            if line.startswith(self._begin_marker):
                if in_cod_section:
                    raise SSHConfigManagerException(
                        "Unexpected begin marker encountered")
                in_cod_section = True
                continue

            if line.startswith(self._end_marker):
                if not in_cod_section:
                    raise SSHConfigManagerException(
                        "Unexpected end marker encountered")
                in_cod_section = False
                continue

            if line.startswith("#### BEGIN") and not self._prefix:
                raise MultipleCodTypesException()

            if in_cod_section and line.startswith("####"):  # skip markers in COD section
                continue

            # every line goes either to the COD section or the user section
            section = self._cod_section if in_cod_section else self._usr_section
            section.append(line)

        # at EOF we're supposed to be out of the COD section
        if in_cod_section:
            raise SSHConfigManagerException(
                "Missing end marker detected")

        # This loop maintains in 'curr' a list of lines. We scan the entire file, line by line, accumulating
        # lines in 'curr'. Every time we encounter a Host declaration we want to process the accumulated lines.
        # Then, we reset the 'curr' list and continue. Once we've scanned the entire file, a few lines will
        # still be in curr. Those will be processed separately.
        curr: list[str] = []
        for line in self._cod_section:
            # "Match" is not supported within the COD section
            if line.startswith(HOST_):
                if curr:
                    descriptor = SSHConfigHostDescriptor.from_lines(lines=curr, prefix=self._prefix)
                    self._safe_add_host_descriptor(descriptor)
                    curr = []
            curr.append(line)

        # final wrap-up
        if curr:
            descriptor = SSHConfigHostDescriptor.from_lines(lines=curr, prefix=self._prefix)
            self._safe_add_host_descriptor(descriptor)
            curr = []

        assert not curr, "Unexpected"
        log.debug(
            "local ssh config file '%s' parsed, COD section holds %d %s.",
            self._ssh_config, len(self._hosts),
            "entry" if 1 == len(self._hosts) else "entries")


def private_key_for_public(public_key_path: str) -> str | None:
    if not public_key_path:
        return None

    name, ext = os.path.splitext(public_key_path)
    if os.path.exists(name) and ext:
        return name

    return None


@dataclass
class SSHClientError(Exception):
    result: subprocess.CompletedProcess[bytes]
    ssh_log: str

    def __str__(self) -> str:
        return f"SSH returned non-zero exit status {self.result.returncode}:\n{self.ssh_log}"


class SSHClient:
    def __init__(
        self,
        host: str,
        connect_timeout: int | None = None,
        identity_file: str | None = None,
        password: str | None = None,
        port: int | None = None,
        user: str | None = None,
    ) -> None:
        if connect_timeout is None:
            connect_timeout = config.get("ssh_connect_timeout")
        if identity_file is None:
            identity_file = config.get("ssh_identity")
        if identity_file is None:
            identity_file = private_key_for_public(config.get("ssh_pub_key_path"))
        if password is None:
            password = config.get("ssh_password")
        if password is None:
            password = config.get("cluster_password")

        self._host: str = host
        self._connect_timeout: int | None = connect_timeout
        self._identity_file: str | None = identity_file
        self._password: str | None = password
        self._port: int | None = port
        self._user: str = user if user is not None else "root"

    @property
    def host(self) -> str:
        return self._host

    @property
    def port(self) -> int | None:
        return self._port

    def check_call(self, args: str | list[str]) -> None:
        self._run(args, check=True)

    def check_output(self, args: str | list[str]) -> bytes:
        return self._run(args, stdout=subprocess.PIPE, check=True).stdout

    def _run(
        self, args: str | list[str], check: bool = False, **kwargs: Any
    ) -> subprocess.CompletedProcess[bytes]:
        with tempfile.TemporaryDirectory() as temp_dir:
            log_file: str = os.path.join(temp_dir, "ssh.log")

            ssh_args: list[str] = ["ssh", "-E", log_file]
            env: dict[str, str] = {}

            if ssh_auth_sock := os.environ.get("SSH_AUTH_SOCK"):
                env["SSH_AUTH_SOCK"] = ssh_auth_sock

            options: dict[str, str] = {
                "BatchMode": "yes" if self._password is None else "no",
                "PasswordAuthentication": "no" if self._password is None else "yes",
                "StrictHostKeyChecking": "no",
                "UserKnownHostsFile": "/dev/null",
            }
            if self._connect_timeout is not None:
                options["ConnectTimeout"] = str(self._connect_timeout)
                # Guess reasonable keepalive settings based on the connect timeout.
                if self._connect_timeout == 0:
                    server_alive_count_max = 0
                    server_alive_interval = 0
                elif self._connect_timeout <= 15:
                    server_alive_count_max = 3
                    server_alive_interval = 5
                else:
                    server_alive_count_max = 3
                    server_alive_interval = 10
                options["ServerAliveCountMax"] = str(server_alive_count_max)
                options["ServerAliveInterval"] = str(server_alive_interval)

            if self._password is not None:
                askpass: str = os.path.join(temp_dir, "askpass.sh")
                with open(
                    os.open(askpass, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, mode=0o700),
                    "w",
                ) as f:
                    f.write(f"#!/bin/sh\necho {shlex.quote(self._password)}")
                env["DISPLAY"] = ""
                env["SSH_ASKPASS"] = askpass
                env["SSH_ASKPASS_REQUIRE"] = "force"

            if self._identity_file is not None:
                ssh_args.extend(["-i", self._identity_file])

            for option, value in sorted(options.items()):
                ssh_args.extend(["-o", f"{option}={value}"])

            if self._port is not None:
                ssh_args.extend(["-p", str(self._port)])

            if self._user:
                ssh_args.append(f"{self._user}@{self._host}")
            else:
                ssh_args.append(self._host)

            ssh_args.append(args if isinstance(args, str) else shlex.join(args))

            log.debug(f"{shlex.join(ssh_args)}")

            result = subprocess.run(
                ssh_args,
                stderr=subprocess.PIPE,
                env=env,
                start_new_session=True,
                **kwargs,
            )
            log.debug(f"SSH returned exit status {result.returncode}")

            # SSH exits with the exit status of the remote command or with 255 if an error occurred.
            # BCM/COD reserve exit code 255 for SSH errors.
            if result.returncode == 255:
                try:
                    f = open(log_file, "r")
                except FileNotFoundError:
                    # SSH exited early before creating the log file. The error was printed to
                    # stderr.
                    raise SSHClientError(result=result, ssh_log=result.stderr.decode())
                else:
                    with f:
                        # SSH always logs on error. If the log is empty, assume the remote process
                        # exited with 255.
                        if ssh_log := _remove_known_hosts_warnings(f.read()):
                            raise SSHClientError(result=result, ssh_log=ssh_log)
            result.args = args
            if check:
                result.check_returncode()
            return result


# SSH warnings about known hosts are not relevant when UserKnownHostsFile=/dev/null.
def _remove_known_hosts_warnings(ssh_log: str) -> str:
    return "\n".join(
        line for line in ssh_log.splitlines() if not line.startswith("Warning: Permanently added ")
    )
