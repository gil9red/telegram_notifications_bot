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
        group: str = None,
        group_max_number: int = None,
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
        group=group,
        group_max_number=group_max_number,
    )


if __name__ == '__main__':
    add_notify('TEST', 'Hello World! Привет мир!')
    add_notify('', 'Hello World! Привет мир!')
    add_notify('TEST', 'With url-button!', url='https://example.com/')
    add_notify('TEST', 'With delete-button!', has_delete_button=True)
    add_notify('TEST', 'show_type=False!', show_type=False)
    add_notify('TEST', 'With url and delete buttons!', url='https://example.com/', has_delete_button=True)

    from db import NotificationGroup
    group_1 = NotificationGroup.add('group 1', max_number=2)
    for notify in group_1.notifications:
        notify.delete_instance()
    add_notify('TEST', '#1. Group 1!', group=group_1)
    add_notify('TEST', '#2. Group 1!', group=group_1)

    # Пусть группа будет создана через имя в add_notify
    group_2 = NotificationGroup.add('group 2', max_number=3)
    group_2.delete_instance(recursive=True)
    add_notify('TEST', '#1. Group 2!', group=group_2.name, group_max_number=group_2.max_number)
    add_notify('TEST', '#2. Group 2!', group=group_2.name, group_max_number=group_2.max_number)
