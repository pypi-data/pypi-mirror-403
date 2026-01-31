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

import fnmatch
import logging
import re
from collections.abc import Collection, Iterable, Iterator
from typing import Any

from clusterondemand.clusternameprefix import clusterprefix_ns, ensure_cod_prefix
from clusterondemand.exceptions import CODException
from clusterondemandconfig import ConfigNamespace, config

from . import const

log = logging.getLogger("cluster-on-demand")


class ClusterFinder:
    """
    Class to abstract all finding functions coming from the backend. Each provider has to implement this
    """
    def __init__(self, min_cod_version: int | None = None, ignore_newer: bool | None = None,
                 all_stacks: bool | None = None) -> None:
        self.all_stacks = all_stacks if all_stacks is not None else config["all_stacks"]
        self.min_cod_version = min_cod_version if min_cod_version is not None else 1
        self.ignore_newer = ignore_newer if ignore_newer is not None else config["ignore_newer"]

    def find_by_names(self, names: Collection[str]) -> Iterator[Any]:
        raise NotImplementedError()

    def find_by_uuids(self, uuids: Collection[str]) -> Iterator[Any]:
        raise NotImplementedError()

    def find_all(self) -> Iterator[Any]:
        raise NotImplementedError()

    def find_by_tags(self, tags: list[str] | None = None, tags_any: list[str] | None = None,
                     not_tags: list[str] | None = None, not_tags_any: list[str] | None = None) -> Iterator[Any]:
        raise NotImplementedError()

    def get_cluster_name(self, cluster: Any) -> str:
        raise NotImplementedError()

    def get_cluster_id(self, cluster: Any) -> str:
        raise NotImplementedError()

    def get_cluster_tags(self, cluster: Any) -> list[str]:
        raise NotImplementedError()

    def filter_by_cod_version(self, clusters: Iterable[Any]) -> Iterator[Any]:
        return (
            cluster for cluster in clusters
            if self.check_cod_tool_version(cluster)
        )

    def check_cod_tool_version(self, cluster: Any, current_cod_version: int = const.COD_TOOL_VERSION) -> bool:
        tags = self.get_cluster_tags(cluster)
        if self.all_stacks and const.COD_TAG not in tags:
            return True

        version_re = re.compile(const.COD_TOOL_VERSION_TAG + "=([0-9]+)$")
        for tag in tags:
            m = version_re.match(tag)
            if m:
                if int(m.group(1)) < self.min_cod_version:
                    raise CODException(
                        "Cluster %s was created with an older version of the "
                        "cluster-on-demand tools. Can't perform the requested operation "
                        "on this cluster." % self.get_cluster_name(cluster)
                    )

                if int(m.group(1)) > current_cod_version:
                    if self.ignore_newer:
                        return False

                    raise CODException(
                        "Cluster %s was created with a newer version of the "
                        "cluster-on-demand tools. Please update your tools, or pass "
                        "--ignore-newer to ignore this cluster." % self.get_cluster_name(cluster)
                    )

                return True

        if not self.ignore_newer:
            raise CODException(
                "Unable to determine cluster-on-demand tool version used "
                "to create cluster %s." % self.get_cluster_name(cluster)
            )
        return False

    def find_clusters_with_config(self) -> tuple[list[Any], list[Any]]:
        return self.find_clusters(
            filters=config["filters"],
            tags=config["tags"],
            not_tags_any=config["not_tags_any"],
            not_tags=config["not_tags"],
            version=config["version"],
            distro=config["distro"],
        )

    def find_clusters(self, filters: list[str] | None = None, tags: list[str] | None = None,
                      tags_any: list[str] | None = None, not_tags: list[str] | None = None,
                      not_tags_any: list[str] | None = None, version: str | None = None,
                      distro: str | None = None) -> tuple[list[Any], list[Any]]:
        filters = [] if filters is None else filters
        tags = [] if tags is None else tags
        tags_any = [] if tags_any is None else tags_any
        not_tags = [] if not_tags is None else not_tags
        not_tags_any = [] if not_tags_any is None else not_tags_any

        cp_filters = filters[:]
        cp_tags = tags[:]

        if version:
            cp_tags = _replace_or_add_tag(cp_tags, const.COD_VERSION_TAG, version)
        if distro:
            cp_tags = _replace_or_add_tag(cp_tags, const.COD_DISTRO_TAG, distro)

        if not (cp_filters or cp_tags or tags_any or not_tags or not_tags_any):
            cp_filters = ["*"]

        stacks: Iterable[Any] = []
        missing_names: set[str] = set()

        if cp_tags or tags_any or not_tags or not_tags_any:
            stacks = self.find_by_tags(cp_tags, tags_any, not_tags, not_tags_any)
        if cp_filters:
            (stacks, missing_names) = _get_clusters_by_names(self, cp_filters, self.all_stacks, stacks)

        if len(missing_names) != 0:
            log.debug("Not found: %s" % ", ".join(sorted(missing_names)))

        return (sorted(stacks, key=lambda x: self.get_cluster_name(x)), sorted(missing_names))


