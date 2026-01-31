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

import http.client as httplib
import logging
import os
import re
from urllib.parse import urlparse

import requests

from clusterondemand.bcm_version import BcmVersion
from clusterondemand.configuration import (
    DEFAULT_DISK_SETUP,
    DEFAULT_DISK_SETUP_10_AND_ABOVE,
    OS_DEFAULT_NODE_DISK_SETUP_11_AND_ABOVE
)
from clusterondemand.const import BASIC_SERVICES
from clusterondemand.copyfile import copy_file_set_version, fill_env_variables
from clusterondemand.exceptions import CODException
from clusterondemandconfig import config

from . import CloudConfig

log = logging.getLogger("cluster-on-demand")

CMD_READY_PROBE_PATH = "/root/cm/cmd_ready"
CMD_READY_PROBE_TEMPLATE = """\
#!/bin/bash
date
echo "Waiting for CMDaemon on `hostname` to update configuration files and start services..."
if [ "$(curl -m 61 -s -o /dev/null -w %{{http_code}} http://localhost:8080/ready?wait=60\\&version=query)" == "404" ]; then
    echo "The CMDaemon on `hostname` doesn't support the ready service. Will wait for 30 seconds to allow CMDaemon to set up base services."
    sleep 30
    echo "Done, will assume CMDaemon on `hostname` is ready."
    exit 0
fi
# CM-42419, We check the ready version of cmd, write it into tmp file.
# Later the version is used to make decision which endpoint to call
while [ "$(curl -m 61 -s -o /tmp/ready_version -w %{{http_code}} http://localhost:8080/ready?wait=60\\&version=query)" != "200" ]; do
    date
    echo "CMDaemon on `hostname` is not ready yet. Will wait some more..."
    sleep 3
done
if [ "$(cat /tmp/ready_version)" == "ready" ]; then
    curl_url="http://localhost:8080/ready?wait=60&name={service_list}"
elif [ "$(cat /tmp/ready_version)" == "v2" ]; then
    curl_url="http://localhost:8080/ready?wait=60&name=cod"
else
    echo "Querying ready service version returned unexpected response: "
    echo "$(cat /tmp/ready_version)"
    exit 1
fi
while [ "$(curl -m 61 -s -o /dev/null -w %{{http_code}} $curl_url)" != "200" ]; do
    date
    echo "Services on `hostname` are not ready yet. Will wait some more..."
    sleep 3
done
date
echo "CMDaemon on `hostname` is ready."
"""  # noqa: E501,W605

REMOTE_NODE_DISK_SETUP_PATH = "/root/cm/node-disk-setup.xml"
URL_REGEX = r"^http\:\/\/.*"


