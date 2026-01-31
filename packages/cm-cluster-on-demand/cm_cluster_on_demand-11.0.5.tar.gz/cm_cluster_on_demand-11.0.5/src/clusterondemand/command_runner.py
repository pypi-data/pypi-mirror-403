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
import pdb
import string
import sys
from collections.abc import Iterable
from itertools import chain
from typing import Any, Callable

from clusterondemand import tracing
from clusterondemand.exceptions import CODException
from clusterondemandconfig import (
    UnknownCLIArgumentError,
    UnknownConfigFileParameterError,
    check_for_unknown_config_parameters,
    determine_invoked_command,
    explain_parameter,
    global_configuration,
    human_readable_config_dump,
    load_boot_configuration_for_command,
    load_configuration_for_command,
    print_help,
    print_help_for_positionals_missing_required_value,
    print_help_for_unknown_parameters,
    validate_configuration
)
from clusterondemandconfig.command_context import Command, CommandContext
from clusterondemandconfig.configuration import CommandConfiguration, ConfigurationView
from clusterondemandconfig.exceptions import ConfigLoadError
from clusterondemandconfig.parameter import Parameter
from clusterondemandconfig.testutils import sys_argv

from . import accept_eula
from .configuration import get_enforcing_config_files, get_system_config_files
from .import_utils import load_module_attribute
from .setup_logging import setup_logging, temporarily_logging_all_statements_to_syslog
from .utils import setup_signal_handlers
from .version import print_version_info

log = logging.getLogger("cluster-on-demand")


def run_invoked_command(
        command_context: CommandContext,
        pre_run_check: Callable[[Command, CommandConfiguration], Any] | None = None,
        additional_included_config_files: list[str] | None = None,
        additional_system_config_files: list[str] | None = None) -> None:
    """Pass the control to the appropriate tool, specified in 'name' argument.

    Handles the exception, and stack trace printing
    """
    setup_logging()

    with temporarily_logging_all_statements_to_syslog(log):
        log.debug(" ".join(sys.argv))

    non_ascii_chars_used = _check_for_non_ascii_chars_in_arguments()

    # FIXME: clusterondemandconfig doesn't allow us to have this in a clean way
    if "--version" in sys.argv and len(sys.argv) == 2:
        print_version_info()
        sys.exit(0)

    system_config_files = get_system_config_files(additional_included_config_files, additional_system_config_files)
    enforcing_config_files = get_enforcing_config_files()
    (command, clean_sys_argv) = determine_invoked_command(command_context)
    assert command
    try:
        configuration = None

        with sys_argv(clean_sys_argv):
            boot_configuration = load_boot_configuration_for_command(command)

            with global_configuration(boot_configuration):
                configuration = load_configuration_for_command(
                    command, system_config_files=system_config_files, enforcing_config_files=enforcing_config_files
                )
                if configuration["check_config"]:
                    _check_for_unknown_config_parameters(configuration,
                                                         system_config_files=system_config_files,
                                                         enforcing_config_files=enforcing_config_files,
                                                         parameters=command.parameters)

    except UnknownCLIArgumentError as e:
        print_help_for_unknown_parameters(command, e.flags)
        sys.exit(1)
    except CODException as e:
        if configuration:
            _log_cod_exception(e, configuration)
        else:
            _log_cod_exception(e, {"print_stack_trace_on_failure": True})  # use a mock config if config can't be loaded
        sys.exit(1)

    try:
        if non_ascii_chars_used and configuration["only_ascii_arguments"]:
            raise CODException(
                "Aborting because of a non-ASCII character in an argument. You can use "
                "'--no-only-ascii-arguments' to ignore this error."
            )

        if configuration["help"] or configuration["advanced_help"]:
            print_help(command, configuration)
        elif configuration["explain"]:
            explain_parameter(command, command_context, configuration["explain"])
        elif configuration["show_configuration"]:
            print(human_readable_config_dump(configuration, show_secrets=configuration["show_secrets"]))  # type: ignore
        elif configuration.required_positionals_with_missing_values():
            print_help_for_positionals_missing_required_value(command, configuration)
            sys.exit(1)
        elif configuration["show_eula"]:
            accept_eula.show_eula()
        elif command.require_eula and not accept_eula.user_accepts_eula(configuration):
            sys.exit(1)
        else:
            try:
                validate_configuration(configuration)
                configuration.lock()
            except RuntimeError as e:
                print(e)
                sys.exit(1)
            if pre_run_check:
                pre_run_check(command, configuration)
            setup_signal_handlers(command)
            with global_configuration(configuration):
                command_name = command.group.name + " " + command.name
                with tracing.trace_events(command_name):
                    command.run_command()
    except KeyboardInterrupt as e:
        _print_error_stack_on_failure(e, configuration)
        sys.exit(1)
    except (ConfigLoadError, CODException) as e:
        _post_mortem(configuration)
        _log_cod_exception(e, configuration)
        # TODO If it's useful, CODException could contain the error code
        sys.exit(1)
    except Exception:
        _post_mortem(configuration)
        raise


def _check_for_non_ascii_chars_in_arguments() -> bool:
    found = False

    for arg in sys.argv:
        if not all(char in string.printable for char in arg):
            found = True
            log.warning("Argument '{argument}' contains a non-ASCII character. This might cause "
                        "unforeseen behavior.".format(argument=arg))

    return found


def _check_for_unknown_config_parameters(configuration: ConfigurationView, system_config_files: list[str],
                                         enforcing_config_files: list[str],
                                         parameters: Iterable[Parameter] | None = None) -> None:
    def load_module_parameters(module_name: str, commands_name: str) -> list[Parameter]:
        commands: CommandContext = load_module_attribute(module_name, commands_name)
        return [] if commands is None else commands.parameters()

    check_all_commands = configuration["check_config_for_all_commands"]
    if parameters is None or check_all_commands:
        aws_parameters = load_module_parameters("clusterondemandaws.cli", "aws_commands")
        azure_parameters = load_module_parameters("clusterondemandazure.cli", "azure_commands")
        openstack_parameters = load_module_parameters("clusterondemandopenstack.cli", "openstack_commands")
        oci_parameters = load_module_parameters("clusterondemandoci.cli", "oci_commands")
        forge_parameters = load_module_parameters("clusterondemandforge.cli", "forge_commands")
        gcp_parameters = load_module_parameters("clusterondemandgcp.cli", "gcp_commands")
        parameters = chain(aws_parameters, azure_parameters, openstack_parameters,
                           oci_parameters, forge_parameters, gcp_parameters)

    try:
        check_for_unknown_config_parameters(
            parameters,
            system_config_files=system_config_files,
            enforcing_config_files=enforcing_config_files,
            ignore_unknown_namespaces=not check_all_commands,
        )
    except UnknownConfigFileParameterError:
        raise CODException("Some configuration files have problems. Use --no-check-config"
                           " to disable this check.")


def _print_error_stack_on_failure(e: BaseException, configuration: ConfigurationView | dict[str, Any]) -> None:
    # Print the error stack on failure even if verbosity wasn't requested
    if configuration["print_stack_trace_on_failure"]:
        log.info(e, exc_info=True)
    else:
        log.debug(e, exc_info=True)


def _post_mortem(configuration: ConfigurationView) -> None:
    if configuration["pdb_on_error"]:
        pdb.post_mortem()


def _log_cod_exception(exception: Exception, config: ConfigurationView | dict[str, Any]) -> None:
    _print_error_stack_on_failure(exception, config)
    if isinstance(exception, CODException):
        log.debug("Caused by: %s \n %s", exception.caused_by, exception.caused_by_trace)
    log.error(str(exception))
