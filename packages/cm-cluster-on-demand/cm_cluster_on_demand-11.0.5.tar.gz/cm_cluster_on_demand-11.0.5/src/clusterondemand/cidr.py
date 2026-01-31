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

from typing import Callable

import netaddr

from clusterondemand.inbound_traffic_rule import CLIENT_IP
from clusterondemand.utils import get_public_ip_of_cod_client
from clusterondemandconfig.configuration import ConfigurationView
from clusterondemandconfig.parameter import OptionalParameter, Parameter

from .exceptions import CODException


def cidr_list(cidrs_str: str) -> list[netaddr.IPNetwork]:
    """Parses a list of CIDRs or 'none' """
    if cidrs_str.lower() == "none":
        return []
    return [cidr(c.strip()) for c in cidrs_str.split(",")]


def nullable_cidr(string: str) -> netaddr.IPNetwork | None:
    """A parser for cidr strings which allows None values as well."""
    if string.lower() == "none":
        return None
    return cidr(string)


def cidr(string: str) -> netaddr.IPNetwork:
    """A parser for cidr strings."""
    try:
        if string == CLIENT_IP:
            string = get_public_ip_of_cod_client()
        network = netaddr.IPNetwork(string)
        if str(network.cidr) != str(network):
            raise CODException("'%s' is not a valid CIDR: the host section is not empty" % (string))
        return network
    except netaddr.core.AddrFormatError:
        raise CODException("'%s' is not a valid CIDR" % (string))


def must_be_within_cidr(parent_cidr_name: str) -> Callable[[Parameter, ConfigurationView], None]:
    """Validation that raises an error when the CIDR value of the parameter is not contained within the parent CIDR"""
    def wrapper(parameter: Parameter, configuration: ConfigurationView) -> None:
        parent = configuration.get_item_for_key(parent_cidr_name).parameter
        subnet_cidr = configuration[parameter.key]
        parent_cidr = configuration[parent.key]
        assert isinstance(parameter, OptionalParameter)
        assert isinstance(parent, OptionalParameter)

        if subnet_cidr is None:
            raise CODException("%s is not set" % (parameter.key))
        if parent_cidr is None:
            raise CODException("%s is not set" % (parent.key))

        if subnet_cidr.network < parent_cidr.network or subnet_cidr.broadcast > parent_cidr.broadcast:
            raise CODException(
                "%s=%s not within %s=%s. Use %s and/or %s to change that." % (
                    parameter.key, subnet_cidr,
                    parent.key, parent_cidr,
                    parent.default_flag, parameter.default_flag
                )
            )

    return wrapper
