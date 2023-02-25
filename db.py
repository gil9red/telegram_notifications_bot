#!/usr/bin/env python3
# -*- coding: utf-8 -*-

__author__ = 'ipetrash'


import datetime as DT
import enum
import html
import time

from typing import Any, Type

# pip install peewee
from peewee import (
    Model, TextField, ForeignKeyField, DateTimeField, CharField, IntegerField, BooleanField
)
from playhouse.sqliteq import SqliteQueueDatabase

from config import DB_FILE_NAME
from common import TypeEnum

from third_party.shorten import shorten


# This working with multithreading
# SOURCE: http://docs.peewee-orm.com/en/latest/peewee/playhouse.html#sqliteq
db = SqliteQueueDatabase(
    DB_FILE_NAME,
    pragmas={
        'foreign_keys': 1,
        'journal_mode': 'wal',    # WAL-mode
        'cache_size': -1024 * 64  # 64MB page-cache
    },
    use_gevent=False,     # Use the standard library "threading" module.
    autostart=True,
    queue_max_size=64,    # Max. # of pending writes that can accumulate.
    results_timeout=5.0   # Max. time to wait for query to be executed.
)


class EnumField(CharField):
    """
    This class enable an Enum like field for Peewee
    """

    def __init__(self, choices: Type[enum.Enum], *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)

        self.choices: Type[enum.Enum] = choices
        self.max_length = 255

    def db_value(self, value: Any) -> Any:
        return value.value

    def python_value(self, value: Any) -> Any:
        type_value_enum = type(list(self.choices)[0].value)
        value_enum = type_value_enum(value)
        return self.choices(value_enum)


class BaseModel(Model):
    class Meta:
        database = db

    @classmethod
    def get_inherited_models(cls) -> list[Type['BaseModel']]:
        return sorted(cls.__subclasses__(), key=lambda x: x.__name__)

    @classmethod
    def print_count_of_tables(cls):
        items = []
        for sub_cls in cls.get_inherited_models():
            name = sub_cls.__name__
            count = sub_cls.select().count()
            items.append(f'{name}: {count}')

        print(', '.join(items))

    def __str__(self):
        fields = []
        for k, field in self._meta.fields.items():
            v = getattr(self, k)

            if isinstance(field, (TextField, CharField)):
                if v:
                    if isinstance(v, enum.Enum):
                        v = v.value

                    v = repr(shorten(v))

            elif isinstance(field, ForeignKeyField):
                k = f'{k}_id'
                if v:
                    v = v.id

            fields.append(f'{k}={v}')

        return self.__class__.__name__ + '(' + ', '.join(fields) + ')'


class Notification(BaseModel):
    chat_id = IntegerField()
    name = TextField()
    message = TextField()
    type = EnumField(null=False, choices=TypeEnum, default=TypeEnum.INFO)
    url = TextField(null=True)
    has_delete_button = BooleanField(default=False)
    append_datetime = DateTimeField(default=DT.datetime.now)
    sending_datetime = DateTimeField(null=True)

    @classmethod
    def add(
            cls,
            chat_id: int,
            name: str,
            message: str,
            type: TypeEnum = TypeEnum.INFO,
            url: str = None,
            has_delete_button: bool = False,
    ) -> 'Notification':
        if isinstance(url, str) and not url.strip():
            url = None

        return cls.create(
            chat_id=chat_id,
            name=name,
            message=message,
            type=type,
            url=url,
            has_delete_button=has_delete_button,
        )

    @classmethod
    def get_unsent(cls) -> list['Notification']:
        """
        Функция класс, что возвращает неотправленные уведомления
        """

        return list(cls.select().where(cls.sending_datetime.is_null(True)))

    def set_as_send(self):
        """
        Функция устанавливает дату отправки и сохраняет ее
        """

        self.sending_datetime = DT.datetime.now()
        self.save()

    def get_html(self) -> str:
        """
        Функция возвращает текст для отправки запроса в формате HTML
        """

        title = html.escape(self.name)
        text = html.escape(self.message)
        return f'{self.type.emoji} <b>{title}</b>\n{text}'


db.connect()
db.create_tables(BaseModel.get_inherited_models())

# Задержка в 50мс, чтобы дать время на запуск SqliteQueueDatabase и создание таблиц
# Т.к. в SqliteQueueDatabase запросы на чтение выполняются сразу, а на запись попадают в очередь
time.sleep(0.050)


if __name__ == '__main__':
    BaseModel.print_count_of_tables()
    # Notification: 2593

    print()

    # Notification.delete().execute()

    # Notification.add(
    #     chat_id=1,
    #     name='check',
    #     message='ALL OK!',
    #     type=TypeEnum.INFO,
    # )

    print('Total:', len(Notification.select()))
    # for x in Notification.select():
    #     print(x)
    #     print(x.get_html())

    print('Unsent:', len(Notification.get_unsent()))

    # print()
    #
    # for x in Notification.get_unsent():
    #     print(x)
    #     x.set_as_send()
