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

from typing import Any, Callable, TypeVar

RT = TypeVar("RT")


def static_vars(**kwargs: Any) -> Callable[[Callable[..., RT]], Callable[..., RT]]:
    """Set some local static variables in a function.

    This will be a global variable, but linked to a function by being an attribute of it

    Example:
    @static_vars(my_var=0):
    def f():
      f.my_var += 1
    """
    def decorator(func: Callable[..., RT]) -> Callable[..., RT]:
        for key, value in kwargs.items():
            setattr(func, key, value)
        return func
    return decorator
