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

import re
from functools import total_ordering
from logging import getLogger
from typing import Any

from clusterondemand.exceptions import CODException

log = getLogger("cluster-on-demand")


_DISTRO_REGEX = [
    re.compile(r"^(?P<family>(?:rocky|alma)?centos)(?:(?P<major>\d+)(?:(u|\.)(?P<minor>\d+))?)?$"),
    re.compile(r"^(?P<family>rhel)(?:(?P<major>\d+)(?:(u|\.)(?P<minor>\d+))?)?$"),
    re.compile(r"^(?P<family>sles)(?:(?P<major>\d+)(?:sp(?P<minor>\d+))?)?$"),
    re.compile(
        r"^(?P<base_family>ubuntu)(?:(?P<base_major>\d{2})(\.)?(?P<base_minor>\d{2})?)?"
        r"-(?P<family>dgx-os)(-(?P<major>\d+)?(\.)?(?P<minor>\d+)?)?$",
    ),
    re.compile(r"^(?P<family>ubuntu)(?:(?P<major>\d\d)(\.)?(?P<minor>\d\d)?)?$"),
    re.compile(r"^(?P<family>sl)(?:(?P<major>\d+)(?:u(?P<minor>\d+))?)?$"),
    re.compile(r"^(?P<family>rocky|alma)(?:(?P<major>\d+)(?:(u|\.)(?P<minor>\d+))?)?$"),
]


def parse_distro_string(distro: str) -> tuple[str, int | None, int | None]:
    """
    Parses the input distro string and extracts the distribution family, major version, and minor version.

    Parameters:
        distro (str): The input distro string to be parsed.

    Returns:
        tuple[str, int | None, int | None]: A tuple containing the distribution family, major version (or None),
        and minor version (or None).

    Raises:
        ValueError: If the input 'distro' parameter is not of type str.
        CODException: If the 'distro' string does not match any of the predefined regex patterns.
    """
    if not isinstance(distro, str):
        raise ValueError(f"distro parameter should be of type str, found {distro.__class__}")
    family = None
    major = None
    minor = None
    for regex in _DISTRO_REGEX:
        match = regex.match(distro)
        if match:
            family = str(match["family"])
            major = int(match["major"]) if match["major"] else None
            minor = int(match["minor"]) if match["minor"] else None
            assert family and (not minor or minor and major), (
                f"Invalid distro regex: {regex}")
            break
    else:
        raise CODException(f"Unable to determine base distribution from '{distro}'")

    return (family, major, minor)


@total_ordering
class ImageDistroSpec:
    """Utility class for parsing and comparing image distro specifications."""

    _DISTRO_FORMAT = {
        "centos": "{}u{}",
        "rhel": "{}u{}",
        "sles": "{}sp{}",
        "ubuntu": "{}{:02d}",
        "sl": "{}u{}",
        "rocky": "{}u{}",
        "rockycentos": "{}u{}",
        "alma": "{}u{}",
        "almacentos": "{}u{}",
    }

    def __init__(self, distro: str | None) -> None:
        parts = parse_distro_string(distro) if distro is not None else (None, None, None)
        self._family: str | None = parts[0]
        self._major: int | None = parts[1]
        self._minor: int | None = parts[2]

    def __eq__(self, value: Any) -> bool:
        if isinstance(value, str):
            value = ImageDistroSpec(value)
        if not isinstance(value, ImageDistroSpec):
            return False
        return (self.family == value.family and
                self.major == value.major and
                self.minor == value.minor)

    def __gt__(self, value: Any) -> bool:
        if isinstance(value, str):
            value = ImageDistroSpec(value)
        if not isinstance(value, ImageDistroSpec):
            return False
        if self.family != value.family:
            raise Exception(f"Cannot compare distros '{self}' and '{value}'")
        major1 = self.major or 0
        minor1 = self.minor or 0
        major2 = value.major or 0
        minor2 = value.minor or 0
        return major1 > major2 or (major1 == major2 and minor1 > minor2)

    def __contains__(self, value: Any) -> bool:
        if isinstance(value, str):
            value = ImageDistroSpec(value)
        if not isinstance(value, ImageDistroSpec):
            return False
        return ((self.family is None or self.family == value.family) and
                (self.major is None or self.major == value.major) and
                (self.minor is None or self.minor == value.minor))

    def __str__(self) -> str:
        if not self.family:
            return ""
        result = self.family
        if self.major is not None:
            result += str(self.major)
            if self.minor is not None:
                result = self._DISTRO_FORMAT[self.family].format(result, self.minor)
        return result

    @property
    def family(self) -> str | None:
        return self._family

    @property
    def major(self) -> int | None:
        return self._major

    @property
    def minor(self) -> int | None:
        return self._minor

    @property
    def family_and_major(self) -> str | None:
        if self.family and self.major:
            return self.family + str(self.major)
        return None

    @property
    def full(self) -> str | None:
        return str(self) if self.is_full else None

    @property
    def is_full(self) -> bool:
        return self.major is not None and self.minor is not None


def latest_distro(list_of_distros: list[str], distro: str) -> ImageDistroSpec | None:
    """
    Given a list of distros, we return the latest for a given distro specification
    `distro` can be:
    - Distro family: "centos"
    - Distro family and major: "centos7"
    - Full distro name: "centos7u7"
    - None: In this case we return the latest from the list

    list_of_distros has to be all in the full name format and all the same distro family
    """
    if not list_of_distros:
        return None

    distros = [ImageDistroSpec(d) for d in list_of_distros]
    if distro:
        distro_spec = ImageDistroSpec(distro)
    else:
        distro_spec = ImageDistroSpec(distros[0].family)

    distros = [d for d in distros if d in distro_spec]
    return max(distros) if distros else None
