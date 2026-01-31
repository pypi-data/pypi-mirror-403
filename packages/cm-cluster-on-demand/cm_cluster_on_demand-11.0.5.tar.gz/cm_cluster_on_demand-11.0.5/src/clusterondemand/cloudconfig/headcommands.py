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
import shlex
from typing import Any
from urllib.parse import urlparse

import netaddr
import requests
import yaml
from passlib.hash import sha512_crypt

from clusterondemand.clustercreate import enable_cmd_debug_commands, set_cmd_advanced_config_commands
from clusterondemand.exceptions import CODException
from clusterondemand.utils import get_commands_to_inject_resolved_hostnames, resolve_hostnames
from clusterondemandconfig import config

from .cloudconfig import CloudConfig, SignalHandler, SimpleSignalHandler
from .headfiles import CMD_READY_PROBE_PATH, add_common_head_files

log = logging.getLogger("cluster-on-demand")

DEFAULT_IMAGE_PATH = "/cm/images/default-image"


def add_head_node_commands(cloud_config: CloudConfig, internal_ip: str | None = None,
                           internal_interface: str = "eth0") -> None:
    """ Let's first signal the status wait condition that cloud init started """
    cloud_config.add_status_commands("cloud-init: Started.")

    encrypted_root_password = sha512_crypt.hash(config["cluster_password"])
    cloud_config.add_command(
        "echo %s | chpasswd -e" % shlex.quote("root:" + encrypted_root_password)
    )

    if internal_ip is not None:
        cloud_config.add_status_commands(f"cloud-init: Setting up {internal_interface}.")
        ip_net = netaddr.IPNetwork(str(config["internal_cidr"]))
        assert internal_ip in ip_net, "%s is not in subnet %s" % (internal_ip, ip_net)

        cloud_config.add_commands([
            "echo Set head node IP",
            f"ip link set up dev {internal_interface}",
            f"ip address flush dev {internal_interface}",
            f"ip addr add {internal_ip}/{ip_net.netmask} dev {internal_interface}",
        ])

        mtu = config["internal_mtu"]
        if mtu is not None:
            cloud_config.add_status_commands(f"cloud-init: Setting {internal_interface} custom mtu.")
            cloud_config.add_command(f"ip link set mtu {mtu} dev {internal_interface}")

    has_failover_network = config.get("ha") or config.get("create_ha_network_resources")
    # We always have at least one internal NIC and one external NIC. If failover networks are enabled (HA),
    # an additional NIC eth2 is added. Therefore, the NICs for additional internal networks start either with
    # eth2 or eth3
    extra_nic_idx = 3 if has_failover_network else 2
    for network_name, network_cidr in config.get("extra_network", []):
        cloud_config.add_status_commands(
            f"cloud-init: Setting up NIC eth{extra_nic_idx} for additional network {network_name}."
        )
        ip_address = network_cidr.network + network_cidr.hostmask - 1
        cloud_config.add_commands([
            f"echo Set head node IP for NIC eth{extra_nic_idx}",
            f"ip link set up dev eth{extra_nic_idx}",
            f"ip address flush dev eth{extra_nic_idx}",
            f"ip addr add {ip_address}/{network_cidr.netmask} dev eth{extra_nic_idx}",
        ])
        extra_nic_idx += 1

    if config["ssh_password_authentication"]:
        cloud_config.add_status_commands("cloud-init: Enabling password authentication.")
        cloud_config.add_commands([
            "echo 'COD-OS: SSH password authentication requested, editing sshd config file'",
            "sed -i 's/^PasswordAuthentication no/# Cluster on Demand: enabling due to "
            "ssh-password-authentication\\nPasswordAuthentication yes/g' /etc/ssh/sshd_config",
            "echo 'Reloading the sshd service'",
            "if ! systemctl try-reload-or-restart sshd; then",
            "  echo 'Old systemd, using different reload command.'",
            "  systemctl reload-or-try-restart sshd",
            "fi",
        ])

    cloud_config.add_commands(get_ssh_auth_key_commands())

    if config["append_to_root_bashrc"]:
        cloud_config.add_command("echo '# START of entries added by append_to_root_bashrc of Cluster on Demand' "
                                 ">> /root/.bashrc")
        for line in config["append_to_root_bashrc"]:
            cloud_config.add_command("echo '%s' >> /root/.bashrc" % line)
        cloud_config.add_command("echo '# END of entries added by append_to_root_bashrc of Cluster on Demand' "
                                 ">> /root/.bashrc")

    if config["cmd_debug"]:
        subsystems = config["cmd_debug_subsystems"]
        log.debug(f"Setting debug mode on CMDaemon for subsystems: '{subsystems}'")
        for command in enable_cmd_debug_commands(subsystems):
            cloud_config.add_command(command)

    # In this mode the CMD monitoring system will sample metric at randomized intervals
    # And it also says to CMD that hanged compute nodes must be reset
    log.debug("Setting VirtualCluster mode on CMDaemon")
    for command in set_cmd_advanced_config_commands(["VirtualCluster=1"]):
        cloud_config.add_command(command)


