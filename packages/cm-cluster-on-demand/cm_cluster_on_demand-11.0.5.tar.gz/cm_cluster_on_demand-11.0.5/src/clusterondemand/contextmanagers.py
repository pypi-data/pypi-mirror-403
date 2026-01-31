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
import os
from collections.abc import Iterator
from contextlib import contextmanager

from filelock import FileLock

from clusterondemand.utils import is_writable_directory

log = logging.getLogger("cluster-on-demand")


@contextmanager
def SmartLock(lock_file: str) -> Iterator[None]:
    """
    An enhanced FileLock that gracefully disables synchronization
    if the parent directory of the specified lock file does not
    exist or is not writable.
    """
    if is_writable_directory(os.path.dirname(lock_file)):
        with FileLock(lock_file):
            yield

    else:
        log.debug("%s is not a writable directory! Locking not available.", os.path.dirname(lock_file))
        yield
