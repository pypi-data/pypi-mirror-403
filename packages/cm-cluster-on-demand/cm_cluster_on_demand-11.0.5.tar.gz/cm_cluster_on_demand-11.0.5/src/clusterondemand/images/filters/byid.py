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
from collections.abc import Iterable
from fnmatch import translate
from itertools import chain
from re import Pattern


def match_by_id_query(id_query: Iterable[tuple[int | None, Pattern[str]]], id: str, revision: int) -> bool:
    """Match image data using id_query.

    >>> rev_reg = make_id_query([("id1", 1), ("id2", None)], [("pat*", 1)], ["regex.*"])

    >>> match_by_id_query(rev_reg, "id1", 1)
    True

    >>> match_by_id_query(rev_reg, "id1", 2)
    False

    >>> match_by_id_query(rev_reg, "id2", 1)
    True

    >>> match_by_id_query(rev_reg, "id2", 2)
    True

    >>> match_by_id_query(rev_reg, "pattern", 1)
    True

    """
    for rev, regex in id_query:
        if rev is not None and revision != rev:
            continue
        if id and regex.match(id) is not None:
            return True
    return False


def make_id_query(ids: Iterable[tuple[str, int | None]], patterns: Iterable[tuple[str, int | None]],
                  regexes: Iterable[str]) -> list[tuple[int | None, Pattern[str]]]:
    """Return list of tuples (revision, combined_regex).

    >>> rev_reg = dict(make_id_query([("id1", 1), ("id2", None)], [("pat*", 1)], ["regex.*"]))
    >>> bool(rev_reg[1].match("id1"))
    True
    >>> bool(rev_reg[1].match("id2"))
    False
    >>> bool(rev_reg[1].match("pattern"))
    True
    >>> bool(rev_reg[1].match("regexp"))
    False

    >>> bool(rev_reg[None].match("id1"))
    False
    >>> bool(rev_reg[None].match("id2"))
    True
    >>> bool(rev_reg[None].match("pattern"))
    False
    >>> bool(rev_reg[None].match("regexp"))
    True

    """
    regex_queries = chain(
        # Creating a simple full match regex for a explicit ids ...
        (("^%s$" % (id,), rev) for id, rev in ids),
        # ... converting pattern to a regex
        ((translate(pat), rev) for pat, rev in patterns),
        # ... and using regexes as is with None revision
        ((regex, None) for regex in regexes)
    )

    result_dict: dict[int | None, str] = {}
    for regex, revision in regex_queries:
        combined_regex = result_dict.get(revision, "")
        if len(combined_regex) == 0:
            combined_regex += "(?:"
        else:
            combined_regex += "|"
        combined_regex += "(?:" + regex + ")"
        result_dict[revision] = combined_regex

    return [(rev, re.compile(regex + ")")) for rev, regex in result_dict.items()]