# When nodes are created from an image, the resulting root file-system
# will typically have the size of the image. We inject this script to
# grow the file-system to span the entire disk. This is done by finding
# any disk that has a single partition with an XFS file-system, because
# our images are created with XFS. When cluster-extension is done from
# the cod cluster, this script may end up on cloud nodes. We therefore
# skip any node-installer disks.
CATEGORY_INITIALIZE_SCRIPT_PATH = "/root/cm/category-initialize-script"
CATEGORY_INITIALIZE_SCRIPT = """\
#!/bin/bash

# This script is setup by the cluster-on-demand client. It finds disks with a
# single XFS partition (that's not the node-installer) and grows the file-
# system to span the entire disk.
disks=$(lsblk -lno name,type | grep 'disk$' | awk '{print $1}')
mkdir /tmp/xfs_mount
for disk in ${disks}; do
  echo -n "Detected disk /dev/${disk}"
  nr_of_partitions=$(lsblk -lno name,type /dev/${disk} | grep -c 'part$')
  if [ "${nr_of_partitions}" -eq "1" ]; then
    partition=$(lsblk -lno name,type /dev/${disk} | grep 'part$' | awk '{print $1}')
  elif [ "${nr_of_partitions}" -eq "3" ]; then
    # GPT layout: find largest partition (should be root filesystem, not biosgrub or EFI)
    partition=$(lsblk -ln -o name,size,type /dev/${disk} | grep 'part$' | sort -k2 -hr | head -1 | awk '{print $1}')
  else
    echo ", contains ${nr_of_partitions} partitions, skipping resize."
    continue
  fi

  if [ -n "${partition}" ]; then
    # note, use 'file' instead of 'lsblk'
    # 'lsblk -lno fstype /dev/$partition' sometimes returns empty, see CM-34808
    # "SGI XFS filesystem data" string is from 'file' program source, see CM-41737
    if file --special-files --dereference /dev/$partition | grep --quiet --ignore-case "SGI XFS filesystem data"; then
      if [ "$(lsblk -lno label /dev/${partition})" != "BCMINSTALLER" ]; then
        echo ", resizing partition /dev/${partition}."
        partition_number=${partition//[^0-9]/}
        echo Fix | parted /dev/${disk} ---pretend-input-tty print
        parted /dev/${disk} --script resizepart ${partition_number} 100%
        sleep 1
        partprobe /dev/${disk}

        echo -e "\\nMounting /dev/${partition}."
        tries=5
        while [[ "${tries}" -gt "0" ]]; do
          # On edge directors, edge iso image is already mounted on /mnt/
          # 2 devices mounted on /mnt, makes xfs_growfs fail. So we use /tmp/xfs_mount
          if ! mount /dev/${partition} /tmp/xfs_mount; then
            ((tries--))
            echo "Mounting /dev/${partition} failed, ${tries} attempts left."
            sleep 1
          else
            echo "Mounted /dev/${partition}."
            break
          fi
        done
        if [[ "${tries}" -eq "0" ]]; then
          echo "Failed to mount /dev/${partition}, aborting."
          exit 1
        fi

        echo "Resizing XFS file-system on /dev/${partition}."
        xfs_growfs /tmp/xfs_mount

        echo "Unmounting /dev/${partition}."
        umount /tmp/xfs_mount
      else
        echo ", partition /dev/${partition} has node-installer label, skipping resize."
      fi
    else
      echo ", partition /dev/${partition} is not XFS, skipping resize."
    fi
  fi
done
"""  # noqa: W605


def _get_node_disk_setup(bright_version: str) -> str:
    if config["node_disk_setup_path"]:
        with open(config["node_disk_setup_path"]) as file_handle:
            log.info("Using disk setup from %s" % config["node_disk_setup_path"])
            node_disk_setup = file_handle.read()
    elif config["node_disk_setup"]:
        if config["node_disk_setup"] is not DEFAULT_DISK_SETUP:  # user-supplied disk setup
            log.debug("Using disk setup from --node-disk-setup")
            node_disk_setup = config["node_disk_setup"]
        elif (
            bright_version
            and BcmVersion(bright_version).release >= (11, 0)
            and config["cloud_type"] == "openstack"
        ):
            log.debug("Using default disk setup for Openstack 11.0 and above")
            node_disk_setup = OS_DEFAULT_NODE_DISK_SETUP_11_AND_ABOVE
        elif bright_version and BcmVersion(bright_version).release >= (10, 0):
            log.debug("Using default disk setup for 10.0 and above")
            node_disk_setup = DEFAULT_DISK_SETUP_10_AND_ABOVE
        else:
            log.debug("Using default disk setup for 9.2 and below")
            node_disk_setup = DEFAULT_DISK_SETUP
    else:
        raise CODException("Please specify a valid node disk setup using --node-disk-setup or "
                           "--node-disk-setup-path.")
    # FIXME: need to remove newlines as somehow the file ends up
    # with '\n' characters if there is newline anywhere, which breaks the setup
    return str(node_disk_setup.replace("\n", ""))


