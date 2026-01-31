#!/usr/bin/env python
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

import argparse
import getpass
import logging
import logging.handlers
import os
import sys
from dataclasses import dataclass, replace
from logging import DEBUG, ERROR, INFO
from typing import Any


class CustomSyslogFormatter(logging.Formatter):
    """A formatter that can resolve %(user)s within the fmt string."""
    def __init__(self, *args: Any, **kwargs: Any) -> None:
        self.username = getpass.getuser()
        super().__init__(*args, **kwargs)

    def format(self, record: logging.LogRecord) -> str:
        record.user = self.username
        return super().format(record)


@dataclass
class LogConfig():
    level: int
    handler: type[logging.Handler]
    format_str: str
    short_time: bool
    formatter: type[logging.Formatter] = logging.Formatter


CONSOLE_0_CONFIG = LogConfig(
    level=INFO,
    handler=logging.StreamHandler,
    format_str="%(asctime)s: %(levelname)8s: %(message)s",
    short_time=True
)
CONSOLE_0_WITHOUT_TIME_CONFIG = replace(CONSOLE_0_CONFIG, format_str="%(levelname)8s: %(message)s")
CONSOLE_1_CONFIG = replace(CONSOLE_0_CONFIG, level=DEBUG)
CONSOLE_2_CONFIG = replace(
    CONSOLE_1_CONFIG,
    format_str="%(asctime)s: %(name)s: %(levelname)8s: %(message)s",
    short_time=False
)
CONSOLE_3_CONFIG = replace(
    CONSOLE_2_CONFIG,
    format_str="%(asctime)s: %(name)s: %(pathname)s:%(lineno)d: %(levelname)8s: %(message)s"
)

LOGFILE_CONFIG = replace(CONSOLE_3_CONFIG, handler=logging.FileHandler)

SYSLOG_CONFIG = LogConfig(
    level=DEBUG,
    handler=logging.handlers.SysLogHandler,
    formatter=CustomSyslogFormatter,
    format_str="cluster-on-demand[%(process)d][%(user)s] %(levelname)s: %(message)s",
    short_time=False
)

CONSOLE_ERROR_ONLY_CONFIG = LogConfig(
    level=ERROR,
    handler=logging.StreamHandler,
    format_str="%(asctime)s: %(name)s: %(levelname)8s: %(message)s",
    short_time=True
)


class temporarily_logging_all_statements_to_syslog:
    def __init__(self, logger: logging.Logger) -> None:
        self.logger = logger
        self.loggerAndOriginalLevel: list[tuple[logging.Handler | logging.Logger, int]] = []

    def __enter__(self) -> None:
        for handler in self.logger.handlers:
            self.loggerAndOriginalLevel.append((handler, handler.level))

            if isinstance(handler, logging.handlers.SysLogHandler):
                handler.setLevel(DEBUG)
            elif self.logger.level > handler.level:
                handler.setLevel(self.logger.level)

        self.loggerAndOriginalLevel.append((self.logger, self.logger.level))
        self.logger.setLevel(DEBUG)

    def __exit__(self, _type: Any, _value: Any, _traceback: Any) -> None:
        for (logger, level) in self.loggerAndOriginalLevel:
            logger.setLevel(level)


def setup_logging() -> None:
    """
    Configure the root and cluster-on-demand logger and their handlers.

    COD and all of its dependencies generate log messages. We split all of these generators into two categories:
    - cluster-on-demand, and (represented here by cod_logger)
    - everything else. (the root logger).
    These two are separated by disabling the (upwards) propagation of the cod logger and are configured separately.

    There are several log handlers:
     - console, the contents of which are shown directly to the user on stderr,
     - syslog, the destination of log lines depend on the system configuration, and
     - file (if configured on the CLI)

    The desired behavior is as summarized as follows:
     - errors from cod and its dependencies are always shown on the console.
     - the console handler shows only INFO from cluster-on-demand when verbosity is 0.
       for verbosity=1 it shows all DEBUG messages from cluster-on-demand,
       for verbosity=2 it shows all DEBUG messages from the entire program and all libraries,
       for verbosity=3 and up it adds filenames and line numbers to every logged line,
    - the syslog handler sends all DEBUG messages from cluster-on-demand,
    - the file handler, if set, is similar to the console handler with verbosity=3.
    """
    config = _parse_config()

    _setup_cod_logging(config)
    _setup_root_logging(config)


def _parse_config() -> argparse.Namespace:
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument("-v", action="count", dest="verbosity", default=0)
    parser.add_argument("--log-file", default=None)
    parser.add_argument("--log-omit-time", action="store_true")
    parsed, _ = parser.parse_known_args(sys.argv)

    if parsed.log_file is None and "COD_LOG_FILE" in os.environ:
        parsed.log_file = os.environ["COD_LOG_FILE"]
    if parsed.log_file:
        parsed.log_file = os.path.expanduser(parsed.log_file)
    if not parsed.log_omit_time and "COD_LOG_OMIT_TIME" in os.environ:
        parsed.log_omit_time = os.environ["COD_LOG_OMIT_TIME"].lower() in ["1", "true", "yes"]
    return parsed


def _setup_cod_logging(config: argparse.Namespace) -> None:
    """Affects the main cod logger."""
    cod_logger = logging.getLogger("cluster-on-demand")
    cod_logger.propagate = False

    cod_logger.setLevel(DEBUG)
    cod_logger.addHandler(_console_handler(verbosity=config.verbosity, omit_time=config.log_omit_time))
    cod_logger.addHandler(_handler_for_log_config(SYSLOG_CONFIG))

    if config.log_file:
        cod_logger.addHandler(_handler_for_log_config(LOGFILE_CONFIG, filename=config.log_file))


def _setup_root_logging(config: argparse.Namespace) -> None:
    """Affects logger used by libraries."""
    root_logger = logging.getLogger()

    if 2 <= config.verbosity or config.log_file:
        root_logger.setLevel(DEBUG)
    else:
        root_logger.setLevel(ERROR)

    if config.verbosity < 2:
        # From 3rd party libraries, only show errors unless -vv or -vvv
        root_logger.addHandler(_handler_for_log_config(CONSOLE_ERROR_ONLY_CONFIG))
    else:
        root_logger.addHandler(_console_handler(verbosity=config.verbosity, omit_time=False))

    if config.log_file:
        root_logger.addHandler(_handler_for_log_config(LOGFILE_CONFIG, filename=config.log_file))


def _console_handler(verbosity: int, omit_time: bool) -> logging.Handler:
    if 0 == verbosity:
        config = CONSOLE_0_WITHOUT_TIME_CONFIG if omit_time else CONSOLE_0_CONFIG
    elif 1 == verbosity:
        config = CONSOLE_1_CONFIG
    elif 2 == verbosity:
        config = CONSOLE_2_CONFIG
    else:
        config = CONSOLE_3_CONFIG
    return _handler_for_log_config(config)


def _handler_for_log_config(config: LogConfig, *handler_args: Any, **handler_kwargs: Any) -> logging.Handler:
    formatter_kwargs = {"datefmt": "%H:%M:%S"} if config.short_time else {}
    formatter = config.formatter(config.format_str, **formatter_kwargs)  # type: ignore

    handler: logging.Handler = config.handler(*handler_args, **handler_kwargs)
    handler.setFormatter(formatter)
    handler.setLevel(config.level)
    return handler
