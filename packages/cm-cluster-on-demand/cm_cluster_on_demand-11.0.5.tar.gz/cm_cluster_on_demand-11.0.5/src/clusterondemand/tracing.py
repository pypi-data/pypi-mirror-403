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

import getpass
import logging
import os
import socket
import sys
import time
import uuid
from collections.abc import Iterator
from contextlib import contextmanager
from functools import lru_cache
from typing import Any, Callable

import requests

import clusterondemand.utils as codutils
from clusterondemand import version
from clusterondemand.exceptions import CODException
from clusterondemandconfig import config

log = logging.getLogger("cluster-on-demand")


# set by "init_tracing"
_cod_command = None
_cod_argv = None


def init_tracing(cod_command: str, cod_argv: list[str]) -> None:
    """
    Initializes some global data which is later used by calls to send_event
    """
    global _cod_command, _cod_argv
    _cod_command = cod_command
    _cod_argv = cod_argv


class Timer:
    """
    Helper class for measuring elapsed time in various places of the code
    """
    def __init__(self) -> None:
        self._start_ts = time.time()
        self._stop_ts: float | None = None

    def restart(self) -> None:
        self._start_ts = time.time()
        self._stop_ts = None

    def get_elapsed(self) -> float:
        if self._stop_ts:
            until = self._stop_ts
        else:
            until = time.time()
        return round(until - self._start_ts, 2)

    def stop(self) -> float:
        if self._stop_ts:
            raise RuntimeError("Cannot stop stopped timer")
        self._stop_ts = time.time()

        return self.get_elapsed()


@lru_cache
def get_trace_id() -> str:
    """
    Returns a UUID which is unique across each execution runtime of COD.
    Can be used to correlate logs across different system
    """
    return str(uuid.uuid4())


def log_trace_id(log_destination: Callable[[str], Any] = log.info) -> None:
    """
    Logs the trace ID in a standard format
    """
    if "events" in config and config["events"]:
        log_destination("Trace ID: %s" % get_trace_id())


def send_event(name: str, **kwargs: Any) -> bool:
    """
    Sends a HTTP POST request to a specified URL.
    The request containes a json dictionary as payload, containing
    at least the "name" of the event (arbitrary string)
    """
    # This can happen upon e.g. import error, when
    # send_event is called from our exception handler
    if "events" not in config:
        log.debug("not sending event, 'events' not defined. Is global configuration defined?")
        return False

    if not config["events"]:
        return False

    if codutils.running_in_virtual_env():
        if not config["events_in_ve"]:
            log.debug("Not sending event, running in a virtual environment, use '--events-in-ve' to override.")
            return False

    data = _get_event_data(name, **kwargs)

    try:
        expected_status_code = 200
        response = requests.post(config["events_url"], json=data, timeout=config["events_timeout"])
        if response.status_code == expected_status_code:
            log.debug(response.text)
        else:
            raise requests.HTTPError(
                "Response status code was not %s, it was %s" % (expected_status_code, response.status_code),
                request=response.request,
                response=response,
            )
    except (requests.ConnectionError, requests.ReadTimeout, requests.HTTPError) as e:
        log.debug("Failed to submit event: %s" % e)

    return True


@contextmanager
def trace_events(command_name: str) -> Iterator[None]:
    try:
        # TODO: add cloud type (openstack, AWS, Azure)
        init_tracing(cod_command=command_name, cod_argv=sys.argv[:])
        log_trace_id(log_destination=log.debug)
        version_info = version.get_version_info()
        send_event(
            "Running " + command_name,
            cod_version=version_info["version"],
            cod_branch=version_info["branch"],
            cod_git_hash=version_info["git_hash"],
            cod_git_date=version_info["git_date"],
            build_date=version_info["build_date"])
        yield
    except CODException as e:
        send_event("CODException in " + command_name, error=str(e))
        log_trace_id(log_destination=log.error)
        raise
    except Exception as e:
        send_event("Unhandled Exception in " + command_name, error=str(e))
        log_trace_id(log_destination=log.error)
        raise


def _get_event_data(name: str, **kwargs: Any) -> dict[str, Any]:
    """
    Helper class of 'send_event'.
    Prepares data to be send by the event
    """
    assert _cod_command
    assert _cod_argv

    assert "type" not in kwargs.keys()
    assert "username" not in kwargs.keys()
    assert "hostname" not in kwargs.keys()
    assert "trace_id" not in kwargs.keys()
    assert "ve" not in kwargs.keys()

    kwargs["message"] = name
    kwargs["severity"] = "INFO"
    if "error" in kwargs.keys():
        kwargs["severity"] = "ERROR"

        # move error do details for consistency with other event sources in BCI
        kwargs["details"] = kwargs["error"]
        del kwargs["error"]

    kwargs["type"] = "COD"
    kwargs["username"] = getpass.getuser()
    kwargs["cod_client_hostname"] = socket.getfqdn()
    kwargs["trace_id"] = get_trace_id()
    if codutils.running_in_virtual_env():
        kwargs["ve"] = True

    kwargs["cod_command"] = _cod_command
    kwargs["cod_argv"] = str(_cod_argv)  # list rendered as a string, in case there's spaces in user provided args
    kwargs["cod_args"] = " ".join(_cod_argv)  # as a joined string, for easier copy-paste-and-use in most case

    inject_env_vars = ["OS_USERNAME", "OS_AUTH_URL", "OS_PROJECT_NAME", "COD_PREFIX", "CI_JOB_URL"]
    for env_var in inject_env_vars:
        if env_var in os.environ:
            kwargs[env_var] = os.environ[env_var]

    return kwargs
