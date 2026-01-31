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
from collections.abc import Collection

from clusterondemand.exceptions import CODException


def only_explicit_ids(ids: Collection[tuple[str, int | None]], patterns: Collection[tuple[str, int | None]],
                      regexes: Collection[str], uuids: Collection[str], advanced: bool) -> bool:
    """Determine if query set contains only explicit image ids (names).

    A pattern is there
    >>> only_explicit_ids([("id", 1), ("id", 2)], ["pat*"], [], [], False)
    False

    A regex is there
    >>> only_explicit_ids([("id", 1), ("id", 2)], [], ["re.*"], [], False)
    False

    An id specifier does not specifies a version
    >>> only_explicit_ids([("id", 1), ("id", None)], [], [], [], False)
    False

    Which is fine for the advanced mode
    >>> only_explicit_ids([("id", 1), ("id", None)], [], [], [], True)
    True

    Now we can pick images by ids
    >>> only_explicit_ids([("id", 1), ("id", 2)], [], [], [], False)
    True

    Empty ids specified
    >>> only_explicit_ids([], [], [], [], False)
    False

    Only UUIDs specified
    >>> only_explicit_ids([], [], [], ["uuid", "uuid1"], False)
    True

    """
    if patterns or regexes:
        return False
    if not ids and not uuids:
        return False
    if not advanced and any(revision is None for _id, revision in ids):
        return False
    return True


def classify_ids(ids: Collection[str]) -> tuple[
    list[tuple[str, int | None]],
    list[tuple[str, int | None]],
    list[str],
    list[str],
]:
    """Parse set of passed Image IDs specifiers.

    Each of the specifiers can be either "image_id" or "image_id:revision" or "image_glance_uuid" or
    "image_id_wildcard" or "image_id_wildcard:revision" or "re:image_id_regex"

    >>> classify_ids(["image-id:1"])
    ([('image-id', 1)], [], [], [])

    >>> classify_ids(["re:image-id.*"])
    ([], [], ['image-id.*'], [])

    >>> classify_ids(["image-id.*:3"])
    ([], [('image-id.*', 3)], [], [])

    >>> classify_ids(["01234567-89ab-cdef-0123-456789abcdef"])
    ([], [], [], ['01234567-89ab-cdef-0123-456789abcdef'])

    >>> classify_ids(["ami-1234"])
    ([], [], [], ['ami-1234'])

    >>> classify_ids(["https://brightimages.blob.core.windows.net/images/bcm-cod-image-9.0-ubuntu1804-10.vhd"])
    ([], [], [], ['https://brightimages.blob.core.windows.net/images/bcm-cod-image-9.0-ubuntu1804-10.vhd'])

    >>> classify_ids(["image-id:1", "image-id.*:3", "re:image-id.*", \
        "01234567-89ab-cdef-0123-456789abcdef"])
    ([('image-id', 1)], [('image-id.*', 3)], ['image-id.*'], \
    ['01234567-89ab-cdef-0123-456789abcdef'])

    """
    plain_ids = []
    patterns = []
    regexes = []
    uuids = []
    for id in ids:
        if id.startswith("re:"):
            regexes.append(id[3:])
        elif re.match(r"[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}", id):
            uuids.append(id)
        elif re.match(r"ami-.*", id):
            uuids.append(id)
        elif re.match(r"https://.*", id):
            uuids.append(id)
        elif re.match(r"ocid\d*\..*", id):
            uuids.append(id)
        elif "*" in id or "?" in id or re.search(r".*\[.*\].*", id):
            patterns.append(parse_id_revision(id))
        else:
            plain_ids.append(parse_id_revision(id))
    return (plain_ids, patterns, regexes, uuids)


ID_REVISION_FORMAT = r"^(?P<id>[^:]+)(?::(?P<revision>[0-9]+))?$"
ID_REVISION_RE = re.compile(ID_REVISION_FORMAT)


def parse_id_revision(id_str: str) -> tuple[str, int | None]:
    """Parse image_id:revision string.

    >>> parse_id_revision("image-id:2")
    ('image-id', 2)

    >>> parse_id_revision("image-id")
    ('image-id', None)

    >>> parse_id_revision("image-id:wrong:")  # doctest: +IGNORE_EXCEPTION_DETAIL
    Traceback (most recent call last):
       ...
    CODException: image-id:wrong: has an invalid id:revision format. id should not contain colons \
    and revision has to be numeric
    """
    match = ID_REVISION_RE.match(id_str)
    if match is None:
        raise CODException(
            "%s has an invalid id:revision format. "
            "id should not contain colons and revision has to be numeric"
            % (id_str,)
        )
    id, revision_str = match.group("id"), match.group("revision")
    return id, int(revision_str) if revision_str is not None else None
