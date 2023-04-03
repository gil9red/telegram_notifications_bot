#!/usr/bin/env python3
# -*- coding: utf-8 -*-

__author__ = 'ipetrash'


import re

from third_party.regexp import fill_string_pattern


PATTERN_NOTIFICATION_PAGE = re.compile(
    r'^notify page=(?P<page>\d+) group#(?P<group_id>\d*)$'
)


if __name__ == '__main__':
    print(fill_string_pattern(PATTERN_NOTIFICATION_PAGE, 1, 999_999_999))
    assert fill_string_pattern(PATTERN_NOTIFICATION_PAGE, 1, 999_999_999) == 'notify page=1 group#999999999'
