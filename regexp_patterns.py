#!/usr/bin/env python3
# -*- coding: utf-8 -*-

__author__ = "ipetrash"


import re

from third_party.regexp import fill_string_pattern


PATTERN_NOTIFICATION_PAGE = re.compile(
    r"^notify page=(?P<page>\d+) group#(?P<group_id>\d*)$"
)
PATTERN_DELETE_MESSAGE = "delete_message"

COMMAND_START = "start"
COMMAND_HELP = "help"

COMMAND_SHOW_NOTIFICATION_COUNT = "show_notification_count"

COMMAND_START_NOTIFICATION = "start_notification"
COMMAND_STOP_NOTIFICATION = "stop_notification"

COMMAND_SEARCH = "search"
PATTERN_REPLY_SEARCH = re.compile(r"^Search (?P<text>.+)$", flags=re.IGNORECASE)
PATTERN_SEARCH_PAGE = re.compile(
    r"^notify search=(?P<search_id>\d+) page=(?P<page>\d+)$"
)

COMMAND_FIND = "find"
PATTERN_REPLY_FIND = re.compile(r"^Find (?P<text>.+)$", flags=re.IGNORECASE)


if __name__ == "__main__":
    print(fill_string_pattern(PATTERN_NOTIFICATION_PAGE, 1, 999_999_999))
    assert (
        fill_string_pattern(PATTERN_NOTIFICATION_PAGE, 1, 999_999_999)
        == "notify page=1 group#999999999"
    )
