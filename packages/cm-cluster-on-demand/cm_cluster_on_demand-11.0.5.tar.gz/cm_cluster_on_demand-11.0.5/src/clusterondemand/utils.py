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

import concurrent.futures
import getpass
import itertools
import logging
import os
import re
import signal
import socket
import string
import sys
import time
import traceback
from collections.abc import Iterable, Iterator
from datetime import datetime, timedelta, tzinfo
from subprocess import CalledProcessError, check_call
from typing import Any, Callable

import netaddr
import tenacity
import yaml
from dateutil.parser import parse
from dateutil.tz import tzlocal, tzutc
from requests import RequestException, get

from clusterondemand.exceptions import CODException, ValidationException
from clusterondemandconfig import ConfigNamespace, config
from clusterondemandconfig.command_context import Command

from .decorators import static_vars

log = logging.getLogger("cluster-on-demand")
tenaicty_log = logging.getLogger("tenacity")

DATE_TIME_FORMAT = "%m-%d %H:%M"
# RFC3280 defines maximum CN (common name) length = 64. However, we can't always use 64 as a cluster name, as there
# are cases when '-head-[a|b]', '.cm.cluster', etc. are appended to the headnode CN, leading to cert generation failure.
# Therefore, we introduce MAX_CLUSTER_NAME_LENGTH = 46, which accounts for such cases.
MAX_RFC3280_CN_LENGTH = 64
MAX_CLUSTER_NAME_LENGTH = 46

# reserved for SIGINT signal handler
MAX_DELAY_SECS = 2
_interrupts = 0
_last_seen = 0.0

UUID_RE = re.compile(r"^[\da-f]{8}-([\da-f]{4}-){3}[\da-f]{12}$", re.IGNORECASE)

UBUNTU_DEV_REPO = """
deb http://dev.bcm.nvidia.com/bright/apt/${repo_type}/$$(ARCH)/${bcm_version}/ubuntu/${ubuntu_version}/base/ ./
""".strip()

PUBLIC_IP_SERVICE_URL = "https://api.ipify.org"

confirm_ns = ConfigNamespace("confirm", "Confirm operations")
confirm_ns.add_switch_parameter(
    "yes",
    flags=["-y"],
    help="Do not ask for confirmation when executing operations"
)


def is_uuid(string: str) -> bool:
    return UUID_RE.match(string) is not None


def validate_arch_vs_machine_arch(arch: str | None, machine_arch: str | None, machine_type: str, node_type: str) -> str:
    """
    Validate that the machine type and selected architecture match.
    If no architecture is specified in the config, use the machine type's architecture.
    Returns the effective architecture.
    """
    # Validate that arch and machine_arch are either None or non-empty strings
    assert arch != ""
    assert machine_arch != ""

    match machine_arch, arch:
        case None, None:
            raise ValidationException(
                f"Machine architecture of {node_type} type '{machine_type}' unknown. "
                "Set the architecture via the --arch flag (e.g. --arch=x86_64)."
            )
        case None, _:
            log.warning(
                f"Machine architecture for {node_type} type {machine_type!r} is unknown. "
                f"Please ensure that arch={arch!r} is the correct architecture for "
                "this machine type, otherwise cluster creation might fail."
            )
        case _, None:
            log.info(
                f"No architecture specified in config, using {machine_arch!r} instead, "
                f"based on selected {node_type} type {machine_type!r}"
            )
        case _, _ if machine_arch != arch:
            raise ValidationException(
                f"Incompatible arch={arch} selected for {node_type} type {machine_type!r}, "
                f"which has arch={machine_arch}"
            )
    return arch or machine_arch  # type: ignore


def valid_cluster_name_regex() -> str:
    # Following RFC952 and RFC1123, a cluster name may only consist of alphabetic characters, digits
    # and dashes. It may not start or end with a dash. Additionally, we also don't allow cluster
    # names that consist of only digits.
    # (Note that all these restrictions are also enforced by cmdaemon.)
    only_digits_name = r"^[0-9]+$"
    single_char_name = r"[a-zA-Z]"
    multi_char_name = r"[a-zA-Z0-9][a-zA-Z0-9-]*[a-zA-Z0-9]"

    return r"(?!%s)^(%s|%s)$" % (only_digits_name, single_char_name, multi_char_name)


