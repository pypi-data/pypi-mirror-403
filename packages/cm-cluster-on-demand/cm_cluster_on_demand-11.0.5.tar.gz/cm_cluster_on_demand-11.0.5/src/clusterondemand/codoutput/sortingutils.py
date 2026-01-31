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

import csv
from abc import ABC, abstractmethod
from datetime import datetime
from functools import total_ordering
from io import StringIO
from ipaddress import IPv4Address
from typing import Any

import prettytable
import yaml

from .datetimefunctions import format_datetime, get_datetime_ago


@total_ordering
class NoneWrapper:
    """
    Object of any data type can be compared to the instance of this class.
    No error is raised with any comparison operators.
    Needed to convert None into its instance to sort table with unexpected, mixed data types.
    """
    def __init__(self) -> None:
        pass

    def __eq__(self, other: Any) -> bool:
        if isinstance(other, NoneWrapper):
            return True

        return False

    def __gt__(self, other: Any) -> bool:
        if isinstance(other, NoneWrapper):
            return False

        return True

    def __str__(self) -> str:
        return "?"

    def __repr__(self) -> str:
        return "?"


@total_ordering
class SSHAlias:
    """
    Small helper class for our SSH alias column.

    We sort the SSH aliases based on the index of the alias, not on the prefix. E.g. os1 and os2
    are sorted as 1 and 2. For some clusters there won't be an SSH alias, for example while the
    cluster is being created (there are other cases as well). We want to display those as "?",
    but we also need to be able to sort on the column. So for sorting we treat "?" as 0.
    """
    def __init__(self, alias: str | int, prefix: str = "") -> None:
        self._alias = alias
        self._index: int | str

        if isinstance(alias, str):
            self._index = alias.replace(prefix, "")
        elif isinstance(alias, int):
            self._index = alias
        else:
            raise TypeError(f"alias of type {type(alias)} not supported")

    @staticmethod
    def _index_to_int(index: Any) -> int:
        try:
            return int(index)
        except ValueError:
            return 0

    def __eq__(self, other: Any) -> bool:
        return self._index_to_int(self._index) == self._index_to_int(other._index)

    def __gt__(self, other: Any) -> bool:
        return self._index_to_int(self._index) > self._index_to_int(other._index)

    def __str__(self) -> str:
        return str(self._alias)

    def __repr__(self) -> str:
        return str(self._alias)


# Ignore type error due to mypy bug: https://github.com/python/mypy/issues/8539
@total_ordering
class FormatableData(ABC):
    def __eq__(self, other: Any) -> bool:
        return isinstance(other, type(self)) and self.value_data == other.value_data

    @abstractmethod
    def __lt__(self, other: Any) -> bool:
        pass

    @property
    @abstractmethod
    def table_data(self) -> str:
        pass

    @property
    @abstractmethod
    def csv_data(self) -> str:
        pass

    @property
    @abstractmethod
    def value_data(self) -> str:
        pass

    @property
    @abstractmethod
    def yaml_data(self) -> Any:
        pass


@total_ordering
class ClusterIPs(FormatableData):
    def __init__(
            self,
            primary_ip: str | None = None,
            secondary_ip: str | None = None,
            shared_ip: str | None = None,
            primary_private_ip: str | None = None,
            secondary_private_ip: str | None = None,
            shared_private_ip: str | None = None
    ) -> None:
        self.primary_ip = IPv4Address(primary_ip) if primary_ip is not None else None
        self.secondary_ip = IPv4Address(secondary_ip) if secondary_ip is not None else None
        self.shared_ip = IPv4Address(shared_ip) if shared_ip is not None else None
        self.primary_private_ip = IPv4Address(primary_private_ip) if primary_private_ip is not None else None
        self.secondary_private_ip = IPv4Address(secondary_private_ip) if secondary_private_ip is not None else None
        self.shared_private_ip = IPv4Address(shared_private_ip) if shared_private_ip is not None else None

    # Sorting by IP address if probably not _that_ useful, so no smart implementation here,
    # but we do need to implement these to not raise errors
    def __lt__(self, other: Any) -> bool:
        if isinstance(other, ClusterIPs):
            if self.primary_ip is not None and other.primary_ip is not None:
                return self.primary_ip < other.primary_ip

            return self.primary_ip is None

        return False

    @property
    def table_data(self) -> str:

        # Non-HA cluster
        if not any((self.secondary_ip, self.secondary_private_ip, self.shared_ip, self.shared_private_ip)):
            # Use public IP if available, otherwise, private IP is fine
            return f"{self.primary_ip}" if self.primary_ip \
                else f"{self.primary_private_ip} (Private)" if self.primary_private_ip \
                else ""

        # HA cluster
        elements = [
            # Since OCI support, cluster with private IPs only is a valid use-case, so we fall back to private IPs.
            # Printing private IPs might be useful for other clouds too, if public one is broken for some reason.
            f"{self.primary_ip} (A)" if self.primary_ip
            else f"{self.primary_private_ip} (A) (Private)" if self.primary_private_ip else None,
            f"{self.secondary_ip} (B)" if self.secondary_ip
            else f"{self.secondary_private_ip} (B) (Private)" if self.secondary_private_ip else None,
            f"{self.shared_ip} (HA)" if self.shared_ip
            else f"{self.shared_private_ip} (HA) (Private)" if self.shared_private_ip else None,
        ]

        return "\n".join(filter(None, elements))

    @property
    def value_data(self) -> str:
        return self.csv_data

    @property
    def csv_data(self) -> str:
        # to keep the format consistent we always include all IPs, so for non-ha clusters the last two fields are None
        return " ".join([
            str(self.primary_ip),
            str(self.secondary_ip),
            str(self.shared_ip),
            str(self.primary_private_ip),
            str(self.secondary_private_ip)
        ])

    @property
    def yaml_data(self) -> Any:
        return {
            "primary": str(self.primary_ip),
            "secondary": str(self.secondary_ip),
            "shared": str(self.shared_ip),
            "primary_private": str(self.primary_private_ip),
            "secondary_private": str(self.secondary_private_ip),
        }


