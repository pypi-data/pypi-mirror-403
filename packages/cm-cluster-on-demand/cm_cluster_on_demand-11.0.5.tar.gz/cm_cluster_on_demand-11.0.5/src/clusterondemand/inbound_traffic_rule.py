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

import logging
import re
import socket
from copy import deepcopy
from enum import Enum, auto
from functools import cached_property
from ipaddress import ip_network

from clusterondemand.exceptions import CODException
from clusterondemand.utils import get_public_ip_of_cod_client

CLIENT_IP = r"{CLIENT_IP}"
IPV4_CIDR = r"\d{1,3}(?:\.\d{1,3}){3}(?:/\d{1,2})"
IPV4_CIDR_OR_CLIENT_IP = r"(" + IPV4_CIDR + "|" + CLIENT_IP + ")"
PORT_OR_PORT_RANGE = r"(\d{1,5}(-\d{1,5})?)?"
PORT = r"\d{1,5}"
TRANSPORT_PROTOCOL = r"(tcp|udp)"
ICMP_AND_ALL_PROTOCOL = r"(icmp|all)"
ALL_PROTOCOL_NUMBER = -1  # Hardcoded because socket.getprotobyname doesn't handle "all". Based on boto3 docs
ANY = "*"

# Inbound Rule Regular expression for inbound rule matching the following format:
#   [SRC_CIDR[:SRC_PORT_OR_PORT_RANGE],]DST_PORT_OR_PORT_RANGE[:PROTOCOL]
INBOUND_RULE_SOURCE_REGEX = r"^(" + IPV4_CIDR_OR_CLIENT_IP + "(:" + PORT_OR_PORT_RANGE + ")?,)?"
INBOUND_RULE_DESTINATION_REGEX = PORT_OR_PORT_RANGE + "(:" + TRANSPORT_PROTOCOL + ")?"
INBOUND_RULE_REGEX = INBOUND_RULE_SOURCE_REGEX + INBOUND_RULE_DESTINATION_REGEX

# Network ACL Regular expression matching the following format:
#    [SRC_CIDR,]DST_PORT_OR_PORT_RANGE:TCP|UDP,ALLOW|DENY,RULE_NUM or
#    [SRC_CIDR,]ICMP|ALL,ALLOW|DENY,RULE_NUM
RULE_ACTION = r"(allow|deny)"
RULE_NUMBER = r"(\d{1,5})"
NETWORK_ACL_SUFFIX = r"," + RULE_ACTION + "," + RULE_NUMBER
NETWORK_ACL_SOURCE_REGEX = r"^(" + IPV4_CIDR_OR_CLIENT_IP + ",)?"
NETWORK_ACL_TRANSPORT_DESTINATION_REGEX = INBOUND_RULE_DESTINATION_REGEX
NETWORK_ACL_TRASPORT_REGEX = NETWORK_ACL_SOURCE_REGEX + NETWORK_ACL_TRANSPORT_DESTINATION_REGEX + NETWORK_ACL_SUFFIX
NETWORK_ACL_ICMP_OR_ALL_REGEX = NETWORK_ACL_SOURCE_REGEX + ICMP_AND_ALL_PROTOCOL + NETWORK_ACL_SUFFIX
RESERVED_NETWORK_ACL_RULE_NUM = 10010
EPHEMERAL_PORTS_ACL_RULE_NUM = 10020  # Used to identify ephemeral ports in cm-cloud-ha-setup


class RuleType(Enum):
    TCP_OR_UDP = auto(),
    ICMP_OR_ALL = auto(),
    INVALID = auto()


log = logging.getLogger("cluster-on-demand")


def parse_port(port: str) -> tuple[str, str]:
    if "-" in port:
        first_port, last_port = port.split("-")
    else:
        first_port = last_port = port
    return first_port, last_port


def parse_source(source_rule: str) -> tuple[str, str]:
    if ":" in source_rule:
        cidr, port = source_rule.split(":")
    else:
        cidr, port = source_rule, ANY
    return cidr, port