def is_valid_cluster_name(cluster_name: str | None, max_name_length: int) -> bool:
    return bool(
        cluster_name and
        len(cluster_name) <= max_name_length and
        re.match(valid_cluster_name_regex(), cluster_name)
    )


def is_valid_ip_address(ip: str | None) -> bool:
    try:
        netaddr.IPAddress(ip)
        return True
    except Exception:
        return False


def is_valid_positive_integer(num: Any) -> bool:
    try:
        if int(num) <= 0:
            return False
        return True
    except ValueError:
        return False


def is_writable_directory(fullpath: str) -> bool:
    return os.path.exists(fullpath) and os.path.isdir(fullpath) and os.access(fullpath, os.W_OK)


def format_timestamp(timestamp: float, format: str = DATE_TIME_FORMAT) -> str:
    """
    Format timestamp.

    :param date:   UNIX timestamp
    :param format:
    :return:       formatted local date/time
    """
    return datetime.fromtimestamp(timestamp).strftime(format)


def format_to_local_date_time(date: str, tz: tzinfo | None = None, format: str = DATE_TIME_FORMAT) -> str:
    """
    Format data to local date/time.

    :param date:   ISO 8601 date  (with or without timezone; no timezone means local time)
    :param tz: tzinfo (default: tzlocal())
    :param format:
    :return:       formatted local date/time
    """
    d: datetime = parse(date)
    tz = tz or tzlocal()
    if d.tzinfo is not None:
        d = d.astimezone(tz)
    return d.strftime(format)


def get_time_ago_from_iso(date: str) -> str:
    """
    Return human readable version of how long 'date' was ago.

    :param date: ISO 8601 date  (with or without timezone; no timezone means local time)
    :return:  "1d 12h"    (human string time from now
    """
    d1 = parse(date)
    d2 = datetime.now(d1.tzinfo)

    return get_time_ago(d1, d2)


def get_time_ago(past: datetime, now: datetime | None = None) -> str:
    """Return human readable version of how long 'past' was ago."""
    N_SEC_PER_DAY = 60 * 60 * 24
    N_SEC_PER_HOUR = 60 * 60
    N_SEC_PER_MINUTE = 60

    now = now or datetime.now(past.tzinfo)
    delta = now - past

    seconds = delta.days * N_SEC_PER_DAY + delta.seconds
    days, seconds = divmod(seconds, N_SEC_PER_DAY)
    hours, seconds = divmod(seconds, N_SEC_PER_HOUR)
    minutes, seconds = divmod(seconds, N_SEC_PER_MINUTE)

    if hours == 23 and 30 < minutes:
        return "%dd 0h" % (days + 1)

    if days:
        return "%dd %dh" % (days, hours)

    if 30 < seconds:
        return "%dh %dm" % (hours, minutes + 1)

    return "%dh %dm" % (hours, minutes)


def setup_signal_handlers(command: Command) -> None:
    def sigint_signal_handler(*args: Any) -> None:
        global _interrupts
        global _last_seen

        log.debug("Caught SIGINT!")

        now = time.time()
        if now > _last_seen + MAX_DELAY_SECS:
            _interrupts = 0

        _last_seen = now
        _interrupts += 1
        if _interrupts == 1:
            log.info("\n\n\033[91mPress ctrl+c again, quickly, to abort\033[0m\n")

        elif _interrupts > 1:
            if command.name == "create":
                log.warning("Operation aborted by user (Ctrl+C). Some resources may have been created and could "
                            f"require clean up either by {command.group.cli_expression} delete, or manual cleanup "
                            "using cloud provider management tools.")
            log.info("Aborted by user (ctrl+c).")
            raise KeyboardInterrupt

    signal.signal(signal.SIGINT, sigint_signal_handler)


def confirm(message: str = "", accept_parameter: str = "yes") -> bool:
    if message:
        log.info(message)

    if config[accept_parameter]:
        log.debug(f"The option --{accept_parameter.replace('_', '-')} is set. Skipping confirmation...")
        return True

    while True:
        log.info("Proceed? [yes/no]")

        reply = input().lower()
        if reply == "no" or reply == "n":
            log.info("Aborted.")
            return False

        if reply == "yes" or reply == "y":
            return True

        log.info("Please type 'yes' or 'no'.")


