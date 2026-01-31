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

FLEXIBLE_VERSION_PATTERN = r'^(?P<major>\d+)(\.(?P<minor>\d+))?(\.(?P<patch>\d+))?(-(?P<suffix>dev|rc))?$'


def validate_version_format(version_string: str) -> None:
    """Validate BCM version format according to versioning rules.

    Rules:
    - Versions < 10: Must be major.minor format (e.g., 9.0, 9.1, 9.2)
      Single digit (e.g., "9") or patch versions (e.g., "9.2.0") are NOT allowed.
    - Versions >= 10: Can be major (e.g., "10"), major.0 (e.g., "10.0"),
      or major.Y.Z where Y!=0 (e.g., "10.30.0", "11.7.5")
      Note: "X.0" is for backend compatibility. If minor!=0, full version number is required.
    - Dev versions: Cannot have patch numbers (e.g., "11.30.0-dev" is invalid)
      For v<10: "9.2-dev" is valid
      For v>=10: only "10-dev" or "10.0-dev" are valid (minor must be 0 or omitted)
    - RC versions: Can have patch numbers (e.g., "11.30.0-rc" is valid)

    Args:
        version_string: The version string to validate

    Raises:
        CODException: If version format is invalid according to the rules
    """
    if version_string == "trunk":
        return

    match = re.match(FLEXIBLE_VERSION_PATTERN, version_string)
    if not match:
        raise CODException(
            f"The value '{version_string}' is not a valid BCM version. "
            "Examples: '10', '10.0', '10.30.0', '9.2', '10-dev'"
        )

    major = int(match.group("major"))
    minor = match.group("minor")
    patch = match.group("patch")
    suffix = match.group("suffix")

    # For versions < 10: only major.minor format is valid
    if major < 10 and (not minor or patch):
        raise CODException(
            f"Invalid version '{version_string}'. For versions < 10. "
            f"Use major.minor format only (e.g., '9.0', '9.1', '9.2')"
        )

    # Dev versions cannot have patch numbers
    # For v>=10: minor must be 0 (or not specified)
    # For v<10: any minor is allowed (already validated above)
    if suffix == "dev":
        if patch:
            raise CODException(
                f"Invalid version '{version_string}'. Dev versions cannot have patch numbers"
            )
        if major >= 10 and minor and minor != "0":
            raise CODException(
                f"Invalid version '{version_string}'. Use '{major}-dev' or '{major}.0-dev' instead"
            )

    # For versions >= 10: if minor != 0, patch is required
    # Valid: "10", "10.0", "10.30.0"
    # Invalid: "10.30", "11.7"
    if major >= 10 and minor and minor != "0" and not patch:
        raise CODException(
            f"Invalid version '{version_string}'. "
            f"Only allowed minor version is 0, otherwise full version number is required. "
            f"Examples: '{major}', '{major}.0', or '{major}.30.0'"
        )


def normalize_version_for_backend(version_string: str, cloud_type: str | None = None) -> str:
    """Normalize a BCM version string for backend/cloud provider queries.

    Backend systems (AWS, OpenStack, Azure, etc.) store images with version metadata
    that uses a consistent format. For v>=10, all images are stored with "X.0" format
    regardless of the actual patch version.

    Examples:
        "11" -> "11.0"           (fill up)
        "11.0" -> "11.0"         (no change)
        "11.30.0" -> "11.0"      (strip down)
        "10-dev" -> "10.0-dev"   (fill up with minor)
        "9.2" -> "9.2"           (v<10 unchanged)

    Note: For OpenStack, the full patch version is stored in bcm_optional_info field,
    which allows client-side filtering for exact patch matches.

    Args:
        version_string: The version to normalize (e.g., "11", "11.30.0", "9.2")
        cloud_type: The cloud provider type (e.g., 'openstack', 'aws', 'azure').
                   Passed to validate_version_format for warning purposes.

    Returns:
        Normalized version string for backend queries

    Raises:
        CODException: If version_string is invalid (via validate_version_format)
    """
    if version_string == "trunk":
        return version_string

    validate_version_format(version_string)
    match = re.match(FLEXIBLE_VERSION_PATTERN, version_string)
    assert match  # Needed for mypy, validate_version_format ensures this

    major = int(match.group("major"))
    patch = match.group("patch")

    # For v<10, keep as-is
    if major < 10:
        return version_string

    # Warn if user specifies exact patch version for non-OpenStack clouds
    # (before we normalize it away)
    if cloud_type and cloud_type != "openstack" and patch and major >= 10:
        log.warning(
            f"Exact release version '{version_string}' specified, but {cloud_type} "
            f"doesn't yet support exact version matching. The query will match any version {major} ({major}.0) image."
        )

    # For v>=10, normalize to X.0 format (lazy, don't check if used supplied .0, just do anyway)
    suffix = match.group("suffix")
    normalized = f"{major}.0"
    if suffix:
        normalized += f"-{suffix}"
    return normalized


