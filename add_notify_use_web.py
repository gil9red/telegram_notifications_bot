#!/usr/bin/env python3
# -*- coding: utf-8 -*-

__author__ = 'ipetrash'


import time
from typing import Union

import requests

from common import TypeEnum
from config import HOST, PORT


URL = f'http://{HOST}:{PORT}/add_notify'


def add_notify(name: str, message: str, type: Union[TypeEnum, str] = TypeEnum.INFO):
    data = {
        'name': name,
        'message': message,
        'type': type.value,
    }

    # Попытки
    attempts_timeouts = [1, 5, 10, 30, 60]

    while True:
        try:
            rs = requests.post(URL, json=data)
            rs.raise_for_status()
            return

        except Exception as e:
            # Если закончились попытки
            if not attempts_timeouts:
                raise e

            timeout = attempts_timeouts.pop(0)
            time.sleep(timeout)


if __name__ == '__main__':
    add_notify('TEST', 'Hello World! Привет мир!')
    add_notify('', 'Hello World! Привет мир!')
    add_notify('Ошибка!', 'Hello World! Привет мир!', TypeEnum.ERROR)