class SortableData:
    """
    Utility class for dealing with sortable data.

    :param all_headers: Headers of all columns in following format
        [
            (column_id, column_name),
            ....
        ]
    :param requested_headers: a list of ids of the columns to be displayed.
        If empty. All columns are displayed.
    :param rows: Rows of data
    """

    def __init__(self, all_headers: list[tuple[str, str]], requested_headers: list[str], rows: list[list[Any]]) -> None:
        self.all_headers = all_headers
        self.requested_headers = [
            col_data for col_data in self.all_headers
            if not requested_headers or col_data[0] in requested_headers
        ]
        self.rows = rows

    def sort(self, *sorting_columns: str) -> None:
        columns = [header[0] for header in self.all_headers]
        filtered_sorting_columns = [s for s in sorting_columns if s in columns]

        # pick first one by default
        if not filtered_sorting_columns:
            filtered_sorting_columns = [columns[0]]

        column_ids = [elt[0] for elt in self.all_headers]

        self.column_indices = [
            column_ids.index(sorting_column) for sorting_column in filtered_sorting_columns
        ]

        self.rows = [[NoneWrapper() if col is None else col for col in row] for row in self.rows]

        self.sorted_rows = sorted(
            self.rows, key=lambda x: [
                x[column_index] for column_index in self.column_indices
            ]
        )

        self.filter(self.sorted_rows)
        self.sorted_rows = self._format_datetime(self.sorted_rows)

    def filter(self, all_rows: list[list[Any]]) -> None:
        requested_indices = []
        filtered_rows: list[list[Any]] = []
        filtered_columns: list[tuple[str, str]] = []

        for column_data in self.all_headers:
            if column_data in self.requested_headers and column_data not in filtered_columns:
                filtered_columns.append(column_data)
                requested_indices += [self.all_headers.index(column_data)]

        for row in all_rows:
            filtered_rows.append([row[x] for x in requested_indices])

        self.filtered_columns_data, self.sorted_rows = filtered_columns, filtered_rows

    def output(self, output_format: str) -> Any:
        if output_format == "table":
            return self.make_pretty_table(self.filtered_columns_data, self.sorted_rows)

        if output_format == "csv":
            return self.make_csv_table(self.filtered_columns_data, self.sorted_rows)

        if output_format == "value":
            return self.make_value_output(self.filtered_columns_data, self.sorted_rows)
        if output_format == "yaml":
            return self.make_yaml_output(self.filtered_columns_data, self.sorted_rows)

        assert False, "output_format was of unrecognized format: %s" % (output_format)

    @staticmethod
    def make_pretty_table(columns: list[tuple[str, str]], data: list[list[Any]]) -> prettytable.PrettyTable:
        columns_names = [column[1] for column in columns]
        table = prettytable.PrettyTable(columns_names)
        table.align = "l"
        for row in data:
            table.add_row([cell if not isinstance(cell, FormatableData) else cell.table_data for cell in row])
        return table

    @staticmethod
    def make_csv_table(columns: list[tuple[str, str]], data: list[list[Any]]) -> str:
        columns_names = [column[1] for column in columns]
        csv_output = StringIO()
        csv_writer = csv.writer(csv_output)
        csv_writer.writerow(columns_names)
        csv_writer.writerows(
            [[cell if not isinstance(cell, FormatableData) else cell.csv_data for cell in row] for row in data]
        )

        return csv_output.getvalue()

    @staticmethod
    def make_value_output(columns: list[tuple[str, str]], data: list[list[Any]]) -> str:
        def escape(cell: Any) -> str:
            cell_str = str(cell)
            if " " in cell_str:
                cell_str = '"' + cell_str.replace('"', '\\"') + '"'
            elif cell_str == "":
                cell_str = '""'
            return cell_str

        def make_line(row: list[Any]) -> str:
            return " ".join(
                [escape(cell) if not isinstance(cell, FormatableData) else escape(cell.value_data)
                    for cell in row])

        lines = [make_line(row) for row in data]
        return "\n".join(lines)

    @staticmethod
    def make_yaml_output(columns: list[tuple[str, str]], data: list[list[Any]]) -> Any:
        results = []

        for row in data:
            results.append(
                {col[0]: str(cell) if not isinstance(cell, FormatableData) else cell.yaml_data
                    for col, cell in zip(columns, row)})

        output = {"results": results}
        return yaml.safe_dump(output, default_flow_style=False)

    @staticmethod
    def _format_datetime(rows: list[list[Any]]) -> list[list[Any]]:
        for i, row in enumerate(rows):
            for j, cell in enumerate(row):
                if isinstance(cell, datetime):
                    rows[i][j] = "{created} ({ago})".format(
                        created=format_datetime(rows[i][j]),
                        ago=get_datetime_ago(rows[i][j])
                    )
        return rows
