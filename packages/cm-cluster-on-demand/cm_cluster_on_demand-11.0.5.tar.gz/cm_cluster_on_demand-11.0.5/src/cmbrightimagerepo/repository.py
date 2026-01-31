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

from collections.abc import Iterable, Iterator
from itertools import chain
from logging import getLogger
from typing import Any, Callable
from urllib.request import urlopen

import yaml

from .image import Image

log = getLogger("cluster-on-demand")


class ManifestVersionMismatch(Exception):
    def __init__(self, version: int) -> None:
        super().__init__(
            "Version %d is not supported.", version
        )


class Repository:
    """
    Image repository object.

    That class represents image repo list of version 1.
    """

    @classmethod
    def read_manifest_file(cls, manifest_url: str) -> Any:
        yaml_stream = urlopen(manifest_url)
        assert manifest_url
        try:
            return yaml.safe_load(yaml_stream)
        finally:
            yaml_stream.close()

    @classmethod
    def bootstrap_manifest(cls) -> dict[str, Any]:
        return {"version": 1}

    @classmethod
    def add_image(cls, repo_data: dict[str, Any], image_data: dict[str, Any]) -> dict[str, Any]:
        images = repo_data.get("images", [])
        images.append(image_data)
        repo_data["images"] = images
        return repo_data

    @classmethod
    def make_copy_override(cls, source_repo: Repository,
                           images: Iterable[Image] | None = None,
                           image_descriptions: list[dict[str, Any]] | None = None,
                           links: list[str] | None = None,
                           resolve_link_func: Callable[[Any], Repository] | None = None,
                           baseurl: str | None = None) -> Repository:
        return cls(
            images=image_descriptions or
            [img.raw_description() for img in images] if images is not None else
            source_repo._images,

            links=links or source_repo._links,
            resolve_link_func=resolve_link_func or source_repo._resolve_link,
            baseurl=baseurl or source_repo._baseurl
        )

    @classmethod
    def make_from_data(cls, data: dict[str, Any], baseurl: str | None = None) -> Repository:
        if data["version"] != 1:
            raise ManifestVersionMismatch(data["version"])

        return cls(data.get("images", []),
                   data.get("links", []),
                   cls.make_from_url,
                   baseurl)

    @classmethod
    def make_from_url(cls, manifest_url: str) -> Repository:
        """Create an object using the manifest file located by URL."""
        data = cls.read_manifest_file(manifest_url)

        return cls.make_from_data(data, manifest_url)

    def __init__(self, images: list[dict[str, Any]], links: list[Any], resolve_link_func: Callable[[Any], Repository],
                 baseurl: str | None) -> None:
        """
        Construct an object.

        images - list of images
        links - list of objects that refer other repo sources
        resolve_link_func - function that accepts link as an argument and returns a Repository
        object
        """
        self._images = images
        self._links = links
        self._resolve_link = resolve_link_func
        self._baseurl = baseurl

    def raw_data(self) -> dict[str, Any]:
        return {"version": 1,
                "images": self._images,
                "links": self._links}

    def repos_iter(self) -> Iterator[Repository]:
        """Recursive iterate over all linked repos, including current."""
        yield self
        for link in self._links:
            repo = self._resolve_link(link)
            yield from repo.repos_iter()

    def image_descriptions(self) -> list[dict[str, Any]]:
        return self._images

    def images_noraise(self) -> Iterator[Image]:
        return (img for img in
                (Image.make_from_descripton_noraise(descr, self._baseurl) for descr in
                 self.image_descriptions())
                if img is not None)

    def images_rec_noraise(self) -> chain[Image]:
        return chain.from_iterable(
            one_repo.images_noraise() for one_repo in self.repos_iter()
        )

    def images(self) -> Iterator[Image]:
        return (Image.make_from_descripton(descr, self._baseurl)
                for descr in self.image_descriptions())
