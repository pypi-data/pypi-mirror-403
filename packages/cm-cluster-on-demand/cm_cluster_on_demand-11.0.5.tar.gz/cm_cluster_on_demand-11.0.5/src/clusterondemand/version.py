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
from collections import OrderedDict

import yaml

PATH_TO_VERSION_INFO = os.path.join(os.path.dirname(os.path.realpath(__file__)), "version-info.yaml")

HUMAN_READABLE_INFO = OrderedDict([
    ("version", "Version"),
    ("branch", "Branch"),
    ("git_hash", "Git Hash"),
    ("git_date", "Git Date"),
    ("build_date", "Build Date"),
])


def get_version_info() -> dict[str, str]:
    """Returns dictionary containing the version information."""
    try:
        version_info: dict[str, str] = yaml.safe_load(open(PATH_TO_VERSION_INFO).read())
        return version_info
    except FileNotFoundError:
        return {
            "version": "trunk",
            "branch": "",
            "git_hash": "",
            "git_date": "",
            "build_date": ""
        }


def print_version_info() -> None:
    version_info = get_version_info()
    for key, human_text in HUMAN_READABLE_INFO.items():
        value = version_info.get(key)
        if value:
            print(f"{human_text}: {value}")