def validate_copy_file_parameters(bright_version: str, raise_on_missing: bool = True) -> None:
    if config["copy_file_with_env"]:
        file_pairs = copy_file_set_version(config["copy_file_with_env"], bright_version)
    elif config["copy_file"]:
        file_pairs = config["copy_file"]
    else:
        return

    if config["copy_file"] or config["copy_file_with_env"]:
        compiled_url_regex = re.compile(URL_REGEX)
        for source, destination in file_pairs:
            if compiled_url_regex.match(source):
                parsed_uri = urlparse(source)
                c = httplib.HTTPConnection(parsed_uri.netloc)
                c.request("HEAD", parsed_uri.path)
                if c.getresponse().status != 200:
                    if raise_on_missing:
                        raise CODException("URL '%s' is unreachable, please make sure "
                                           "the provided URL is valid." % source)
                    log.warning("URL '%s' is unreachable, the file will not be copied to the cluster." % source)
                log.debug("Copying file '%s' to '%s' on the head node.", source, destination)
            else:
                if not os.path.isfile(source):
                    if raise_on_missing:
                        raise CODException(
                            "The file '%s' does not exist, please make sure the specified path is valid." % source)

                    log.warning("The file '%s' does not exist, it will not be copied to the cluster." % source)
                elif destination.startswith("/home"):
                    log.warning("Copying file '%s' to '%s' on the head node.", source, destination)
                    log.warning("Destination file '%s' is in a home directory. Did you mean '/root'?", destination)
                else:
                    log.debug("Copying file '%s' to '%s' on the head node.", source, destination)


def _append_to_write_files(cloud_config: CloudConfig, file_pairs: list[list[str]], cluster_version: str | None = None,
                           get_env: bool = False, preserve_permissions: bool = False) -> None:
    """Append files to the write_files in the heat stack in order to write them on the headnode.

    :param cloud_config: CloudConfig object to add the files to
    :param file_pairs: A series of either colon separated src:dst paths
    :param cluster_version: Cluster version
    :param get_env: Specify whether or not to we want to import environment variables
    :param preserve_permissions: Specify whether or not to preserve source file permissions
    """
    file_pairs = copy_file_set_version(file_pairs, cluster_version)
    compiled_url_regex = re.compile(URL_REGEX)
    for file_pair in file_pairs:
        source_file, destination_file = file_pair
        source_permissions = None

        if compiled_url_regex.match(source_file):
            r = requests.get(source_file)
            if r.status_code != 200:
                raise CODException("URL '%s' is unreachable, please make sure "
                                   "the provided URL is valid." % source_file)
            raw_content = r.text.encode()
        else:
            if not os.path.isfile(source_file):
                continue
            if preserve_permissions:
                source_permissions = f"{os.stat(source_file).st_mode:04o}"[-4:]
            with open(source_file, "rb") as fdata:
                raw_content = fdata.read()

        if get_env:
            raw_content = fill_env_variables(destination_file, raw_content.decode()).encode()
        cloud_config.add_file(
            destination_file,
            raw_content,
            base64=True,
            permissions=source_permissions
        )


def add_common_head_files(cloud_config: CloudConfig, bright_version: str, distro: str) -> None:
    services = BASIC_SERVICES

    if not distro.startswith("sles"):
        services.append("nslcd")
    service_list = "&name=".join(services)
    cloud_config.add_file(CMD_READY_PROBE_PATH, str(CMD_READY_PROBE_TEMPLATE).format(service_list=service_list))
    cloud_config.add_file(REMOTE_NODE_DISK_SETUP_PATH, _get_node_disk_setup(bright_version))
    cloud_config.add_file(CATEGORY_INITIALIZE_SCRIPT_PATH, CATEGORY_INITIALIZE_SCRIPT)

    if config["copy_file"]:
        _append_to_write_files(
            cloud_config,
            config["copy_file"],
            cluster_version=bright_version,
            preserve_permissions=True,
        )
        # no yaml.dump for content, as it's not clear how to force proper encoding
        # of newlines for unknown reason it works differently than e.g. for cluster_info

    if config["copy_file_with_env"]:
        _append_to_write_files(
            cloud_config,
            config["copy_file_with_env"],
            get_env=True,
            cluster_version=bright_version,
            preserve_permissions=True,
        )

    if config["license_activation_password"]:
        cloud_config.add_file(
            "/var/spool/cmd/license-activation-server.pass",
            config["license_activation_password"],
            permissions="0600", base64=True)
