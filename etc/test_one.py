#!/usr/bin/env python3
# -*- coding: utf-8 -*-

__author__ = "ipetrash"


import sys
import random

from telegram_notifications_bot.tools.add_notify import add_notify


if __name__ == "__main__":
    # Название можно передать как аргумент
    try:
        name: str = sys.argv[1]
    except IndexError:
        name = "test"

    number: int = random.randrange(2, 5 + 2)
    for i in range(number):
        text = f"Rand: {i+1} / {number}"
        print(name, text)
        add_notify(name=name, message=text)
