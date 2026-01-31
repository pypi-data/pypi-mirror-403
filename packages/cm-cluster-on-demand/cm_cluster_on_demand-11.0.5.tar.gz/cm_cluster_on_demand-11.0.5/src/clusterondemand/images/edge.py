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

import enum

from .distro_family import parse_distro_string

_DISTRO_ID_LIKE = {
    "rhel": ["alma", "almacentos", "centos", "redhat", "rhel", "rocky", "rockycentos", "sl"],
    "sles": ["suse", "sles"],
    "ubuntu": ["ubuntu"],
}


def distro_family(distro: str) -> str:
    """
    Determine the distribution family of the given 'distro' string.

    This function searches for the distribution family in the predefined _DISTRO_ID_LIKE dict
    If no match is found, it returns the input 'distro' string as is.

    Parameters:
        distro (str): The input distro string for which the distribution family is to be determined.

    Returns:
        str: The distribution family of the input 'distro' string.
    """
    return next(iter(
        family
        for family, distros in _DISTRO_ID_LIKE.items()
        if distro in distros
    ), distro)


class _DefaultEdgeDirectorInterfaces(enum.Enum):
    rhel7 = ('eth0', 'eth1')
    rhel8 = ('ens3', 'ens4')
    rhel9 = ('ens3', 'ens4')
    ubuntu20 = ('ens3', 'ens4')
    ubuntu22 = ('ens3', 'ens4')
    _default = ('eth0', 'eth1')

    @classmethod
    def for_distro_and_major(kls, distro_id_and_major: str) -> '_DefaultEdgeDirectorInterfaces':
        return getattr(kls, distro_id_and_major, kls._default)


def get_default_director_edge_interfaces(distro: str) -> tuple[str, str]:
    """
    Get the default edge director interfaces for the given distribution.

    This function uses the 'distro' string to retrieve the default edge director interfaces
    from the predefined _DefaultEdgeDirectorInterfaces enum class.
    If no value is defined, the values (eth0, eht1) are returned.

    Parameters:
        distro (str): The input distribution string.

    Returns:
        tuple[str, str]: A tuple containing the default external network and internal network interface names.
    """
    name, major, _ = parse_distro_string(distro)
    family_and_major = f"{distro_family(name)}{major}"
    default = _DefaultEdgeDirectorInterfaces.for_distro_and_major(family_and_major)
    return default.value
