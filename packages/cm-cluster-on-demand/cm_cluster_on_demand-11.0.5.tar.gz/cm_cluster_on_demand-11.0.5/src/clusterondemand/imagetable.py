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

from collections.abc import Iterable
from datetime import datetime
from typing import TYPE_CHECKING, Any

from clusterondemand.codoutput.sortingutils import SortableData
from clusterondemand.utils import get_time_ago

if TYPE_CHECKING:
    from clusterondemand.images.find import CODImage


ALL_COLUMNS = [
    ("id_revision", "ImageID:Revision"),
    ("name", "Image name"),
    ("type", "Image type"),
    ("head_size", "Head(GB)"),
    ("node_size", "Node(GB)"),
    ("size", "Size(GB)"),
    ("image_size", "Image(GB)"),
    ("distro", "Distro"),
    ("cmd_revision", "CMD Rev."),
    ("bcm_version", "BCM Version"),
    ("arch", "Arch"),
    ("created_at", "Created"),
    ("uploaded_at", "Uploaded"),
    ("package_groups", "Packages"),
    ("is_public", "Public"),
    ("uuid", "UUID"),
    ("cloud_type", "Cloud Type"),
]

ADVANCED_COLUMNS = [
    "name", "type", "size", "distro", "cmd_revision", "bcm_version", "arch", "created_at", "uploaded_at",
    "package_groups", "is_public", "uuid", "cloud_type",
]

BASIC_COLUMNS = [
    "id_revision", "head_size", "node_size", "distro", "cmd_revision", "bcm_version", "arch", "created_at",
    "package_groups", "is_public"
]

USER_READABLE_IMAGE_TYPES = {
    "node": "Compute node",
    "headnode": "Head node",
    "node-installer": "Node installer",
    "edge-iso": "Edge ISO",
    "edge-director": "Edge Director",
}


def user_readable_image_type(image_type: str) -> str:
    return USER_READABLE_IMAGE_TYPES.get(image_type) or ""


def make_images_table(images: Iterable[CODImage | CODImageAdapter], sortby: list[str] | None = None,
                      columns: list[str] | None = None, output_format: str = "table") -> Any:
    sortby = sortby or []
    columns = columns or [column[0] for column in ALL_COLUMNS]
    rows = [
        [getattr(image, column[0], "N/A") for column in ALL_COLUMNS]
        for image in images
    ]

    table = SortableData(all_headers=ALL_COLUMNS, requested_headers=columns, rows=rows)
    table.sort(*sortby)
    return table.output(output_format=output_format)


def make_cod_images_table(cod_images: Iterable[CODImage], sortby: list[str] | None = None,
                          columns: list[str] | None = None, advanced: bool = False,
                          output_format: str = "table") -> Any:
    if not columns:
        columns = ADVANCED_COLUMNS if advanced else BASIC_COLUMNS

    return make_images_table(
        [CODImageAdapter(image, advanced) for image in cod_images],
        sortby=sortby,
        columns=columns,
        output_format=output_format
    )


class CODImageAdapter:
    """Adapter that maps every key in ALL_COLUMNS to a value of a COD Image."""

    def __init__(self, image: CODImage, advanced: bool = False) -> None:
        self.name = image.name
        if image.bcm_optional_info:
            self.id_revision = "{0.id}:{0.revision} ({0.bcm_optional_info})".format(image)
        else:
            self.id_revision = "{0.id}:{0.revision}".format(image)
        self.revision = image.revision

        if 0 == len(image.node_images):
            node_images_size = None
            compute_node_image_size = None
        else:
            node_images_size = sum(i.size for i in image.node_images)
            compute_node_image_size = next((i.size for i in image.node_images if i.type == "node"), None)
        self.size = GigabyteSize(image.size + (node_images_size or 0))
        self.head_size = GigabyteSize(image.size)
        self.node_size = GigabyteSize(compute_node_image_size)
        self.image_size = GigabyteSize(image.size)  # used when we don't want to use "head_size" column name
        # for "flattened" images that may not be the headnode

        self.distro = image.distro
        self.cmd_revision = image.cmd_revision
        self.bcm_version = image.version
        self.arch = image.arch or None
        self.created_at = RelativeDateTime(image.created_at) if image.created_at else None
        self.uploaded_at = RelativeDateTime(image.uploaded_at) if image.uploaded_at else None
        self.package_groups = ",".join(image.package_groups)
        self.is_public = image.image_visibility == "public"
        self.uuid = image.uuid
        self.cloud_type = image.cloud_type

        image_types = [image.type]
        if not advanced:
            # In the non-advanced we show the image sets, so we put all the types here
            image_types += [node_image.type for node_image in image.node_images]
        self.type = ", ".join(user_readable_image_type(t) for t in image_types)


class GigabyteSize:
    """Utility class that allows both sorting by value while still giving the value a custom string representation."""

    N_BYTES_PER_GB = 1024 ** 3

    def __init__(self, bytes: int | None) -> None:
        self.bytes = bytes

    def __lt__(self, other: Any) -> bool:
        if not isinstance(other, GigabyteSize):
            return False
        if other.bytes is None:
            return False
        return self.bytes is None or self.bytes < other.bytes

    def __str__(self) -> str:
        if self.bytes is None:
            return "N/A"

        return str(round(self.bytes / GigabyteSize.N_BYTES_PER_GB, 2))


class RelativeDateTime:
    """Utility class that allows both sorting by value while still giving the value a custom string representation."""

    def __init__(self, time: datetime) -> None:
        self.time = time

    def __lt__(self, other: Any) -> bool:
        return isinstance(other, RelativeDateTime) and self.time < other.time

    def __str__(self) -> str:
        return get_time_ago(self.time) + " ago" if self.time else "N/A"
