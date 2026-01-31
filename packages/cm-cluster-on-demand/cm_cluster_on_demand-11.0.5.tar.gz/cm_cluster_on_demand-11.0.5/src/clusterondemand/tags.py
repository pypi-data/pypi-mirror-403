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
from collections.abc import Iterable, Sequence
from typing import Any

from clusterondemand import const, utils
from clusterondemand.utils import partition
from clusterondemandconfig import ConfigNamespace

log = logging.getLogger("cluster-on-demand")

tags_ns = ConfigNamespace("cluster.create.tags")

tags_ns.add_enumeration_parameter(
    "cluster_tags",
    default=[],
    help=("Tags to apply to cluster resources "
          "(i.e. --cluster-tags tag1=value tag2=value)."),  # TODO: Only nodes or also VPCs etc.?
    parser=utils.parse_assignment,
    serializer=lambda val: "{}={}".format(*val)
)

tags_ns.add_enumeration_parameter(
    "head_node_tags",
    default=[],
    help=("Tags to apply to the head node "
          "(e.g. --head-node-tags tag1=value tag2=value)."),
    parser=utils.parse_assignment,
    serializer=lambda val: "{}={}".format(*val)
)


def format_cluster_tags(dict_tags: dict[str, Any], unparsed_tags: list[str] | None = None) -> list[str]:
    if unparsed_tags is None:
        unparsed_tags = []

    list_tags, single_tags = partition(lambda x: isinstance(dict_tags[x], list), dict_tags)

    collapsed_dict_tags = ["%s=%s" % (tag, dict_tags[tag]) for tag in single_tags]
    for tag in list_tags:
        collapsed_dict_tags += ["%s#%s" % (tag, value) for value in dict_tags[tag]]

    tags = collapsed_dict_tags + unparsed_tags
    return tags


def format_packagegroups_tags(package_groups: Iterable[str]) -> list[str]:
    return [f"{const.COD_PACKAGE_GROUP}={group}" for group in package_groups]


def parse_cluster_tags(tags: Sequence[str]) -> tuple[dict[str, str | list[str]], list[str]]:
    """Parse the cluster tags to a shape easier to handle.

    Clusters will have tags like 'COD::XX=YY', this returns a dict where dict['COD::XX'] = YY
    Tags that don't follow this key=value form, are returned in a list

    Since the package group tag can appear more than once, it's not included.
    Use get_packagegroups_from_tags(tags) to get that data.

    Tags are allowed to be repeated using the format ['COD::XX#YY', 'COD::XX#ZZ']. In that
    case it will be returned as dict['COD::XX'] = ['YY', 'ZZ']

    :param tags: list of cluster tags
    :return: Tuple (dict_tags, unparsed_tags)
    """
    if not tags:
        return ({}, [])

    single_tags_regex = re.compile("(?!" + const.COD_PACKAGE_GROUP + ")(COD::.+)=(.+)")
    list_tags_regex = re.compile("(COD::.+)#(.+)")

    dict_tags: dict[str, str | list[str]] = {}
    unparsed_tags: list[str] = []

    for tag in tags:
        # Try to parse as a single tag.
        m = single_tags_regex.match(tag)
        if m:
            k, v = m.groups()
            dict_tags[k] = v
            continue

        # Try to parse as a list tag.
        m = list_tags_regex.match(tag)
        if m:
            k, v = m.groups()
            vals = dict_tags.setdefault(k, [])
            assert isinstance(vals, list)
            vals.append(v)
            continue

        # Otherwise add it to unparsed tags.
        unparsed_tags.append(tag)

    return dict_tags, unparsed_tags


def get_packagegroups_from_tags(tags: Iterable[str]) -> list[str]:
    """Return the list of package groups from the cluster tags."""
    if not tags:
        return []
    regex = re.compile(const.COD_PACKAGE_GROUP + "=(.+)")
    return [m.group(1) for m in [regex.match(tag) for tag in tags] if m]
