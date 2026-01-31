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

from collections.abc import Collection


def match_by_package_groups(package_groups: Collection[str], image_package_groups: Collection[str]) -> bool:
    """Check if image_package_groups fits the requirement.

    If there is "any" in package_groups than we accepting any image
    >>> match_by_package_groups(["any", "something"], ["other", "yada"])
    True

    If there is "none" in package_groups than we accept only the image with empty
    list of package groups
    >>> match_by_package_groups(["none", "something"], ["other"])
    False
    >>> match_by_package_groups(["none", "something"], [])
    True

    In other cases we are looking for images with all the passed package groups
    installed
    >>> match_by_package_groups(["gr1", "gr2"], ["gr1", "other"])
    False
    >>> match_by_package_groups(["gr1", "gr2"], ["other"])
    False
    >>> match_by_package_groups(["gr1", "gr2"], ["gr2", "gr1", "other"])
    True

    """
    if "none" in package_groups:
        return len(image_package_groups) == 0
    if "any" in package_groups:
        return True
    for package_group in package_groups:
        if package_group not in image_package_groups:
            return False
    return True
