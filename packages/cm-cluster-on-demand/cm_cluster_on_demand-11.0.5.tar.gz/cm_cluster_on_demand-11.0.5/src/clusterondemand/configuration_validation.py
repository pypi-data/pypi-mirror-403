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

from clusterondemandconfig import ConfigLoadError
from clusterondemandconfig.config_namespace import ConfigNamespace
from clusterondemandconfig.configuration import ConfigurationView
from clusterondemandconfig.parameter import Parameter

from .clustercreate import generate_random_cluster_password

log = logging.getLogger("cluster-on-demand")


def is_ssh_key_specified(configuration: ConfigurationView) -> bool:
    # Depending on the COD implementation there are two different types of ssh keys that can be provided
    # via the CLI. Because their existence depends on the implementation we might run into KeyErrors.
    for argument in ["ssh_key_pair", "ssh_pub_key_path"]:
        try:
            if configuration.get_item_for_key(argument).value:
                return True
        except KeyError:
            continue
    return False


def validate_access_to_cluster(namespace: ConfigNamespace, configuration: ConfigurationView) -> None:
    if is_ssh_key_specified(configuration):
        return

    cluster_password = configuration.get_item_for_key("cluster_password").value
    ssh_password_authentication = configuration.get_item_for_key("ssh_password_authentication").value
    log_cluster_password = configuration.get_item_for_key("log_cluster_password").value

    if ssh_password_authentication and (cluster_password or log_cluster_password):
        return

    # We need a way to bypass the validation, as the user might have deliver the SSH key
    # to their cluster in some other way.
    if not configuration.get_item_for_key("access_validation").value:
        log.info("Skipping cluster access validation due to '--no-access-validation' being set.")
        return

    raise ConfigLoadError(
        "Refusing to create the cluster, access to it would not be possible. "
        "Please specify either the SSH key (see --help), or "
        "'--ssh-password-authentication true' alongside either "
        "'--cluster-password <your_password>' or '--log-cluster-password' (to be able to see "
        "the randomly generated password). You can also use "
        "'--no-access-validation' to skip this check. "
        "Run with '--show-configuration' to see exactly which values have been set.")


def generate_password_if_not_set(parameter: Parameter, configuration: ConfigurationView) -> None:
    password = configuration.get_item_for_key(parameter.key)
    log_cluster_password = configuration.get_item_for_key("log_cluster_password").value

    if password.value:
        return

    password.value = generate_random_cluster_password(length=24)
    text = "No custom cluster password specified. Using a random password."
    if log_cluster_password:
        text += f" Password: '{password.value}'"
    else:
        text += (
            " Use --log-cluster-password to see it."
            " If you are going to use the Bright View you have to change this password"
            " by using cm-change-passwd script (change root password of head node) or"
            " simply 'passwd root' command. If this cluster has a high-availability setup"
            " with 2 head nodes, be sure to change the password on both head nodes."
        )

    log.info(text)


def validate_password_strength(parameter: Parameter, configuration: ConfigurationView) -> None:
    # a password is defined to be weak if any of the following conditions hold:
    # 1. it is 8 or fewer characters long or;
    # 2. it does not contain a digit or;
    # 3. it does not contain an upper-case letter;
    def is_weak_password(s: str) -> bool:
        return (len(s) <= 8 or
                all(str(n) not in s for n in range(10)) or
                all(chr(65 + a) not in s for a in range(26)))

    password = configuration.get_item_for_key(parameter.key).value
    password_policy = configuration["weak_password_policy"]

    # If the password is not set we can skip the validation.
    if not password:
        return

    if is_weak_password(password):
        if password_policy == "allow":
            return

        if password_policy == "warn":
            log.warning("The password you entered is not strong enough, "
                        "and it is being used in conjunction with enabled "
                        "SSH password authentication! Please consider "
                        "using a stronger password, or disabling SSH "
                        "password authentication. This warning can be "
                        "disabled by altering the weak password policy.")
            return

        if password_policy == "fail":
            raise ConfigLoadError("The password you entered is not strong enough! "
                                  "Current configuration forbids weak passwords "
                                  "in conjunction with enabled SSH password authentication. "
                                  "Use a stronger password, or disable SSH password "
                                  "authentication. A strong password must contain "
                                  "9 or more characters, out of which at least one "
                                  "is a number, and at least one is an upper-case letter.")
        raise ConfigLoadError(f"Could not determine the password policy {password_policy}. "
                              "--weak_password_policy is not one of: allow, warn, fail.")
