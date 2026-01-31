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

import importlib
from types import ModuleType
from typing import Any


def import_if_exists(module: str) -> ModuleType | None:
    """Try to import a module. If the module does not exist, nothing is raised."""
    try:
        return importlib.import_module(module)
    except ImportError as error:
        possible_error_messages = ["No module named %s" % (fragment) for fragment in _module_path_fragments(module)]

        if str(error) in possible_error_messages:
            return None

        raise


def load_module_attribute(module_path: str, attribute: str) -> Any:
    """Return the value of `module_path`.`attribute`, None if the module is not available."""
    module = import_if_exists(module_path)
    return eval("module.%s" % (attribute)) if module else None


def _module_path_fragments(module_path: str) -> list[str]:
    """Convert a module path like 'foo.bar.baz' to ["'foo'", "'foo.bar'", "'foo.bar.baz'"]."""
    fragments = []
    while "." in module_path:
        fragments.append("'%s'" % (module_path))
        module_path = module_path[:module_path.index(".")]
    return fragments + ["'%s'" % (module_path)]