@total_ordering
class BcmVersion:
    """A utility class for comparing Base Command Manager versions.

    Wraps a version number string and handles comparison logic.

    Hard-coded assumption: Once we start working on BCM with major version X, then we
    will never release another minor version of a major X-1. That is: there will never be a release
    of something like 8.4 if 9.0 has been released (even internally).

    The comparison is based on the order in which versions appear during the development cycle:
    - For v<10: 9.0 < 9.1 < 9.2
    - For v>=10: 10.0-dev < 10.0-rc < 10.0 < 10.30.0 < 11.0
    - Note: "10" == "10.0" and "11" == "11.0"

    """
    @classmethod
    def _wrap_with_instance(cls, obj: BcmVersion | str) -> BcmVersion:
        return obj if isinstance(obj, cls) else cls(obj)  # type: ignore

    def __init__(self, string: str) -> None:
        self.string: str = string
        self.major: int = 0
        self.minor: int = 0
        self.patch: int = -1  # -1 means no patch specified, used for sorting
        self.suffix: int = 0  # stored as integer for easy comparison, see below

        if "trunk" == string:
            self.major = self.minor = 1000000  # store trunk as high number so it always wins in comparisons
            return

        validate_version_format(string)
        match = re.match(FLEXIBLE_VERSION_PATTERN, string)
        assert match  # Needed for mypy, validate_version_format ensures this

        self.major = int(match.group("major"))
        self.minor = int(match.group("minor")) if match.group("minor") else 0
        self.patch = int(match.group("patch")) if match.group("patch") else -1

        if not match.group("suffix"):
            self.suffix = 2  # there was no suffix, so this is a public release like 10.0, 10.30.0, store as highest
        elif match.group("suffix") == "rc":
            self.suffix = 1  # release candidate comes before public release
        elif match.group("suffix") == "dev":
            self.suffix = 0  # dev version before release candidate

    def __str__(self) -> str:
        return self.string

    def __eq__(self, other: Any) -> bool:
        other = self.__class__._wrap_with_instance(other)
        # For v>=10: "10" == "10.0" (both have patch=-1)
        return (
            (self.major, self.minor, self.patch, self.suffix)
            == (other.major, other.minor, other.patch, other.suffix)
        )

    def __gt__(self, other: BcmVersion | str) -> bool:
        other = self.__class__._wrap_with_instance(other)
        # For v>=10: base versions (patch=-1) come before patch versions
        # Order: 10.0-dev < 10.0-rc < 10.0 < 10.30.0
        return (
            (self.major, self.minor, self.suffix, self.patch)
            > (other.major, other.minor, other.suffix, other.patch)
        )

    """ Can be used for comparison when we don't care about suffix.
    For example: version.release > (10, 0)
    Note, when version is trunk it returns (1000000, 1000000) so that trunk is always the highest version"""
    @property
    def release(self) -> tuple[int, int]:
        return (self.major, self.minor)