def parse_destination(destination_rule: str) -> tuple[str, str]:
    if ":" in destination_rule:
        port, protocol = destination_rule.split(":")
        protocol = protocol.lower()
    else:
        port, protocol = destination_rule, ANY
    return port, protocol


def _validate_rule_cidr(rule_obj: InboundTrafficRule | InboundNetworkACLRule) -> None:
    rule_type = "inbound network ACL rule" if isinstance(rule_obj, InboundNetworkACLRule) else "inbound rule"

    try:
        ip_network(rule_obj.src_cidr, strict=True)
    except ValueError:
        raise CODException(f"Found invalid CIDR '{rule_obj.src_cidr}' in {rule_type} '{rule_obj}'")


# Class for AWS Network ACL
class InboundNetworkACLRule:
    def __init__(self, network_acl_rule: str) -> None:
        self.network_acl_rule = network_acl_rule
        if self.rule_type == RuleType.INVALID:
            raise CODException(self._get_error_message(network_acl_rule))
        self._parse_rule()

    @property
    def protocol_numeric_str(self) -> str:
        return str(self.protocol_number)

    @property
    def protocol_number(self) -> int:
        if self.protocol == "all":
            return ALL_PROTOCOL_NUMBER
        return socket.getprotobyname(self.protocol)

    @staticmethod
    def _get_error_message(network_acl_rule: str) -> str:
        return (f"Network ACL rule '{network_acl_rule}' does not match the expected format.\n"
                f"The expected format is: '[src_cidr,]dst_port:{TRANSPORT_PROTOCOL},{RULE_ACTION},rule_num' or "
                f"'[src_cidr,]{ICMP_AND_ALL_PROTOCOL},{RULE_ACTION},rule_num'.\n"
                "Examples: '11.0.0.0/24:TCP,ALLOW,100' '12.0.0.0/32:6000-6500,443:TCP,ALLOW,200"
                "'ICMP,ALLOW,500' '10.0.0.0/16,ALL,ALLOW,500'\n"
                f"src_cidr can be replaced with {CLIENT_IP}, as in "
                f"'{CLIENT_IP},20-23:TCP:ALLOW,101', in which case the client's public IP will be detected and used"
                )

    @cached_property
    def rule_type(self) -> RuleType:
        if re.match(NETWORK_ACL_TRASPORT_REGEX + "$", self.network_acl_rule, re.IGNORECASE):
            return RuleType.TCP_OR_UDP
        if re.match(NETWORK_ACL_ICMP_OR_ALL_REGEX + "$", self.network_acl_rule, re.IGNORECASE):
            return RuleType.ICMP_OR_ALL
        return RuleType.INVALID

    def _parse_rule(self) -> None:
        if CLIENT_IP in self.network_acl_rule:
            client_ip = get_public_ip_of_cod_client()
            self.network_acl_rule = self.network_acl_rule.replace(CLIENT_IP, f"{client_ip}/32")
        divide_pattern = r"^(.*?)," + RULE_ACTION + "," + RULE_NUMBER + "$"
        match = re.search(divide_pattern, self.network_acl_rule, re.IGNORECASE)
        if match is None or len(match.groups()) != 3:
            raise CODException(self._get_error_message(self.network_acl_rule))
        rule_body = match.group(1)
        if self.rule_type == RuleType.ICMP_OR_ALL:
            self._parse_icmp_or_all_rule(rule_body)
        elif self.rule_type == RuleType.TCP_OR_UDP:
            self._parse_transport_rule(rule_body)

        self.rule_action = match.group(2)
        self.rule_number = int(match.group(3))
        if not 1 <= self.rule_number <= 32766:
            raise CODException(
                f"The rule number of {self.network_acl_rule} is not within range from 1 to 32766"
            )
        if self.rule_number == RESERVED_NETWORK_ACL_RULE_NUM:
            raise CODException(
                f"The rule number of {self.network_acl_rule} conflicts with the reserved rule num. "
                f"{RESERVED_NETWORK_ACL_RULE_NUM} is reserved for internal VPC communication."
            )

    def _parse_transport_rule(self, transport_rule: str) -> None:
        # [src_cidr,]dst_port:(tcp|udp)
        if "," in transport_rule:
            self.src_cidr, destination_rule = transport_rule.split(",")
        else:
            self.src_cidr = "0.0.0.0/0"
            destination_rule = transport_rule
        dst_port, self.protocol = parse_destination(destination_rule)
        self.dst_first_port, self.dst_last_port = parse_port(dst_port)
        _validate_rule_cidr(self)

    def _parse_icmp_or_all_rule(self, icmp_or_all_rule: str) -> None:
        # [src_cidr,](icmp|all)
        if "," in icmp_or_all_rule:
            self.src_cidr, self.protocol = icmp_or_all_rule.split(",")
        else:
            self.src_cidr = "0.0.0.0/0"
            self.protocol = icmp_or_all_rule
        self.protocol = self.protocol.lower()

    def __str__(self) -> str:
        return self.network_acl_rule


