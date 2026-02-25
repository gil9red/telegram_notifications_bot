#!/usr/bin/env python3
# -*- coding: utf-8 -*-

__author__ = "ipetrash"


import time

import requests

from common import TypeEnum
from config import HOST, PORT


URL = f"http://{HOST}:{PORT}/add_notify"


def add_notify(
    name: str,
    message: str,
    type: TypeEnum | str = TypeEnum.INFO,
    url: str = None,
    has_delete_button: bool = False,
    show_type: bool = True,
    group: str = None,
    group_max_number: int = None,
    need_html_escape_content: bool = True,
):
    if not name:
        raise Exception('Аргумент "name" не задан')

    if not message:
        raise Exception('Аргумент "message" не задан')

    data = {
        "name": name,
        "message": message,
        "type": type if isinstance(type, str) else type.value,
        "url": url,
        "has_delete_button": has_delete_button,
        "show_type": show_type,
        "group": group,
        "group_max_number": group_max_number,
        "need_html_escape_content": need_html_escape_content,
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


def test() -> None:
    add_notify("TEST", "Hello World! Привет мир!")
    add_notify("", "Hello World! Привет мир!")
    add_notify("Ошибка!", "Hello World! Привет мир!", TypeEnum.ERROR)
    add_notify("TEST", "With url-button!", url="https://example.com/")
    add_notify("TEST", "With delete-button!", has_delete_button=True)
    add_notify(
        "TEST",
        "With url and delete buttons!",
        url="https://example.com/",
        has_delete_button=True,
    )

    add_notify("TEST", "#1. Group 1!", group="group 1", group_max_number=2)
    add_notify("TEST", "#2. Group 1!", group="group 1", group_max_number=2)


if __name__ == "__main__":
    import argparse
    import sys

    def create_parser() -> argparse.ArgumentParser:
        parser = argparse.ArgumentParser(
            description="Скрипт для отправки уведомления в телеграм"
        )
        parser.add_argument(
            "--name", help="Название уведомления"
        )
        parser.add_argument(
            "--message", help="Текст уведомления"
        )
        parser.add_argument(
            "--type",
            type=TypeEnum,
            choices=TypeEnum,
            default=TypeEnum.INFO,
            help="Тип уведомления",
        )
        parser.add_argument(
            "--url", help="Ссылка в уведомлении"
        )
        parser.add_argument(
            "--has-delete-button",
            action="store_true",
            default=False,
            help="Добавление кнопки удаления в уведомление",
        )
        parser.add_argument(
            "--show-type",
            action=argparse.BooleanOptionalAction,
            default=True,
            help="Определяет нужно ли показывать иконку типа в уведомлении",
        )
        parser.add_argument(
            "--group", help="Название группы для объединения уведомлений"
        )
        parser.add_argument(
            "--group-max-number",
            type=int,
            help="Количество уведомлений в группе",
        )
        parser.add_argument(
            "--need-html-escape-content",
            action=argparse.BooleanOptionalAction,
            default=True,
            help="Определяет нужно ли экранировать название и текст в уведомлении как HTML",
        )
        parser.add_argument(
            "--run-test",
            action="store_true",
            help="Флаг для отправки тестовых данных",
        )
        return parser

    parser = create_parser()

    # Если не указаны параметры, выводим справку и выходим
    if len(sys.argv) == 1:
        parser.print_help()
        sys.exit()

    args = parser.parse_args()
    if args.run_test:
        test()
        sys.exit()

    add_notify(
        name=args.name,
        message=args.message,
        type=args.type,
        url=args.url,
        has_delete_button=args.has_delete_button,
        show_type=args.show_type,
        group=args.group,
        group_max_number=args.group_max_number,
        need_html_escape_content=args.need_html_escape_content,
    )