def confirm_with_enter(message: str = "") -> None:
    if message:
        log.info(message)

    if config["yes"]:
        log.debug("The option --yes is set. Skipping confirmation...")
        return

    while True:
        try:
            log.info("Press ENTER to continue, ctrl+c to abort.")

            reply = input().lower()
            if reply != "" and reply != "q":
                log.info("ENTER to continue, ctrl+c (or type 'q') to abort.")
                continue

            if reply == "q":
                log.info("Aborted.")
                exit(1)
            else:
                return
        except KeyboardInterrupt:
            log.info("Aborted.")
            exit(1)


def confirm_cluster_creation(num_clusters: int = 1) -> None:
    if config["yes"]:
        log.debug("The option --yes is set. Skipping confirmation...")
        return

    while True:
        try:

            if num_clusters == 1:
                log.info("Press ENTER to continue and create the cluster.")
            else:
                log.info("Press ENTER to continue and create %s clusters." % num_clusters)

            log.info("Press ctrl+c (or type 'a') to abort. Type 'i' for more info.")

            reply = input().lower()
            if reply != "" and reply != "a" and reply != "i":
                continue

            if reply == "a":
                log.info("Aborted.")
                exit(1)
            elif reply == "i":
                log.info("")
                log.info('You can set "ask_to_confirm_cluster_creation: false" in the config file'
                         " to permanently disable this question.")
                log.info("Add '-y' to the command line to skip this question in the future.")
                log.info("")

            else:
                return
        except KeyboardInterrupt:
            log.info("Aborted.")
            exit(1)


def confirm_edge_creation() -> None:
    if config["yes"]:
        log.debug("The option --yes is set. Skipping confirmation...")
        return

    while True:
        try:
            log.info("Press ENTER to continue and create the edges.")
            log.info("Press ctrl+c (or type 'a') to abort. Type 'i' for more info.")

            reply = input().lower()
            if reply != "" and reply != "a" and reply != "i":
                continue

            if reply == "a":
                log.info("Aborted.")
                exit(1)

            elif reply == "i":
                log.info("")
                log.info('You can set "ask_to_confirm_edge_creation: false" in the config file'
                         " to permanently disable this question.")
                log.info("Add '-y' to the command line to skip this question in the future.")
                log.info("")

            else:
                return
        except KeyboardInterrupt:
            log.info("Aborted.")
            exit(1)


def wait_for_socket(ip: str, port: int, timeout: float, throw: bool = False) -> bool:
    @tenacity.retry(
        stop=tenacity.stop_after_delay(timeout),
        retry=tenacity.retry_if_exception_type(socket.error),
        wait=tenacity.wait_fixed(1),
        before_sleep=tenacity.before_sleep_log(tenaicty_log, logging.DEBUG),
        reraise=True,
    )
    def try_to_connect() -> None:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            sock.settimeout(1)
            sock.connect((ip, port))
        finally:
            sock.close()

    try:
        log.debug(f"Waiting for connection to {ip}:{port} to be opened, waiting for {timeout} seconds")
        try_to_connect()
        log.debug(f"Connection to {ip}:{port} was opened successfully")
        return True
    except socket.timeout as e:
        if throw:
            raise
        log.warning(str(e))
        return False


def to_yaml(value: Any) -> str:
    """
    Convert given value (usually a dict) to YAML, correctly handling multi-line strings.

    :param val:   Object to dump as YAML
    :return:      YAML string
    """
    # for some reason the yaml.dump() below doesn't play well
    # with dict's descendant classes
    if isinstance(value, dict) and type(value) is not dict:
        value = dict(value)

    class MultiLineStringDumper(yaml.Dumper):
        def __init__(self, stream: Any, **kwargs: Any) -> None:
            super(self.__class__, self).__init__(stream, **kwargs)
            self.__class__.add_representer(str, self._str_presenter)

        def ignore_aliases(self, data: Any) -> bool:
            # We don't want yaml aliases, they could be confusing to some people. (CM-12080)
            return True

        @staticmethod
        def _str_presenter(dumper: MultiLineStringDumper, data: str) -> yaml.Node:
            if len(data.splitlines()) > 1:  # check for multiline string
                return dumper.represent_scalar("tag:yaml.org,2002:str", data, style="|")
            return dumper.represent_scalar("tag:yaml.org,2002:str", data)

    result: str = yaml.dump(value, default_flow_style=False, Dumper=MultiLineStringDumper)
    return result