def get_ssh_auth_key_commands() -> list[str]:
    commands = []
    key_paths = config["authorized_key_path"].copy()  # make _shallow_ copy so we don't append to the org config
    if config["ssh_pub_key_path"]:
        key_paths.append(config["ssh_pub_key_path"])

    for auth_key in key_paths:
        parts = urlparse(auth_key)
        if all([parts.scheme, parts.netloc]):
            try:
                response = requests.get(auth_key)
                code = response.status_code
                if code != 200:
                    raise CODException(f"URL '{auth_key}' is unreachable ({code}), "
                                       "please make sure the provided URL is valid.")
                raw_content = response.text.rstrip()
            except requests.exceptions.RequestException as e:
                raise CODException(f"URL '{auth_key}' is unreachable, error: {e}")
        else:
            with open(auth_key) as file:
                raw_content = file.read().rstrip()

        commands.append(f"echo '{raw_content}' >> /root/.ssh/authorized_keys")
        if config["configure_default_image_authorized_keys"]:
            commands.append(f"echo '{raw_content}' >> {DEFAULT_IMAGE_PATH}/root/.ssh/authorized_keys")

    return commands


def add_run_bright_setup_commands(cloud_config: CloudConfig) -> None:
    # We have to load these modules so the command cm-bright-setup is available
    # Some older versions don't have the module cm-setup (it's all part of cluster-tools)
    # and would fail to load. That's why "|| true"
    cloud_config.add_commands([
        "echo Loading modules",
        "source /etc/profile.d/modules.sh",
        "module load cluster-tools",
        "module load cm-setup || true",
    ])

    if config["resolve_hostnames"]:
        # This can work around DNS issues by resolving hostnames during cluster creation
        commands = get_commands_to_inject_resolved_hostnames(
            ["/", "/cm/images/default-image"],
            resolve_hostnames(config["resolve_hostnames"]))
        for command in commands:
            cloud_config.add_command(command)

    if config["prebs"]:
        cloud_config.add_status_commands("cloud-init: Running prebs commands.")
        cloud_config.add_command("echo 'Starting custom prebs commands'")
        cloud_config.add_commands(config["prebs"])

    cloud_config.add_status_commands("cloud-init: Running cm-bright-setup.")
    cloud_config.add_command("cm-bright-setup -c /root/cm/cm-bright-setup.conf --on-error-action abort")
    cloud_config.add_status_commands("cloud-init: cm-bright-setup complete.")

    if config["postbs"]:
        cloud_config.add_status_commands("cloud-init: Running postbs commands.")
        cloud_config.add_command("echo 'Starting custom postbs commands'")
        cloud_config.add_commands(config["postbs"])


def add_wait_for_cmd_ready_commands(cloud_config: CloudConfig) -> None:
    cloud_config.add_status_commands("cloud-init: Waiting for CMDaemon to be ready.")
    cloud_config.add_command("chmod +x " + CMD_READY_PROBE_PATH)
    cloud_config.add_command(CMD_READY_PROBE_PATH)
    cloud_config.add_status_commands("cloud-init: CMDaemon is ready.")


def build_cloud_config(
    cm_bright_setup_conf: dict[str, Any],
    version: str,
    distro: str,
    internal_ip: str | None = None,
    signal_handler: SignalHandler | None = None,
    extra_prebs_commands: list[str] | None = None,
) -> CloudConfig:

    if signal_handler is None:
        signal_handler = SimpleSignalHandler("Head node")

    cloud_config = CloudConfig(signal_handler)
    add_common_head_files(cloud_config, version, distro)
    cloud_config.add_file("/root/cm/cm-bright-setup.conf", yaml.dump(cm_bright_setup_conf))
    add_head_node_commands(cloud_config, internal_ip)
    cloud_config.add_commands(extra_prebs_commands or [])
    if config["run_cm_bright_setup"]:
        add_run_bright_setup_commands(cloud_config)
        add_wait_for_cmd_ready_commands(cloud_config)
    cloud_config.add_config_complete_commands()

    return cloud_config
