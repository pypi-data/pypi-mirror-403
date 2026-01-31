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
from logging import getLogger

from clusterondemandconfig.configuration import ConfigurationView
from clusterondemandconfig.parameter import Parameter

from .exceptions import ValidationException
from .utils import MAX_CLUSTER_NAME_LENGTH, is_valid_cluster_name

# GCP does not support periods in image names so modified _BCM_VERSION_REGEX to match both '.' and '-'
# in version. e.g. '10.0' and '11-0'
UUID_REGEX = "^[0-9a-fA-F]{8}(-[0-9a-f]{4}){3}-[0-9a-f]{12}$"
PRODUCT_KEY_REGEX = "^[0-9]{6}(-[0-9]{6}){4}$"
_IMAGE_NAME_REGEX = r"[^-]+"
_BCM_VERSION_REGEX = r"(?:trunk|\d+[.-]\d+)(?:-[a-z-]+[a-z])?"
_IMAGE_REVISION_REGEX = r"\d+"
VALID_IMAGE_REGEX = r"^(?!bcmn|bcmh)%s-%s:%s$" % (_IMAGE_NAME_REGEX, _BCM_VERSION_REGEX, _IMAGE_REVISION_REGEX)
VALID_HEADNODE_IMAGE_REGEX = r"^bcmh-%s-%s-%s$" % (_IMAGE_NAME_REGEX, _BCM_VERSION_REGEX, _IMAGE_REVISION_REGEX)
VALID_NODE_IMAGE_REGEX = r"^bcmn-%s-%s-%s$" % (_IMAGE_NAME_REGEX, _BCM_VERSION_REGEX, _IMAGE_REVISION_REGEX)

log = getLogger("cluster-on-demand")


# TODO Get rid of this class and put in functions?
# There is no point in having a class with only static methods
class ParamValidator:

    @staticmethod
    def validate_cluster_name(cluster_name: str, validate_max_name_len: bool) -> None:
        max_name_length = MAX_CLUSTER_NAME_LENGTH

        if not validate_max_name_len:
            max_name_length = 999

        if not is_valid_cluster_name(cluster_name, max_name_length):
            raise ValidationException(
                f"The cluster name '{cluster_name}' does not match the proper format. "
                f"The cluster name cannot exceed {max_name_length} characters in length and "
                f"should be a valid hostname as specified by RFC952 and RFC1123. "
                f"'--no-validate-max-cluster-name-length' will override the length requirement."
            )

    @staticmethod
    def validate_uuid_format(uuid_string: str, error_message: str = "") -> None:
        if not error_message:
            error_message = f"{uuid_string} is not a valid UUID"

        if not bool(re.match(UUID_REGEX, uuid_string)):
            raise ValidationException(error_message)


def validate_image_value(parameter: Parameter, config: ConfigurationView) -> None:
    value = config[parameter.key]
    if value and not re.match(VALID_IMAGE_REGEX, value):
        log.warning(f"'{value}' does not seem to be a valid image. "
                    "Expected format <distro>-<bcm version>:<n>, e.g. 'ubuntu1604-trunk:13'")


def validate_headnode_image_value(parameter: Parameter, config: ConfigurationView) -> None:
    value = config[parameter.key]
    if value and not re.match(VALID_HEADNODE_IMAGE_REGEX, value) and not re.match(VALID_IMAGE_REGEX, value):
        log.warning(f"'{value}' does not seem to be a valid head node image. "
                    "Expected format bcmh-<distro>-<bcm version>-<n>, e.g. 'bcmh-ubuntu1604-trunk-13' OR "
                    "<distro>-<bcm version>:<n>, e.g. 'ubuntu1604-trunk:13'")


def validate_node_image_value(parameter: Parameter, config: ConfigurationView) -> None:
    value = config[parameter.key]
    if value and not re.match(VALID_NODE_IMAGE_REGEX, value) and not re.match(VALID_IMAGE_REGEX, value):
        log.warning(f"'{value}' does not seem to be a valid node image. "
                    "Expected format bcmn-<distro>-<bcm version>-<n>, e.g. 'bcmn-ubuntu1604-trunk-13' OR "
                    "<distro>-<bcm version>:<n>, e.g. 'ubuntu1604-trunk:13'")


def warn_user_about_cluster_name_length(parameter: Parameter, configuration: ConfigurationView) -> None:
    item = configuration.get_item_for_key(parameter.name)
    if not item.value:
        log.warning("--no-validate-max-cluster-name-length was supplied. This may lead to certificate "
                    "generation failure or various other issues.")


def handle_revision_conflict(parameter: Parameter, configuration: ConfigurationView) -> None:
    all_revisions = configuration.get_item_for_key(parameter.name)
    latest = configuration.get_item_for_key("latest")
    if all_revisions.value and latest.value:
        log.info(
            f"Overlapping parameters detected: Both '--all-revisions' and '--latest {latest.value}' were supplied. "
            "Finding all available image revisions, since '--all-revisions' takes precedence ignoring the "
            "'--latest' setting."
        )
        latest.value = None