def cod_log(logger: logging.Logger, action: str, percentage: int) -> None:
    logger.info("## Progress: %s", percentage)
    logger.info("#### stage: %s""", action)


def get_package_type(bcm_distro: str) -> str:
    if bcm_distro.upper().startswith("CENTOS"):
        return "yum"

    if bcm_distro.upper().startswith("ROCKY"):
        return "yum"

    if bcm_distro.upper().startswith("ALMA"):
        return "yum"

    if bcm_distro.upper().startswith("SLES"):
        return "zypper"

    if bcm_distro.upper().startswith("SL"):  # This has to come after SLES
        return "yum"

    if bcm_distro.upper().startswith("RHEL"):
        return "yum"

    if bcm_distro.upper().startswith("UBUNTU"):
        return "apt"

    raise KeyError("Unknown distro %s" % bcm_distro)


def enumerate_repo_config_files(bcm_distro: str, root_dir: str = "/", suffix: str = "", sles_suffix: str = "",
                                prefix_root_dir: bool = True) -> Iterator[str]:
    if not sles_suffix:
        sles_suffix = suffix
    os_repo_config_mapping = {
        "yum": [
            f"etc/yum.repos.d/cm{suffix}.repo"
        ],
        "zypper": [
            f"etc/zypp/repos.d/Cluster_Manager{sles_suffix}_Updates.repo"
        ],
        "apt": [
            f"etc/apt/sources.list.d/cm{suffix}.list"
        ]
    }

    if prefix_root_dir:
        prefix_dir = root_dir
    else:
        prefix_dir = "/"

    software_images = [
        os.path.join(prefix_dir, "cm/images", elem) for elem in
        os.listdir(os.path.join(root_dir, "cm/images"))
    ]
    node_installer = [os.path.join(prefix_dir, "cm/node-installer")]
    root_paths = [prefix_dir] + software_images + node_installer

    package_type = get_package_type(bcm_distro)
    repo_files = os_repo_config_mapping[package_type]

    for root_path in root_paths:
        for repo_file in repo_files:
            config_file = os.path.join(root_path, repo_file)
            yield config_file


@static_vars(escape_slash_re=re.compile(r"([^\\])\/"))
def sed_file_inplace(path: str, old: str, new: str, plain_text: bool = False) -> None:
    def escape_all_slashes(s: str) -> str:
        while True:
            s, count = sed_file_inplace.escape_slash_re.subn(r"\1\/", s)  # type: ignore
            if count == 0:
                return s

    if plain_text:
        old = re.escape(old)
        new = re.escape(new)

    try:
        old = escape_all_slashes(old)
        new = escape_all_slashes(new)
        expression = "s/%s/%s/g" % (old, new)
        check_call(["sed", "-i", "-E", expression, path])
    except CalledProcessError as e:
        log.warning(str(e))
        raise


def _define_dev_repository(repo: str, repo_type: str, bcm_distro: str, bcm_version: str) -> None:

    major_version, _ = _extract_bcm_version(bcm_version)

    if bcm_distro.lower().startswith("ubuntu"):

        # The regex below is expecting it in lowercase
        bcm_distro = bcm_distro.lower()
        # The regex below is expecting ubuntu1604 instead of ubuntu16.04
        bcm_distro = bcm_distro.replace(".", "")
        # Retrieve distro/version path from distro string (e.g., ubuntu1604 -> ubuntu/1604)
        match = re.match(r"([a-z]+)([0-9]+)", bcm_distro, re.I)
        assert match
        ubuntu_version = match.groups()[1]

        # Comment out all updates-*.brightcomputing.com repo lines
        sed_file_inplace(
            repo,
            "^(deb http://([^@]+@)?updates[^.]*.brightcomputing.com)",
            "# \\1"
        )
        dev_repo_line = string.Template(UBUNTU_DEV_REPO).substitute(
            repo_type=repo_type,
            bcm_version=major_version,
            ubuntu_version=ubuntu_version,
        )
        with open(repo, "r+") as repo_file:
            if not any([line.strip() == dev_repo_line for line in repo_file.readlines()]):
                repo_file.write("\n" + dev_repo_line)
    else:
        sed_file_inplace(repo, major_version, bcm_version, plain_text=True)


