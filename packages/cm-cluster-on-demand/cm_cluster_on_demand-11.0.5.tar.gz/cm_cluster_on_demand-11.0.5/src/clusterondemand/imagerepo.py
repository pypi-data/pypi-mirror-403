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
from collections.abc import Iterator
from datetime import datetime
from typing import Any

import pytz

from clusterondemand.images.find import CODImage, ImageSource
from clusterondemandconfig import ConfigNamespace, config
from clusterondemandconfig.configuration import ConfigurationView
from cmbrightimagerepo.image import Image
from cmbrightimagerepo.repository import Repository

imagerepo_ns = ConfigNamespace("imagerepo", help_section="image repository parameters")
imagerepo_ns.add_parameter(
    "root_manifest",
    advanced=True,
    default="http://support.brightcomputing.com/imagerepo/repo.yaml",
    help_varname="URL",
    help="URL to the image repository yaml manifest"
)


class RepoImageSource(ImageSource):
    def __init__(self, root_manifest: str | None = None, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        if root_manifest is None:
            self.root_manifest = config["root_manifest"]
        else:
            self.root_manifest = root_manifest
        assert not self.uuids

    @classmethod
    def from_config(cls, config: ConfigurationView, ids: list[str] | None = None) -> RepoImageSource:
        return RepoImageSource(
            ids=ids if ids is not None else config["ids"],
            root_manifest=config["root_manifest"],
            tags=config["tags"],
            version=config["version"],
            arch=config["arch"],
            distro=config["distro"],
            package_groups=config["package_groups"],
            revision=config["revision"],
            status=config["status"],
            advanced=config["advanced"],
            image_visibility=config["image_visibility"],
            cloud_type=config["cloud_type"],
        )

    def _iter_from_source(self) -> Iterator[CODImage]:
        assert self.root_manifest
        repo = Repository.make_from_url(self.root_manifest)
        images = repo.images_rec_noraise()
        return (
            make_cod_image_from_repo(image)
            for image in images
        )


def repo_image_name(image: Image) -> str:
    image_type = image.image_type()
    if image_type == "headnode":
        prefix = "bcmh"
    elif image_type == "node":
        prefix = "bcmn"
    elif image_type == "node-installer":
        prefix = "bcni"
    elif image_type == "edge-iso":
        prefix = "bcm-ni-edge"
    elif image_type == "edge-director":
        prefix = "bcm-di-edge"
    else:
        raise Exception("Unsupported image type %s" % (image_type))
    return "{}-{}-{}".format(
        prefix,
        image.id(),
        image.revision()
    )


class RepoImage(CODImage):

    def __init__(self, image: Image):
        # Remove everything after first digit
        # Same logic as in build-cod-image.sh
        distro_family = re.sub(r"\d.*", "", image.os())

        super().__init__(
            bcm_optional_info=None,
            cloud_type=image.cloud_type(),
            cmd_revision=image.cmd_revision(),
            created_at=datetime.fromtimestamp(image.created_at(), pytz.utc),
            distro=image.os(),
            distro_family=distro_family,
            arch=image.arch(),
            id=image.id(),
            name=repo_image_name(image),
            image_visibility="public",
            revision=image.revision(),
            size=image.size(),
            tags=image.tags(),
            type=image.image_type(),
            uploaded_at=None,
            uuid="N/A",
            version=str(image.bcm_version()),
            package_groups=sorted(image.package_groups()),
        )
        self.repo_image = image


def make_cod_image_from_repo(image: Image) -> RepoImage:
    return RepoImage(image)
