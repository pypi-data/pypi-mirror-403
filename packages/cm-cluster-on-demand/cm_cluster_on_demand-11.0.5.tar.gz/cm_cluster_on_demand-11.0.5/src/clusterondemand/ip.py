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

from typing import Any, Callable

import netaddr

from clusterondemandconfig.configuration import ConfigurationView
from clusterondemandconfig.parameter import OptionalParameter, Parameter

from .exceptions import CODException


def ip(string: str) -> netaddr.IPAddress:
    """A parser for ip strings."""
    try:
        ip_addr = netaddr.IPAddress(string)
        return ip_addr
    except netaddr.core.AddrFormatError:
        raise CODException("'%s' is not a valid IP" % (string))


def ip_must_be_within_cidr(cidr_name: str) -> Callable[[Parameter, ConfigurationView], None]:
    """Validation that raises an error when the IP value of the parameter is not contained within the CIDR"""
    def wrapper(parameter: Parameter, configuration: ConfigurationView) -> None:
        cidr_cfg = configuration.get_item_for_key(cidr_name).parameter

        assert isinstance(parameter, OptionalParameter)
        assert isinstance(cidr_cfg, OptionalParameter)

        ip_addr = configuration[parameter.key]
        cidr = configuration[cidr_cfg.key]

        if ip_addr is None:
            raise CODException("%s is not set" % (parameter.key))
        if cidr is None:
            raise CODException("%s is not set" % (cidr_cfg.key))

        if netaddr.IPAddress(ip_addr) not in netaddr.IPNetwork(cidr):
            raise CODException(
                "%s=%s not within %s=%s. Use %s and/or %s to change that." % (
                    parameter.key, ip_addr,
                    cidr_cfg.key, cidr,
                    cidr_cfg.default_flag, parameter.default_flag
                )
            )

    return wrapper


def nth_ip_in_default_network(nth: int, network: str) -> Callable[[Any, ConfigurationView], Any]:
    """Generate a dynamic default method for obtaining the nth ip address of a cidr parameter."""
    return lambda _, config: config[network][nth]
