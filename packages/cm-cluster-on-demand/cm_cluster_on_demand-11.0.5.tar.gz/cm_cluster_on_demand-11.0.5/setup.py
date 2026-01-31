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

from setuptools import setup
from setuptools_scm import get_version

__version__ = get_version(root="..", relative_to=__file__)

setup(
    install_requires=[
        "cm-cluster-on-demand-config==" + __version__,
        "filelock>=2.0.8",
        "netaddr>=0.8.0",
        "passlib>=1.7.4",
        "PrettyTable>=3.4.0",
        "python_dateutil>=1.5",
        "pytz>=2022.5",
        "pyyaml>=6.0",
        "requests>=2.31.0",
        "rich>=13.7.0",
        "tenacity>=8.1.0",
        "urllib3>=2.5.0",
    ]
)
