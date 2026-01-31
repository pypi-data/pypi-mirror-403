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

from clusterondemandconfig.configuration import ConfigurationView
from clusterondemandconfig.parameter import Parameter

from .exceptions import CODException


def localpath(string: str) -> str:
    """A parser for paths that exist on the local machine."""
    return os.path.expanduser(string)


def must_exist(parameter: Parameter, configuration: ConfigurationView) -> None:
    if configuration[parameter.key] and not os.path.isfile(configuration[parameter.key]):
        raise CODException(
            f"{parameter.key}={configuration[parameter.key]} does not exist"
        )


def must_be_readable(parameter: Parameter, configuration: ConfigurationView) -> None:
    if configuration[parameter.key] and not os.access(configuration[parameter.key], os.R_OK):
        raise CODException(
            f"{parameter.key}={configuration[parameter.key]} is not readable"
        )