def _extract_bcm_version(bcm_version: str) -> tuple[str, ...]:
    pattern = r"(.*(?=\-))(.*)"

    try:
        match = re.match(pattern, bcm_version)
        if not match:
            raise AttributeError
        return match.groups()
    except AttributeError:
        log.error(
            "Failed to extract version from BCM version '%s'" % bcm_version
        )
        raise


def define_dev_repositories(bcm_distro: str, bcm_version: str, root_dir: str) -> None:
    try:
        cm_repos = enumerate_repo_config_files(bcm_distro, root_dir)
        ml_repos = enumerate_repo_config_files(bcm_distro, root_dir, suffix="-ml", sles_suffix="_ML")
        ni_repos = enumerate_repo_config_files(bcm_distro, root_dir, suffix="-ni", sles_suffix="_NI")
    except KeyError:
        log.warning(
            "Not changing repository configuration files for unknown distro '%s'" % (bcm_distro, )
        )

    for repo, repo_type in itertools.chain(
        zip(cm_repos, itertools.repeat("cm")),
        zip(ml_repos, itertools.repeat("ml")),
        zip(ni_repos, itertools.repeat("ni"))
    ):
        if not os.path.isfile(repo):
            log.debug("Skipping '%s', does not exist" % (repo, ))
            continue
        log.debug("Enabling %s repository in '%s'" % (bcm_version, repo))
        _define_dev_repository(repo, repo_type, bcm_distro, bcm_version)


def get_user_at_fqdn_hostname() -> str:
    return "{user}@{host}".format(
        user=getpass.getuser(),
        host=socket.getfqdn()
    )


class MultithreadRunError():
    """Used by multithread_run to indicate error."""
    def __init__(self, traceback: str, exception: BaseException):
        self.traceback = traceback
        self.exception = exception


def _multithread_wrapper(function: Callable[..., Any], args: Any) -> Any:
    try:
        if not isinstance(args, tuple):
            args = (args,)
        return function(*args)
    except Exception as e:
        return MultithreadRunError(traceback.format_exc(), e)


def multithread_iter(function: Callable[..., Any],
                     args_list: Iterable[Any],
                     max_threads: int | None,
                     reraise: bool) -> Iterator[Any]:
    """Runs a function multiple times in different threads and waits for them.

    For each tuple in 'args_list', a new thread will be created to run function(*args_list[i]) with a maximum
    of 'max_threads' in parallel.

    The most common use case is to run the same function with different arguments. But It's possible to run
    different functions by passing them in the 'args_list' and setting a dummy function in 'function':
    multithread_iter(lambda f: f(), [func1, func2])
    """
    with concurrent.futures.ThreadPoolExecutor(max_workers=max_threads) as executor:
        # We yield the results with futures.as_completed. Therefore, results order can be different from the input args
        # order. To maintain a link between argument and its result, we return a tuple (args, result)
        futures = [executor.submit(lambda *args: (args[1], _multithread_wrapper(*args)), *(function, args))
                   for args in args_list]
        for future in concurrent.futures.as_completed(futures):
            result = future.result()
            if reraise:
                _detect_multithreading_error([result[1]])
            yield result


def multithread_run(function: Callable[..., Any],
                    args_list: Iterable[Any],
                    max_threads: int | None,
                    reraise: bool = True) -> list[Any]:
    """
    Similar to multithread_iter, but it returns the results after all threads are completed.
    Returned results retain the original argument order.
    Needed mostly for backwards compatibility as many unit tests rely on the order of the threaded output
    """
    with concurrent.futures.ThreadPoolExecutor(max_workers=max_threads) as executor:
        futures = [executor.submit(_multithread_wrapper, *(function, args)) for args in args_list]
        results = [future.result() for future in futures]
        if reraise:
            _detect_multithreading_error(results)
        return results


