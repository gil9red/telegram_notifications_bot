#!/usr/bin/env python3
# -*- coding: utf-8 -*-

__author__ = 'ipetrash'


from db import Notification
from config import CHAT_ID
from common import TypeEnum


def add_notify(
        name: str,
        message: str,
        type: TypeEnum | str = TypeEnum.INFO,
        url: str = None,
        has_delete_button: bool = False,
        show_type: bool = True,
):
    if not CHAT_ID:
        raise Exception('Нужно заполнить "CHAT_ID.txt"!')

    if not isinstance(type, TypeEnum):
        type = TypeEnum[type]

    Notification.add(
        chat_id=CHAT_ID,
        name=name,
        message=message,
        type=type,
        url=url,
        has_delete_button=has_delete_button,
        show_type=show_type,
    )


if __name__ == '__main__':
    add_notify('TEST', 'Hello World! Привет мир!')
    add_notify('', 'Hello World! Привет мир!')
    add_notify('TEST', 'With url-button!', url='https://example.com/')
    add_notify('TEST', 'With delete-button!', has_delete_button=True)
    add_notify('TEST', 'show_type=False!', show_type=False)
    add_notify('TEST', 'With url and delete buttons!', url='https://example.com/', has_delete_button=True)
