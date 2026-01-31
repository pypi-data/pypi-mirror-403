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

import re
from copy import deepcopy
from logging import getLogger
from typing import Any, cast
from urllib.parse import urljoin

log = getLogger("cluster-on-demand")


class ImageDescriptionVersionMismatchError(Exception):
    """Version of the description object is not supported."""

    def __init__(self, version: int) -> None:
        super().__init__(
            "Version %s of image description is not supported", version
        )


class Image:
    """Image description object.

    It can be constructed from the description returned from Repository.
    """

    @classmethod
    def make_from_descripton(cls, descr: dict[str, Any], baseurl: str | None) -> Image:
        """Create image object from descr object."""
        if descr["version"] != 1:
            raise ImageDescriptionVersionMismatchError(descr["version"])

        if baseurl is not None:
            descr = deepcopy(descr)
            descr["url"] = urljoin(baseurl, descr["url"])
        return cls(descr)

    @classmethod
    def make_from_descripton_noraise(cls, descr: dict[str, Any], baseurl: str | None) -> Image | None:
        """Create image object from descr object."""
        try:
            return cls.make_from_descripton(descr, baseurl)
        except Exception as e:
            log.warning("Could not parse image description %s: %s", descr, e)
            return None

    @classmethod
    def bootstrap_image(cls,
                        id: str,
                        url: str,
                        tags: list[str],
                        package_groups: list[str],
                        bcm_version: str,
                        bcm_release: int,
                        image_type: str,
                        os: str,
                        revision: int,
                        cmd_revision: int,
                        created_at: int,
                        cloud_type: str,
                        arch: str) -> Image:
        return cls.make_from_descripton({
            "version": 1,
            "id": id,
            "url": url,
            "tags": tags,
            "package_groups": package_groups,
            "bcm_version": bcm_version,
            "bcm_release": bcm_release,
            "image_type": image_type,
            "arch": arch,
            "os": os,
            "revision": revision,
            "cmd_revision": cmd_revision,
            "created_at": created_at,
            "cloud_type": cloud_type,
        }, baseurl=None)

    def uncompressed_image_info_missing(self) -> bool:
        return self._description.get("uncompressed_size") is None

    def image_info_missing(self) -> bool:
        return self._description.get("size") is None or \
            self._description.get("md5sum") is None

    def set_uncompressed_image_info(self, uncompressed_size: int) -> None:
        self._description["uncompressed_size"] = uncompressed_size

    def set_image_info(self, size: int, md5sum: str) -> None:
        self._description["size"] = size
        self._description["md5sum"] = md5sum

    def __init__(self, description: dict[str, Any]) -> None:
        self._description = description

    def raw_description(self) -> dict[str, Any]:
        return self._description

    def id(self) -> str:
        """Return unique string across the repo."""
        return cast(str, self._description["id"])

    def url(self) -> str:
        """Return URL of the image file."""
        return cast(str, self._description["url"])

    def md5sum(self) -> str:
        """Return MD5 checksum of the image file."""
        return cast(str, self._description["md5sum"])

    def size(self) -> int:
        """Size of the image file in bytes."""
        return cast(int, self._description["size"])

    def uncompressed_size(self) -> int:
        return cast(int, self._description["uncompressed_size"])

    def bcm_version(self) -> str:
        """Bright version installed to the image."""
        return cast(str, self._description["bcm_version"])

    def bcm_release(self) -> int:
        """Bright release installed to the image."""
        return cast(int, self._description.get("bcm_release", 0))

    def image_type(self) -> str:
        """Type of bcm image."""
        return cast(str, self._description["image_type"])

    def arch(self) -> str:
        return cast(str, self._description.get("arch") or "x86_64")

    def os(self) -> str:
        """Operating system of the image."""
        return cast(str, self._description["os"])

    def revision(self) -> int:
        """Image revision."""
        return cast(int, self._description["revision"])

    def created_at(self) -> int:
        """Image creation timestamp."""
        return cast(int, self._description["created_at"])

    def cmd_revision(self) -> int:
        """Return CMDaemon revision installed in the image."""
        return cast(int, self._description["cmd_revision"])

    def cloud_type(self) -> str:
        """Cloud type this image was created for."""
        return cast(str, self._description["cloud_type"])

    def distro_family(self) -> str:
        """Distro family, centos7u9 > centos. Same logic as in build-cod-image.sh"""
        return re.sub(r"\d.*", "", self.os())

    """
    Not all images must have the following attributes, therefore they are not mandatory
    We allow them to be empty and don't verify in completed() function below.
    This allows manipulation on images with some attributes missing, E.g installing the image without
    "bcm_edge_head_node_private_key"
    """

    def tags(self) -> list[str]:
        """Return tags of the image."""
        return cast(list[str], self._description.get("tags", []))

    def bcm_optional_info(self) -> str:
        """Maps public release no. (E.g: 9.1-9) to COD image."""
        return cast(str, self._description.get("bcm_optional_info", ""))

    def bcm_api_hash(self) -> str:
        """CMD API version hash, used by API client such as pythoncm."""
        return cast(str, self._description.get("bcm_api_hash", ""))

    def bcm_edge_head_node_private_key(self) -> str | None:
        """Private key for edge director image"""
        return cast(str, self._description.get("bcm_edge_head_node_private_key"))

    def bcm_edge_head_node_public_key(self) -> str | None:
        """Public key for edge director image"""
        return cast(str, self._description.get("bcm_edge_head_node_public_key"))

    def bcm_pkg_hashes(self) -> str:
        """List of hashes of cmd, cm-setup and cluster tools."""
        return cast(str, self._description.get("bcm_pkg_hashes", ""))

    def package_groups(self) -> list[str]:
        """Return package groups preinstalled to the image."""
        return cast(list[str], self._description.get("package_groups", []))

    def head_node_swap_interfaces(self) -> bool | None:
        """Whether to swap interfaces on the head node."""
        return cast(bool, self._description.get("head_node_swap_interfaces"))

    def completed(self) -> bool:
        """Object is consistent and contains all necessary information."""
        def _check_key(key: str) -> bool:
            return self._description.get(key) is not None

        # "arch" is not included to support old manifests.
        keys = [
            "id",
            "url",
            "tags",
            "md5sum",
            "size",
            "uncompressed_size",
            "package_groups",
            "bcm_version",
            "image_type",
            "os",
            "revision",
            "created_at",
            "cmd_revision",
            "version",
            "cloud_type",
        ]
        for key in keys:
            if not _check_key(key):
                return False

        return True