def is_filtering_enabled() -> bool:

    keys = ["filters", "tags", "not_tags_any", "not_tags", "version", "distro", "ignore_newer"]
    for v in keys:
        if config[v]:
            return True

    return False


def _replace_or_add_tag(tags: Iterable[str], tag_name: str, tag_val: str) -> list[str]:
    tag_name_eq = tag_name + "="
    cleaned_tags = [x for x in tags if not x.startswith(tag_name_eq)]
    cleaned_tags.append(tag_name_eq + tag_val)
    return cleaned_tags


def _classify_names(names: list[str]) -> tuple[set[Any], list[str], list[Any], set[Any]]:
    plain_names = set()
    patterns = []
    regexes = []
    uuids = set()
    for name in names:
        if name.startswith("re:"):
            regexes.append(ensure_cod_prefix(name[3:]))
        elif "*" in name or "?" in name or re.search(r".*\[.*\].*", name):
            patterns.append(ensure_cod_prefix(name))
        elif re.match(r"[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}", name):
            uuids.add(name)
        else:
            plain_names.add(ensure_cod_prefix(name))
    return (plain_names, patterns, regexes, uuids)


def _get_clusters_by_names(finder: ClusterFinder, names: list[str], all_stacks: bool = False,
                           stacks: Iterable[Any] | None = None) -> tuple[list[Any], set[Any]]:
    (plain_names, patterns, regexes, uuids) = _classify_names(names)
    found_stacks = []
    if len(patterns) == 0 and len(regexes) == 0:
        if stacks:
            found_stacks = [s for s in stacks if finder.get_cluster_name(s) in plain_names or s.id in uuids]
        else:
            if len(plain_names) > 0:
                found_stacks.extend(finder.find_by_names(plain_names))
            if len(uuids) > 0:
                found_stacks.extend(finder.find_by_uuids(uuids))
    else:
        valid_regexes = []
        for regex in regexes:
            try:
                re.compile(regex)
            except re.error as e:
                raise CODException("Pattern '%s' is not a valid regex" % regex, caused_by=e)
            else:
                valid_regexes.append(regex)

        valid_regexes.extend([fnmatch.translate(p) for p in patterns])
        valid_regexes.extend([n + "$" for n in plain_names])

        combined_regex = re.compile("(?:%s)" % "|".join(valid_regexes))

        if all_stacks:
            kwargs = {}
        else:
            kwargs = {"tags": [const.COD_TAG]}

        if not stacks:
            stacks = finder.find_by_tags(**kwargs)

        def stack_ok(stack: Any) -> bool:
            return bool(combined_regex.match(finder.get_cluster_name(stack)) or finder.get_cluster_id(stack) in uuids)

        found_stacks = [s for s in stacks if stack_ok(s)]

    found_stacks = [s for s in found_stacks if finder.check_cod_tool_version(s)]
    found_names = {finder.get_cluster_name(s) for s in found_stacks}
    found_uuids = {finder.get_cluster_id(s) for s in found_stacks}
    missing = (plain_names - found_names) | (uuids - found_uuids)
    return (found_stacks, missing)


findclusters_ns = ConfigNamespace("common.cluster.find", help_section="cluster filter parameters")
findclusters_ns.import_namespace(clusterprefix_ns)
findclusters_ns.add_repeating_positional_parameter(
    "filters",
    default=None,
    help=("list of cluster names or UUID's. Regular "
          "expressions can be used with a 're:' prefix. Shell like wildcards are "
          "also supported."),
    require_value=True
)
findclusters_ns.add_parameter(
    "version",
    help="Select clusters with specified Bright version."
)
findclusters_ns.add_parameter(
    "distro",
    help="Select clusters with specified base distribution."
)
findclusters_ns.add_enumeration_parameter(
    "tags",
    default=[],
    help="list of tags, the cluster(s) must have them all. (AND)"
)
findclusters_ns.add_enumeration_parameter(
    "tags_any",
    default=[],
    help="list of tags, the cluster(s) must have at least one of them. (OR)"
)
findclusters_ns.add_enumeration_parameter(
    "not_tags",
    default=[],
    help="list of tags, the cluster(s) must not have all of them. (NAND)"
)
findclusters_ns.add_enumeration_parameter(
    "not_tags_any",
    default=[],
    help="list of tags, the cluster(s) must not have any of them. (NOR)"
)
findclusters_ns.add_switch_parameter(
    "ignore_newer",
    help=("Ignore cluster which were created with a newer version of the "
          "cluster-on-demand tools. When such clusters are encountered, and "
          "this flag is not specified, the tools will abort with an error "
          "message.")
)
findclusters_ns.add_switch_parameter(
    "all_stacks",
    help=("Assume all heat stacks are clusters, even the ones that don't "
          "have the tags normally required. Use with care, especially if heat "
          "is also used for workloads other than cluster on demand.")
)
