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
from collections.abc import Iterable

from clusterondemand.exceptions import CODException
from clusterondemandconfig import ConfigNamespace, config

log = logging.getLogger("cluster-on-demand")


class InvalidDestinationFile(CODException):
    def __init__(self, copy_file_argument: str) -> None:
        super(CODException, self).__init__(
            "Destination path for argument '--copy-file {}' cannot refer to the user directory. "
            "Please write the absolute path.".format(copy_file_argument)
        )


def copy_file_parser(file_pair_str: str) -> list[str]:
    """
    Parse file pair.

    :param file_pair_str: A string of either colon separated src:dst paths or urls (only the source can be a URL),
     or one path acting as both src and dst
    :return: Parsed and processed file pairs
    """
    # This regex is used to avoid confusing the colon in a URL with the separator colon between src and dst
    file_pair = [
        path_name for path_name
        in re.split(r":(?!//)", file_pair_str)
    ]

    source_filepath = destination_filepath = file_pair[0]

    if len(file_pair) > 1:
        destination_filepath = file_pair[1]

    if os.path.expanduser(destination_filepath) != destination_filepath:
        raise InvalidDestinationFile(file_pair_str)

    return [os.path.expanduser(source_filepath), str(destination_filepath)]


def copy_file_serializer(value: Iterable[str]) -> str:
    return ":".join(value)


def copy_file_set_version(file_pairs: list[list[str]], cluster_version: str | None) -> list[list[str]]:
    """
    Parse file pair.

    :param file_pairs: A series of either colon separated src:dst paths,
     or one path acting as both src and dst
    :param cluster_version: Cluster version
    :return: Parsed and processed file pairs
    """
    processed_file_pairs = []

    for file_pair in file_pairs:
        file_pair = [
            path_name.format(COD_BRIGHT_VERSION=cluster_version) for path_name
            in file_pair
        ]

        processed_file_pairs.append(file_pair)
    return processed_file_pairs


def fill_env_variables(filename: str, full_text: str) -> str:
    """ Replaces placeholders with either values from the 'config'
    or from the environment.
    """
    env_vars_regex = r"\$\{[a-zA-Z0-9_]+\}"
    env_vars = re.findall(env_vars_regex, full_text)
    env_vars = list(set(env_vars))
    stripped_env_vars = [env[2:-1] for env in env_vars]

    for stripped_env_var, env_var_placeholder in zip(stripped_env_vars, env_vars):

        if stripped_env_var in config:
            source = "config"
            env_var_value = config[stripped_env_var]
        else:
            env_var_value = os.environ.get(stripped_env_var)
            source = "environment"

        if env_var_value:
            full_text = full_text.replace(env_var_placeholder, env_var_value)
            log.debug("Environment variable '%s' value filled in '%s' (from %s).", stripped_env_var, filename, source)
        else:
            log.warning("When processing files to be copied to the cluster, the environment"
                        " variable '%s' was not found. This entry was also not found in the runtime"
                        " configuration of COD. Therefore, the placeholder"
                        " in file to be uploaded '%s' to the cluster cannot be replaced"
                        " with the proper value.",
                        stripped_env_var, filename)
    return full_text


copyfile_ns = ConfigNamespace("cluster.copy")
copyfile_ns.add_enumeration_parameter(
    "copy_file",
    parser=copy_file_parser,
    serializer=copy_file_serializer,
    help_varname="SRC_PATH[:DST_PATH]  [SRC_PATH_2:[DST_PATH_2] ... ]",
    help=("Colon separated source path and destination path. If only the source path is specified, it will be used as"
          " the destination path. Note: -Using a tilde (~) will be expanded to the user home. "
          " Note: The source path can be an HTTP URL."
          " Note: The keyword {COD_BRIGHT_VERSION}, if present, will be replaced with the value of COD Bright Versions."
          " Example1: /etc/file.conf   Example2:  /home/user/custom-file.conf:/etc/file.conf    "
          " Example3:  http://localhost/path1:/destination/path1 /source/path2:/destination/path2 "))
copyfile_ns.add_enumeration_parameter(
    "copy_file_with_env",
    parser=copy_file_parser,
    serializer=copy_file_serializer,
    help=("Same as --copy-file but replaces instances of ${ENV_VAR} inside of the file being "
          "copied with the content of the environment variable 'ENV_VAR' as well as "
          "{COD_BRIGHT_VERSION} by the bright version in the file path."))
