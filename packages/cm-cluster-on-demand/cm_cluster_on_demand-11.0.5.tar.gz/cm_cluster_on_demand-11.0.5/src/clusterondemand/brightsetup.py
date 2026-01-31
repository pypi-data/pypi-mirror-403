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
from datetime import datetime, timezone
from typing import Any

from passlib.hash import sha512_crypt

from clusterondemand.bcm_version import BcmVersion
from clusterondemand.images.find import CODImage
from clusterondemand.versioned_product_key import resolve_versioned_product_key_from_config
from clusterondemandconfig import config

log = logging.getLogger("cluster-on-demand")

_USE_PASSWORD_HASH_AFTER = datetime(2024, 8, 25, tzinfo=timezone.utc)


def use_password_hash(head_node_image: CODImage) -> bool:
    if not head_node_image.version:
        return False
    version = BcmVersion(head_node_image.version)
    return version.release > (10, 0) or (
        version.release == (10, 0)
        and head_node_image.created_at is not None
        and head_node_image.created_at >= _USE_PASSWORD_HASH_AFTER
    )


def get_license_dict(name: str | None = None) -> dict[str, str]:
    license_dict = {
        "cluster_name": str(name if name else config["name"]),
        "unit": str(config["license_unit"]),
        "locality": str(config["license_locality"]),
        "country": str(config["license_country"]),
        "product_key": resolve_versioned_product_key_from_config(config),
        "state": str(config["license_state"]),
        "organization": str(config["license_organization"])
    }
    # COD images older than 8.1-11 will break because of unrecognized "license_activation_token"
    # configuration key. To prevent it, don't pass it unless it was specified.
    if config["license_activation_token"]:
        license_dict["activation_token"] = str(config["license_activation_token"])
        if config["license_activation_url"]:
            license_dict["activation_url"] = str(config["license_activation_url"])
    return license_dict


def generate_bright_setup(cloud_type: str,
                          wlm: str,
                          license_dict: dict[str, str],
                          hostname: str,
                          head_node_image: CODImage,
                          node_count: int,
                          timezone: str,
                          admin_email: str | None = None,
                          node_disk_setup_path: str | None = None,
                          node_kernel_modules: list[str] | None = None) -> dict[str, Any]:
    brightsetup: dict[str, Any] = {
        "cloud_type": cloud_type,
        "bright": {
            "wlm": wlm,
            "wlm_slot_count": "AUTO" if BcmVersion(config["version"]) > "9.1" else 1,
            # None   type gets translated to 'None' string somewhere,
            # that's why need need empty string here for pbsproc_lic_server
            "pbspro_lic_server": "",
            "license": license_dict,
            "hostname": str(hostname),  # otherwise it will end up as unicode:  u"xxxx"
            "master_compute_node": False,
            "node_count": node_count
        },
    }
    if config["healthchecks_to_disable"]:
        brightsetup["bright"]["healthchecks_to_disable"] = config["healthchecks_to_disable"]
    if use_password_hash(head_node_image):
        brightsetup["bright"]["password_hash"] = sha512_crypt.hash(config["cluster_password"])
    else:
        brightsetup["bright"]["password"] = config["cluster_password"]

    if node_kernel_modules:
        brightsetup["bright"]["node_kernel_modules"] = node_kernel_modules
    else:
        # TODO:fixme: CM-9026 otherwise somehow the default config value does not kick in
        # (we get key error)
        brightsetup["bright"]["node_kernel_modules"] = []
    if node_disk_setup_path:
        brightsetup["bright"]["node_disk_setup_path"] = node_disk_setup_path
    else:
        # TODO:fixme: CM-9026 otherwise somehow the default config value does not kick in
        # (we get key error)
        brightsetup["bright"]["node_disk_setup_path"] = ""
    if timezone:
        brightsetup["bright"]["timezone"] = timezone
    if admin_email:
        brightsetup["bright"]["admin_email"] = admin_email

    if BcmVersion(config["version"]) > "8.1" and config["http_proxy"] is not None:
        brightsetup["bright"]["http_proxy"] = config["http_proxy"]
    elif config["http_proxy"] is not None:
        log.warning("http_proxy is not supported for versions prior to 8.2.")

    return {
        "modules": {
            "brightsetup": brightsetup
        }
    }
