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

from collections.abc import Iterable

from clusterondemand.exceptions import CODException


def expand_vlan_ids(vlan_ids: Iterable[tuple[int, int]]) -> list[int]:
    """Translate [[20, 22], 10] to [10, 20, 21, 22]."""
    ret = []
    for id_range in vlan_ids:
        len_ = len(id_range)
        if len_ == 1:
            ret.append(id_range[0])
        elif len_ == 2:
            ret.extend(range(id_range[0], id_range[1] + 1))
        else:
            raise Exception("Bad value for vlan IDs: %s" % str(id_range))
    return sorted(ret)


def vlan_id_parser(string: str) -> list[int]:
    try:
        return [int(string)]
    except ValueError:
        pass

    try:
        start, end = string.split("-")
        return [int(start), int(end)]
    except ValueError as e:
        raise CODException(
            "Invalid vlan ID format. Should be in '[<start ID>-<end ID> | ID] "
            "[[<start ID>-<end ID> | ID]]' format. Value: %s" % string,
            caused_by=e
        )


def vlan_id_serializer(value: list[int]) -> str:
    if len(value) == 1:
        return str(value[0])

    if len(value) == 2:
        return str(value[0]) + "-" + str(value[1])

    # values should either be individual ID, or start/end pair
    assert False, "Bad value %s for vlan ID." % str(value)