def _detect_multithreading_error(results: list[Any]) -> None:
    error = next((result for result in results if isinstance(result, MultithreadRunError)), None)
    if error is not None:
        log.error(error.traceback)
        raise error.exception


def running_in_virtual_env() -> bool:
    if "VIRTUAL_ENV" in os.environ:
        return True
    return False


def partition(func: Callable[..., Any], iterable: Iterable[Any]) -> tuple[list[Any], list[str]]:
    true_items = []
    false_items = []
    for item in iterable:
        if func(item):
            true_items.append(item)
        else:
            false_items.append(item)
    return true_items, false_items


def resolve_hostname(hostname: str, retries: int = 4, retry_delay_sec: float = 0.2) -> str:
    ip = None
    while True:
        try:
            ip = socket.gethostbyname(hostname)
            log.debug(f"Successfully resolved '{hostname}' to '{ip}'.")
            break
        except OSError as e:
            log.debug(f"Failed to resolve hostname '{hostname}' to an IP. Reason: {e}")
            if retries > 0:
                log.debug(f"... Retry in {retry_delay_sec} seconds.")
                retries -= 1
                time.sleep(retry_delay_sec)
            else:
                raise CODException(f"Failed to resolve hostname '{hostname}' to an IP address.")
    return ip


def resolve_hostnames(hostnames: list[str]) -> dict[str, str]:
    return {name: resolve_hostname(name) for name in hostnames}


def get_commands_to_inject_resolved_hostnames(roots: list[str], resolved_hostname_ips: dict[str, str]) -> list[str]:
    commands = []

    for root in roots:
        if root == "/":
            root = ""
        commands += [f"echo '# This section was added by cod-os' >> {root}/etc/hosts"]
        for hostname, ip in resolved_hostname_ips.items():
            commands += [f"echo '{ip}                     {hostname}' >> {root}/etc/hosts"]
        commands += [f"echo '# The end of entries added by cod-os' >> {root}/etc/hosts"]
    return commands


def log_no_clusters_found(command_name: str) -> None:
    log.info(f"There were no eligible clusters to perform the '{command_name}' operation" +
             (f" with the arguments: {', '.join(config['filters'])}"
              if config.is_item_set_explicitly("filters") else ""))


def generate_timedelta(string: str) -> timedelta:
    regex = re.compile(r"((?P<days>\d+?)d)?((?P<hours>\d+?)h)?((?P<minutes>\d+?)m)?")
    match = regex.match(string.replace(" ", ""))
    assert match
    groups = match.groupdict()

    days = int(groups.get("days") or 0)
    hours = int(groups.get("hours") or 0)
    minutes = int(groups.get("minutes") or 0)
    delta = timedelta(days=days, hours=hours, minutes=minutes)

    return delta


def generate_older_than_date(delta: timedelta) -> datetime | None:
    if not delta:
        return None

    return (datetime.utcnow() - delta).replace(tzinfo=tzutc())


def report_progress(status: str, previous_status: str = "") -> str:
    """
    Report progress only if the progress is printed to a terminal.
    """
    if not sys.stderr.isatty():
        return ""

    if status != previous_status:
        sys.stderr.write("\r" + status)

    return status


def parse_assignment(s: str) -> tuple[str, str]:
    """
    :param s: a string representing an assignment, of the form key=value
    :return: a pair of k, v. k is a non-None string, v is allowed to be empty.
    """
    k, v = s.split("=", 1)  # allows '=' to show up in the value
    assert k, f"The string '{s}' is not a valid assignment in the form 'a=b'"
    return k, v


def get_public_ip_of_cod_client() -> str:
    try:
        log.debug(f"Getting public IP of the COD client from {PUBLIC_IP_SERVICE_URL}")
        ip = get(PUBLIC_IP_SERVICE_URL).content.decode('utf8')
    except RequestException as e:
        raise CODException(
            message=f"Failed to get public IP of the COD client from {PUBLIC_IP_SERVICE_URL}. ",
            caused_by=e
        )
    if not is_valid_ip_address(ip):
        raise CODException(
            f"Could not determine the public IP of the COD client. "
            f"String {ip} is not a valid IP address."
        )

    return ip
