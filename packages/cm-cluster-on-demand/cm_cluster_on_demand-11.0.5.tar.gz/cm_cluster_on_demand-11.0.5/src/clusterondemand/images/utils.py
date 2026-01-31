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
from itertools import chain

from clusterondemand.images.find import CODImage


def flatten_images(images: Iterable[CODImage], nodes_first: bool = True) -> chain[CODImage]:
    def iter_images(cod_image: CODImage) -> chain[CODImage]:
        if nodes_first:
            return chain(cod_image.node_images, [cod_image])

        return chain([cod_image], cod_image.node_images)
    return chain.from_iterable(iter_images(image) for image in images)
