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

import logging
import re

from clusterondemand.bcm_version import BcmVersion
from clusterondemand.exceptions import CODException, ValidationException
from clusterondemandconfig.configuration.configuration_view import ConfigurationView
from clusterondemandconfig.parameter.parameter import Parameter

""" Break down of the regex:
(?P<operator>[<>]=?)? This part tries to find an optional operator (eg <=), which is then followed by
(?P<version>[^:]+): to match a version and trailing colon.
The ? at the end ((?P<operator>[<>]=?)?(?P<version>[^:]+):)? makes of whole combination of
(operator) + version + : optional. (?P<key>[0-9]{6}(-[0-9]{6}){4}) Matches the actual product key.

Examples of valid keys:
111111-222222-333333-444444-555555 (No version given, will match any version)
10.0-dev:111111-222222-333333-444444-555555 (Will be used if the version is 10.0-dev)
<10.0:111111-222222-333333-444444-555555 (Will be used for any version below 10.0)
>=11.0:111111-222222-333333-444444-555555 (Will be used for 11.0 or higher)
"""
VERSIONED_PRODUCT_KEY_REGEX = (
    r"^((?P<operator>[<>]=?)?(?P<version>[^:]+):)?(?P<key>[0-9]{6}(-[0-9]{6}){4})$"
)

log = logging.getLogger("cluster-on-demand")


class VersionedProductKey:
    def __init__(self, versioned_product_key: str) -> None:
        # config framework doesn't handle exceptions in constructor well, store errors for use in validation function
        self.validation_error = None

        if not (m := re.match(VERSIONED_PRODUCT_KEY_REGEX, versioned_product_key)):
            self.validation_error = f"This is not a valid versioned product key: {versioned_product_key}"
            return

        try:
            self.version = BcmVersion(m.group("version")) if m.group("version") else None
        except CODException as e:
            self.validation_error = f"Productkey {versioned_product_key} does not contain a valid BCM version. {str(e)}"
            return
        self.operator = m.group("operator") or "=="
        self.key = m.group("key")
        self.original_str = versioned_product_key

        log.debug(f"Key operator: {self.operator}, version: {self.version}, key: {self.key}")

    def __str__(self) -> str:
        return self.original_str

    def match(self, version: BcmVersion) -> bool:
        if not self.version:
            # plain key always matches
            return True

        assert self.operator in ["==", "<", ">", "<=", ">="]
        expression = f"image_version {self.operator} key_version"
        return bool(eval(expression, {"image_version": version, "key_version": self.version}))


def validate_product_key_list(parameter: Parameter, config: ConfigurationView) -> None:
    # First we check if any of the supplied keys had parsing errors when creating the objects
    validation_errors = " ".join([key.validation_error for key in config[parameter.key] if key.validation_error])
    if validation_errors:
        raise ValidationException(validation_errors)

    # And then we make sure that there is a key for the requested BCM version
    resolve_versioned_product_key_from_config(config)


def resolve_versioned_product_key_from_config(config: ConfigurationView) -> str:
    # Note: this function is called both from parameter validation in validate_product_key_list(),
    # as well as when inserting the product key into cm-bright-setup.conf
    try:
        version = BcmVersion(config["version"])
    except CODException as e:
        raise ValidationException(str(e))

    for product_key_from_config in config["license_product_key"]:
        if product_key_from_config.match(version):
            log.debug(f"Using product key: {product_key_from_config}")
            return str(product_key_from_config.key)
        log.debug(f"Not using product key: {product_key_from_config}")

    raise ValidationException(f"Config has no product key for version {version}.")
