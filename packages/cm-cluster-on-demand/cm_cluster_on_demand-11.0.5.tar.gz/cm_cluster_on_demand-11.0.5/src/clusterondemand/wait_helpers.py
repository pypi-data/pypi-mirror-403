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

import ipaddress
import logging
import time
from collections.abc import Collection
from typing import Any

import tenacity

from clusterondemand.bcm_version import BcmVersion
from clusterondemand.const import BASIC_SERVICES
from clusterondemand.exceptions import CODException
from clusterondemand.ssh import SSHClient, SSHClientError
from clusterondemandconfig import ConfigNamespace
from clusterondemandconfig.configuration import ConfigurationView, MutableConfigurationView
from clusterondemandconfig.exceptions import ConfigLoadError

from .cmclient import CMClient

log = logging.getLogger("cluster-on-demand")
tenacity_log = logging.getLogger("tenacity")

clusterwaiters_ns = ConfigNamespace("cluster.waiters")
clusterwaiters_ns.add_parameter(
    "wait_ssh",
    default=300,
    help_varname="SECONDS",
    help="Wait up to that many seconds for SSH to come up"
)
clusterwaiters_ns.add_parameter(
    "wait_cmdaemon",
    default=900,
    help_varname="SECONDS",
    help="Wait up to that many seconds for CMDaemon to come up. "
         "Depends on --wait-ssh and is ignored when --wait-ssh is 0"
)
clusterwaiters_ns.add_switch_parameter(
    "start_nodes",
    default=False,
    help="Power on compute nodes after starting the cluster",
)
clusterwaiters_ns.add_parameter(
    "wait_for_nodes",
    default=0,
    help_varname="SECONDS",
    help=(
        "Wait up to that many seconds for the compute nodes to come up. "
        "Depends on --wait-ssh and --wait-cmdaemon and is ignored if either of them is 0"
    ),
)
clusterwaiters_ns.add_validation(lambda param, config: validate_waiters(config))


def wait_for_ssh(ssh: SSHClient, timeout: int) -> None:
    log.info(f"Waiting for sshd: {ssh.host} port {ssh.port} (timeout {timeout} seconds)")

    if ipaddress.ip_address(ssh.host).is_private:
        log.warning(
            f"The head node IP address {ssh.host} is private, it will not be reachable from the internet. "
            "Use --wait-ssh=0 to skip waiting for SSH."
        )

    @tenacity.retry(
        before_sleep=tenacity.before_sleep_log(tenacity_log, logging.DEBUG),
        reraise=True,
        retry=tenacity.retry_if_exception_type(SSHClientError),
        stop=tenacity.stop_after_delay(timeout),
        wait=tenacity.wait_fixed(5),
    )
    def wait_ssh() -> None:
        ssh.check_call("exit")

    wait_ssh()
    log.debug("SSH login OK")


def wait_for_cmdaemon(cmclient: CMClient, timeout: float) -> None:
    log.info(f"Waiting for CMDaemon (timeout {timeout} seconds)")

    @tenacity.retry(
        before_sleep=tenacity.before_sleep_log(tenacity_log, logging.DEBUG),
        reraise=True,
        retry=tenacity.retry_if_not_result(lambda ready: ready),
        stop=tenacity.stop_after_delay(timeout),
        wait=tenacity.wait_fixed(5),
    )
    def wait_ready() -> bool:
        return cmclient.ready(timeout=10, services=BASIC_SERVICES)

    try:
        wait_ready()
    except tenacity.RetryError:
        raise CODException("Timed out waiting for CMDaemon.")
    log.debug("CMDaemon ready")


