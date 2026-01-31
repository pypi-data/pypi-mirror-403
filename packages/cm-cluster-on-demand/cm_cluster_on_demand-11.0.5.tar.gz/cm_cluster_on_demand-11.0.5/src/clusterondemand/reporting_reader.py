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
import sys
from typing import Any


class ReportingReader:
    """
    Utility wrapper used for reporting on the progress of reading a file.

    The ReportingReader can be used as a normal file-like object. The main
    difference with a general file-like object is that each time "read" is
    called the read progress is printed to the console.

    For example, to report the progress of uploading a file you can use:

        with ReportingReader(massive_file_path) as local_file:
            requests.post(url, data=local_file)

    This will use the default streaming uploads capability of requests to
    upload a file, but displays the upload progress on the terminal.
    """

    def __init__(self, file_path: str, mode: str = "rb", progress_prefix: str = "") -> None:
        self._previous_status = ""
        self._progress_prefix = progress_prefix
        self._file_size = os.path.getsize(file_path)
        self._reader = open(file_path, mode)

    def __enter__(self) -> ReportingReader:
        return self

    def __exit__(self, exc_type: Any, exc_value: Any, traceback: Any) -> None:
        ReportingReader.write_progress("")
        self._reader.close()

    @staticmethod
    def write_progress(string: str) -> None:
        if not sys.stderr.isatty():
            return
        sys.stderr.write("\r" + string)

    def read(self, size: int = -1) -> Any:
        progress = self._reader.tell() / self._file_size * 100
        status = f"{self._progress_prefix}{progress:.0f}%"
        if status != self._previous_status:
            ReportingReader.write_progress(status)
            self._previous_status = status
        return self._reader.read(size)
