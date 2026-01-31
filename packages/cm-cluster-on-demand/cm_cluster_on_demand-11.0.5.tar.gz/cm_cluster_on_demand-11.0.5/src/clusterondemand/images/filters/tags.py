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

from collections.abc import Collection, Iterable


def match_by_tags(tags: Iterable[str], image_tags: Collection[str]) -> bool:
    """Check all the tags are present in image_tags.

    In other cases we are looking for images with all the passed package groups
    installed
    >>> match_by_tags(["gr1", "gr2"], ["gr1", "other"])
    False
    >>> match_by_tags(["gr1", "gr2"], ["other"])
    False
    >>> match_by_tags(["gr1", "gr2"], ["gr2", "gr1", "other"])
    True

    """
    for tag in tags:
        if tag not in image_tags:
            return False
    return True