class InboundTrafficRule:
    def __init__(self, inbound_rule: str) -> None:
        if not self.validate_inbound_rule(inbound_rule):
            raise CODException(f"Inbound rule '{inbound_rule}' does not match the expected format.\n"
                               "The expected format is: [src_cidr[:src_port],]dst_port[:protocol]\n"
                               "Examples: '80' '21:udp' '11.0.0.0/24,20-23:TCP' "
                               "'12.0.0.0/32:6000-6500,443'. \n"
                               f"src_cidr can be replaced with {CLIENT_IP}, as in '{CLIENT_IP},20-23:TCP', "
                               "in which case COD client's public IP will be detected and used")
        self.inbound_rule = inbound_rule
        self._parse_rule()

    def _parse_rule(self) -> None:
        if CLIENT_IP in self.inbound_rule:
            client_ip = get_public_ip_of_cod_client()
            self.inbound_rule = self.inbound_rule.replace(CLIENT_IP, f"{client_ip}/32")
        if "," in self.inbound_rule:
            source_rule, destination_rule = self.inbound_rule.split(",")
        else:
            source_rule = "{src_cidr}:{src_port}".format(src_cidr="0.0.0.0/0", src_port=ANY)
            destination_rule = self.inbound_rule
        self.src_cidr, self.src_port = parse_source(source_rule)
        self.src_first_port, self.src_last_port = parse_port(self.src_port)
        self.dst_port, self.protocol = parse_destination(destination_rule)
        self.protocol_number = (
            socket.getprotobyname(self.protocol)
            if self.protocol != ANY
            else ALL_PROTOCOL_NUMBER
        )
        self.dst_first_port, self.dst_last_port = parse_port(self.dst_port)
        if not self.dst_first_port <= self.dst_last_port and self.src_first_port <= self.src_last_port:
            raise CODException("Invalid inbound traffic rule: port_range_min must be <= port_range_max")
        _validate_rule_cidr(self)

    @staticmethod
    def validate_inbound_rule(inbound_rule: str) -> re.Match[str] | None:
        return re.match(INBOUND_RULE_REGEX + "$", inbound_rule, re.IGNORECASE)

    def __str__(self) -> str:
        return self.inbound_rule

    @staticmethod
    def process_inbound_rules(inbound_rules: list[InboundTrafficRule]) -> list[InboundTrafficRule]:
        if not inbound_rules:
            return []
        processed_inbound_rules = deepcopy(inbound_rules)
        for inbound_rule in processed_inbound_rules:
            if any(port != "*" for port in [inbound_rule.src_first_port, inbound_rule.src_last_port]):
                log.warning("Source port was specified in rule {traffic_rule} but is only supported by Azure "
                            "so will be ignored.".format(traffic_rule=inbound_rule))

            # if the protocol is not specified in the rule, it has to be split into two separate rules (tcp/udp)
            if inbound_rule.protocol == "*":
                inbound_rule.protocol = "tcp"
                inbound_rule.protocol_number = socket.getprotobyname("tcp")
                inbound_rule_copy = deepcopy(inbound_rule)
                inbound_rule_copy.protocol = "udp"
                inbound_rule_copy.protocol_number = socket.getprotobyname("udp")
                processed_inbound_rules.append(inbound_rule_copy)

        return processed_inbound_rules