def wait_for_compute_nodes(cmclient: CMClient, timeout: float,
                           node_names: Collection[str] | None = None) -> None:
    try:
        nodes = {n[cmclient.entity_unique_field_name]: n for n in cmclient.getComputeNodes()
                 if node_names is None or n["hostname"] in node_names}
    except Exception as e:
        raise Exception("Failed to get compute nodes" +
                        (f" {node_names} " if node_names else " ") +
                        "to wait for") from e

    if not nodes:
        log.debug("No compute nodes to wait for")
        return

    log.info(f"Waiting for compute nodes {[n['hostname'] for n in nodes.values()]} to start.")

    if BcmVersion(cmclient.call("cmmain", "getVersion")["cmVersion"]).release > (8, 2):
        log.debug("Using new device status API to wait for nodes.")
        api_service = "cmstatus"
        api_method = "getStatusForDevices"
    else:
        log.debug("Using old device status API to wait for nodes.")
        api_service = "cmdevice"
        api_method = "getStatusForDeviceArray"

    if cmclient.need_uuid:
        node_keys = list(nodes.keys())
    else:
        node_keys = [int(k) for k in nodes.keys()]

    remaining_nodes: list[dict[str, Any]] = list(nodes.values())
    end_time = time.time() + timeout
    while time.time() < end_time:
        log.debug("Fetching node status from CMDaemon.")
        statuses = cmclient.call(api_service, api_method, [node_keys])

        remaining_nodes = []
        stopped_nodes = []
        for status in statuses:
            node = nodes[status[cmclient.ref_device_field_name]]
            status_name = status["status"]
            log.debug(f"Node {node['hostname']} is {status_name}")
            if status_name != "UP":
                remaining_nodes.append(node)
            if status_name == "DOWN":
                stopped_nodes.append(node)

        if stopped_nodes:
            try:
                log.debug("Some compute nodes became DOWN during powering on, let's try to power"
                          " them on again...")
                cmclient.powerOnNodes(stopped_nodes)
            except Exception:
                log.debug("Failed while retrying power on, probably because previous power on "
                          " operation is still running", exc_info=True)

        if not remaining_nodes:
            break

        remaining_time = end_time - time.time()
        if remaining_time > 0:
            log.debug("Waiting for %d of %d nodes to start, %d:%02d min remaining...",
                      len(remaining_nodes), len(nodes), remaining_time // 60, remaining_time % 60)
            time.sleep(min(10, remaining_time))
    else:
        names = [n["hostname"] for n in remaining_nodes]
        raise CODException(f"Timed out while waiting for nodes {names} to start")


def wait_for_cluster(config: ConfigurationView, host: str) -> None:
    if (wait_ssh := config["wait_ssh"]) > 0:
        ssh = SSHClient(host, port=22)

        wait_for_ssh(ssh, timeout=wait_ssh)

        if (wait_cmdaemon := config["wait_cmdaemon"]) > 0:
            cmclient = CMClient(ssh)

            wait_for_cmdaemon(cmclient, timeout=wait_cmdaemon)

            if config["start_nodes"]:
                cmclient.powerOnNodes(cmclient.getComputeNodes())

                if (wait_for_nodes := config["wait_for_nodes"]) > 0:
                    wait_for_compute_nodes(cmclient, timeout=wait_for_nodes)


def validate_waiters(config: MutableConfigurationView) -> None:
    # Not all configuration parameters are used for all "cod" commands, but some of those commands still need waiters
    # Therefore, we  validate the values of various keys, only if those keys exist in configuration

    # While unlikely, technically run_cm_bright_setup=False may exist without "wait_cmdaemon" or "wait_for_nodes"
    # We won't fail the run if that's the case
    if not config.get("run_cm_bright_setup", True):
        if "wait_cmdaemon" in config and config["wait_cmdaemon"] > 0:
            log.warning(
                "--run-cm-bright-setup=no overrides --wait-cmdaemon value, setting to 0"
            )
            config["wait_cmdaemon"] = 0
        if "wait_for_nodes" in config and config["wait_for_nodes"] > 0:
            log.warning(
                "--run-cm-bright-setup=no overrides --wait-for-nodes value, setting to 0"
            )
            config["wait_for_nodes"] = 0

    if "wait_cmdaemon" in config:
        assert "wait_ssh" in config, "Parameter '--wait-cmdaemon' requires '--wait-ssh' to exist in configuration"

    if "wait_for_nodes" in config and config["wait_for_nodes"] > 0:
        # Edge create has wait_for_nodes but not wait_cmdaemon, as wait_cmdaemon waits for headnode cmd,
        # which is already up
        if "wait_cmdaemon" in config and config["wait_cmdaemon"] <= 0:
            raise ConfigLoadError(
                "Using '--wait-for-nodes' requires '--wait-cmdaemon' value to be > 0"
            )
        # For cluster start
        if "start_nodes" in config and not config["start_nodes"]:
            raise ConfigLoadError(
                "Using '--wait-for-nodes' requires '--start-nodes' value to be true"
            )
