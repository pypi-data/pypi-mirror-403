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

COD_DESCRIPTION = "cluster-on-demand"
COD_TAG = "COD::is_cluster_on_demand"
COD_TOOL_VERSION = 1
COD_TOOL_VERSION_TAG = "COD::cod_version"
COD_DISTRO_TAG = "COD::bcm_distro"
COD_VERSION_TAG = "COD::bcm_version"
COD_CMDREV_TAG = "COD::bcm_cmd_initial_revision"
COD_PACKAGE_GROUP = "COD::bcm_initial_package_group"
COD_HEAD_IMAGE_CREATED_AT = "COD::head_image_created_at"
COD_HEAD_IMAGE_ID = "COD::head_image_id"
COD_HEAD_IMAGE_NAME = "COD::head_image_name"
COD_HEAD_IMAGE_REV = "COD::head_image_revision"
COD_HEAD_IMAGE_UUID = "COD::head_image_uuid"
COD_LOCKED_UNTIL = "COD::locked_until"
COD_EDGE_ATTACHED = "COD::edge"
COD_HAS_CX = "COD::has_cluster_extension"
COD_TRACE_ID = "COD::trace_id"

BASIC_SERVICES = ["RamdiskService", "SysConfigGenerator", "SysConfigWriter", "dhcpd", "named", "nfs", "shorewall"]
