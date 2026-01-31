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

from datetime import datetime, tzinfo

from dateutil import tz

DATE_TIME_FORMAT = "%Y-%m-%d %H:%M"


def format_datetime(date_time: datetime, format: str = DATE_TIME_FORMAT, tzinfo: tzinfo | None = None) -> str:
    """Format datetime in locale timezone.

    >>> import pytz
    >>> format_datetime(datetime(2009, 12, 6, 16, 29, tzinfo=pytz.UTC),
    ...                 tzinfo=pytz.timezone('Etc/GMT+1'))
    '2009-12-06 15:29'
    """
    tzinfo = tzinfo or tz.tzlocal()
    return date_time.astimezone(tzinfo).strftime(format)


def get_datetime_ago(then_datetime: datetime, now_datetime: datetime | None = None) -> str:
    """
    Return human-readable difference between two datetimes.

    :param now_datetime:
    :param then_datetime:
    :return:
    >>> import pytz
    >>> get_datetime_ago(
    ...     datetime(2006, 11, 5, 17, 29, 43, tzinfo=pytz.UTC),
    ...    datetime(2009, 12, 6, 16, 29, 43, tzinfo=pytz.UTC)
    ... )
    '1126d 23h'

    >>> get_datetime_ago(
    ... datetime(2009, 12, 6, 15, 2, 4, tzinfo=pytz.UTC),
    ... datetime(2009, 12, 6, 16, 29, 43, tzinfo=pytz.UTC)
    ... )
    '1h 27m'
    """
    now_datetime = now_datetime or datetime.now(then_datetime.tzinfo)

    delta = now_datetime - then_datetime
    days = delta.days
    minutes = delta.seconds // 60
    hours = minutes // 60
    minutes %= 60
    if days:
        return "%dd %dh" % (days, hours)

    return "%dh %dm" % (hours, minutes)
