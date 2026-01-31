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

import json
import logging
import subprocess
from collections.abc import Sequence
from dataclasses import dataclass
from sys import argv as argv
from typing import Any

from clusterondemand.exceptions import CODException
from clusterondemand.setup_logging import setup_logging
from clusterondemand.ssh import SSHClient

log = logging.getLogger("cluster-on-demand")


@dataclass
class HTTPError(Exception):
    code: int

    def __str__(self) -> str:
        return f"HTTP error {self.code}"


class CallReturnedErrorMessageError(RuntimeError):
    pass


class CMClient:
    def __init__(self, ssh: SSHClient, timeout: int = 120):
        self._ssh = ssh
        self._timeout = timeout
        self._need_uuid: bool | None = None

    @property
    def need_uuid(self) -> bool | None:
        if self._need_uuid is None:
            try:
                self._need_uuid = bool(self.call("cmmain", "need_uuid", silent=True))
                log.debug("Determined need for UUID via RPC, needed: %d", self._need_uuid)
            except Exception as e:
                log.debug("Failed to determine need for UUID via RPC (error: %s), assume not needed", e)
                self._need_uuid = False
        return self._need_uuid

    @property
    def entity_unique_field_name(self) -> str:
        if self.need_uuid:
            return "uuid"
        return "uniqueKey"

    @property
    def ref_device_field_name(self) -> str:
        if self.need_uuid:
            return "ref_device_uuid"
        return "refDeviceUniqueKey"

    def _request(self, path: str, data: str | None = None, timeout: int | None = None) -> bytes:
        # The HTTP code is appended to stdout using printf format specifier "%03ld".
        args = [
            "curl", "-q",
            "--cert", "/root/.cm/admin.pem", "--key", "/root/.cm/admin.key", "--insecure",
            "--fail", "--show-error", "--silent", "--write-out", "%{http_code}",
        ]
        if data is not None:
            args.extend(["--data-binary", data])
        if timeout is not None:
            args.extend(["--max-time", str(timeout)])
        assert path.startswith("/")
        args.append("https://127.0.0.1:8081" + path)
        try:
            return self._ssh.check_output(args)[:-3]
        except subprocess.CalledProcessError as e:
            if stderr := e.stderr.decode().strip():
                log.debug(stderr)
            if e.returncode == 22:
                # HTTP page not retrieved. The requested url was not found or returned another error
                # with the HTTP error code being 400 or above.
                # This return code only appears if -f, --fail is used.
                raise HTTPError(code=int(e.stdout[-3:]))
            raise e

    def ready(self, timeout: int | None = None, services: Sequence[str] | None = None) -> bool:
        """
        Check if cmdaemon is "ready".

        Older cmdaemon versions support this feature and some not. (See: CM-20007)
        If supported it will return a proper True/False status

        If not supported, True is return (i.e. We assume it's ready)

        :param timeout: [optional] Overried the timeout set in the constructor
        :param services: [optional] The list of cmdaemon services to be ready
        """
        ready = True
        detected_ready_state = False

        if timeout is None:
            timeout = self._timeout

        ready_service_url = "/ready"
        ready_version_query_url = ready_service_url + "?version=query"

        # The list of services fetched by `wget -qO- http://master:8080/ready?all=yes`
        # We use static set, because after cmd was just initialized, the output list is incomplete.
        known_services = {"AutomaticFSExport", "CephConfiguratorMaster", "ConfigDumper", "GPUToolsAMD",
                          "GPUToolsDCGM", "KubernetesNodeStatusObserver", "NodeHierarchyConfiguration",
                          "ProxyService", "RamdiskService", "ResourcePoolManagerSlave", "SysConfigGenerator",
                          "SysConfigReader", "SysConfigWriter", "WLMRoleStateChange", "WlmServerCache",
                          "WlmServerInfo", "WlmSupervisorManager", "conman", "dhcpd", "mariadb", "named",
                          "nfs", "nslcd", "ntpd", "postfix", "shorewall", "shorewall6"}
        try:
            # Raises 404 for < 8.1 clusters
            ready_version = self._request(ready_version_query_url, timeout=timeout).decode()

            if ready_version == "ready" and services is not None:
                assert all(s in known_services for s in services)
                ready_service_url += "?" + "&".join(f"name={s}" for s in services)
            elif ready_version == "v2":
                ready_service_url += "?" + "name=cod"
            else:
                raise CODException(f"Unknown ready service version: '{ready_version}'")

            self._request(ready_service_url, timeout=timeout)
            detected_ready_state = True
        except HTTPError as e:
            log.debug(
                "HTTP connection to {address} returned code {code}".format(
                    address=ready_service_url,
                    code=e.code,
                )
            )

            # Older versions of cmdaemon do not offer the /ready endpoint, and the request for that
            # endpoint will fail with 404. In cases where we don't know which version of cmdaemon we
            # are working with, we will 404 to mean that the cluster is ready.
            # Only when we do know that cmdaemon should support the /ready endpoint do we consider
            # 200 to be an indication that cmdaemon is ready.
            if e.code == 404:
                log.debug("CMDaemon version is too old and does not support ready service endpoint")
                ready = True
                detected_ready_state = False
            elif e.code == 503:
                ready = False
                detected_ready_state = True
        except subprocess.CalledProcessError:
            ready = False
            detected_ready_state = True

        if not detected_ready_state:
            log.debug("Could not detect cmdaemon ready state. Assuming ready")

        return ready

    def ping(self) -> Any:
        return self.call("cmmain", "ping", silent=True)

    def call(self, service: str, method: str, args: list[Any] | None = None, silent: bool = False) -> Any:
        log.debug("CMDaemon call to %s::%s(%s)" % (service, method, args))
        request: dict[str, Any] = {"service": service, "call": method}
        if args:
            request["args"] = args
        try:
            data = self._request("/json", data=json.dumps(request), timeout=self._timeout)
            log.debug("CMDaemon call to %s::%s(%s) successfull" % (service, method, args))
            data = json.loads(data)
            if isinstance(data, dict) and "errormessage" in data:
                # Older versions of BCM, e.g. 7.0-dev, return HTTP 200 with JSON on error.
                raise CallReturnedErrorMessageError(data["errormessage"])
            return data
        except Exception:
            if silent:
                log.debug("CMDaemon call to %s::%s(%s) failed." % (service, method, args))
            else:
                log.error("CMDaemon call to %s::%s(%s) failed." % (service, method, args))
            raise

    def getComputeNodes(self) -> list[dict[str, Any]]:
        # TODO Implement some proper version handling
        # This hack is here temporarily for backwards compatibility.
        try:
            return self.call("cmdevice", "getComputeNodes", silent=True)  # type: ignore
        except HTTPError as e:
            if e.code == 400:
                log.debug("Couldn't find getComputeNodes. Using getSlaveNodes. Is this version < 8.2?")
                return self.call("cmdevice", "getSlaveNodes")  # type: ignore
            raise
        except CallReturnedErrorMessageError as e:
            if "Unknown cmdevice call specified" in str(e):
                log.debug("Couldn't find getComputeNodes. Using getSlaveNodes. Is this version <= 7.0?")
                return self.call("cmdevice", "getSlaveNodes")  # type: ignore
            raise

    def pshutdown(self, node_keys: list[str]) -> Any:
        # TODO Implement some proper version handling
        # This hack is here temporarily for backwards compatibility.
        RUN_PRE_HALT_OPERATIONS = True
        PRE_HALT_OPERATIONS_TIMEOUT = 300 * 1000  # from cmdaemon
        try:
            return self.call(
                "cmdevice", "pshutdown",
                [RUN_PRE_HALT_OPERATIONS, PRE_HALT_OPERATIONS_TIMEOUT, node_keys])
        except HTTPError as e:
            if e.code == 400:
                log.debug("pshutdown failed. Is this version < 9.1?")
                return self.call("cmdevice", "pshutdown", [node_keys])
            raise

    def getActiveAndPassiveHeadNode(self) -> dict[str, dict[str, Any]]:
        if self.need_uuid:
            active_head_node_key, passive_head_node_key, _ = self.call("cmmain", "getActivePassiveUuids")
        else:
            active_head_node_key, passive_head_node_key, _ = self.call("cmmain", "getActivePassiveKeys")
        results = {}
        head_nodes = self.call("cmdevice", "getHeadNodes")
        for head_node in head_nodes:
            if head_node[self.entity_unique_field_name] == active_head_node_key:
                results["active_head_node"] = head_node
            if head_node[self.entity_unique_field_name] == passive_head_node_key:
                results["passive_head_node"] = head_node
        return results

    def _runPowerOperation(self, operation: str, nodes: list[dict[str, Any]]) -> None:
        operation_object = {
            "baseType": "PowerOperation",
            "devices": [node[self.entity_unique_field_name] for node in nodes],
            "operation": operation
        }
        self.call("cmdevice", "powerOperation", [operation_object])

    def powerOnNodes(self, nodes: list[dict[str, Any]]) -> None:
        self._runPowerOperation("ON", nodes)

    def powerOffNodes(self, nodes: list[dict[str, Any]]) -> None:
        self._runPowerOperation("OFF", nodes)


if __name__ == "__main__":
    setup_logging()
    log.setLevel(logging.DEBUG)
    client = CMClient(SSHClient(argv[1]))
    if client.ping():
        print("ping ok")
    print(client.call("cmdevice", "getComputeNodes"))
