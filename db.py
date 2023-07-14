#!/usr/bin/env python3
# -*- coding: utf-8 -*-

__author__ = "ipetrash"


import datetime as dt
import enum
import html
import time

from typing import Any, Type, TypeVar, Optional, Iterable

# pip install peewee
from peewee import (
    Model,
    TextField,
    ForeignKeyField,
    DateTimeField,
    CharField,
    IntegerField,
    BooleanField,
    Field,
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
        "foreign_keys": 1,
        "journal_mode": "wal",  # WAL-mode
        "cache_size": -1024 * 64,  # 64MB page-cache
    },
    use_gevent=False,  # Use the standard library "threading" module.
    autostart=True,
    queue_max_size=64,  # Max. # of pending writes that can accumulate.
    results_timeout=5.0,  # Max. time to wait for query to be executed.
    regexp_function=True,
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


ChildModel = TypeVar("ChildModel", bound="BaseModel")


class BaseModel(Model):
    class Meta:
        database = db

    @classmethod
    def get_inherited_models(cls) -> list[Type["BaseModel"]]:
        return sorted(cls.__subclasses__(), key=lambda x: x.__name__)

    @classmethod
    def print_count_of_tables(cls):
        items = []
        for sub_cls in cls.get_inherited_models():
            name = sub_cls.__name__
            count = sub_cls.select().count()
            items.append(f"{name}: {count}")

        print(", ".join(items))

    @classmethod
    def paginating(
        cls,
        page: int = 1,
        items_per_page: int = 1,
        filters: Iterable = None,
        order_by: Field = None,
    ) -> list[ChildModel]:
        query = cls.select()

        if filters:
            query = query.filter(*filters)

        if order_by:
            query = query.order_by(order_by)

        query = query.paginate(page, items_per_page)
        return list(query)

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
                k = f"{k}_id"
                if v:
                    v = v.id

            fields.append(f"{k}={v}")

        return self.__class__.__name__ + "(" + ", ".join(fields) + ")"


class Search(BaseModel):
    text = TextField(unique=True)

    @classmethod
    def get_by(cls, text: str) -> Optional["Search"]:
        return cls.get_or_none(text=text)

    @classmethod
    def add(cls, text: str) -> "Search":
        obj = cls.get_by(text)
        if not obj:
            obj = cls.create(text=text)

        return obj


class NotificationGroup(BaseModel):
    name = TextField(unique=True)
    max_number = IntegerField()

    @classmethod
    def get_by(cls, name: str) -> Optional["NotificationGroup"]:
        return cls.get_or_none(name=name)

    @classmethod
    def add(
        cls,
        name: str,
        max_number: int = None,
    ) -> Optional["NotificationGroup"]:
        obj = cls.get_by(name)
        if not obj:
            if not max_number:
                raise Exception(
                    "Значение max_number для новой NotificationGroup должно быть задано!"
                )

            # Нет смысла создавать группу для 1 или меньше элементов
            if max_number <= 1:
                return

            obj = cls.create(
                name=name,
                max_number=max_number,
            )
        return obj

    def get_total_notifications(self) -> int:
        return len(self.notifications)

    def is_complete(self) -> bool:
        return self.get_total_notifications() >= self.max_number

    def get_notification(self, idx: int = 0) -> Optional["Notification"]:
        items: list[Notification] = list(self.notifications)
        try:
            return items[idx]
        except IndexError:
            return


class Notification(BaseModel):
    chat_id = IntegerField()
    name = TextField()
    message = TextField()
    type = EnumField(null=False, choices=TypeEnum, default=TypeEnum.INFO)
    url = TextField(null=True)
    has_delete_button = BooleanField(default=False)
    show_type = BooleanField(default=True)
    append_datetime = DateTimeField(default=dt.datetime.now)
    sending_datetime = DateTimeField(null=True)
    group: NotificationGroup = ForeignKeyField(
        NotificationGroup, null=True, backref="notifications"
    )

    @classmethod
    def add(
        cls,
        chat_id: int,
        name: str,
        message: str,
        type: TypeEnum = TypeEnum.INFO,
        url: str = None,
        has_delete_button: bool = False,
        show_type: bool = True,
        group: NotificationGroup | str = None,
        group_max_number: int = None,
    ) -> "Notification":
        if isinstance(url, str) and not url.strip():
            url = None

        # Если группа задана и это имя группы
        if group and isinstance(group, str):
            group = NotificationGroup.add(
                name=group,
                max_number=group_max_number,
            )

        if group:
            number = group.get_total_notifications()
            if group.max_number <= number:
                raise Exception(
                    f"Количество уведомлений {number} в группе {group} "
                    f"превысило максимальное количество {group.max_number}"
                )

        # Явно задаем отсутствие группы (например, будет проблема, если в group попадет пустая строка)
        if not group:
            group = None

        return cls.create(
            chat_id=chat_id,
            name=name,
            message=message,
            type=type,
            url=url,
            has_delete_button=has_delete_button,
            show_type=show_type,
            group=group,
        )

    @classmethod
    def get_unsent(cls) -> list["Notification"]:
        """
        Функция класс, что возвращает неотправленные уведомления
        """

        return list(cls.select().where(cls.sending_datetime.is_null(True)))

    def set_as_send(self):
        """
        Функция устанавливает дату отправки и сохраняет ее
        """

        if not self.sending_datetime:
            self.sending_datetime = dt.datetime.now()
            self.save()

    def get_index_in_group(self) -> int:
        if self.group:
            for i in range(self.group.get_total_notifications()):
                if self == self.group.get_notification(i):
                    return i
        return -1

    def get_html(self) -> str:
        """
        Функция возвращает текст для отправки запроса в формате HTML
        """

        text = ""
        if self.show_type:
            text += self.type.emoji + " "

        name = html.escape(self.name)
        message = html.escape(self.message)

        number_in_group: str = ""
        if self.group:
            number = self.get_index_in_group() + 1
            total = self.group.get_total_notifications()
            number_in_group = f" [{number}/{total}]"

        text += f"<b>{name}</b>{number_in_group}\n{message}"

        return text.strip()

    def is_first_in_group(self) -> bool:
        if not self.group:
            return False
        return self == self.group.get_notification()

    @classmethod
    def __get_filter_for_search(cls, regex: str) -> Field:
        regex = f"(?i){regex}"  # Без учета регистра

        # Сложение полей и строк порождает правильное сложение данных в запросе базы
        return (cls.name + " " + cls.message).regexp(regex)

    @classmethod
    def search(cls, regex: str) -> tuple[Search | None, list[int]]:
        expr = cls.__get_filter_for_search(regex)
        query = cls.select(cls.id).where(expr).order_by(cls.id)
        items = [obj.id for obj in query]
        search = Search.add(regex) if items else None
        return search, items

    @classmethod
    def get_by_search(
        cls,
        regex: str | Search,
        page: int = 1,
    ) -> Optional["Notification"]:
        if isinstance(regex, Search):
            regex = regex.text

        items = cls.paginating(
            page=page,
            items_per_page=1,
            filters=[cls.__get_filter_for_search(regex)],
            order_by=cls.id,
        )
        return items[0] if items else None


db.connect()
db.create_tables(BaseModel.get_inherited_models())

# Задержка в 50мс, чтобы дать время на запуск SqliteQueueDatabase и создание таблиц
# Т.к. в SqliteQueueDatabase запросы на чтение выполняются сразу, а на запись попадают в очередь
time.sleep(0.050)


if __name__ == "__main__":
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

    print("Total:", len(Notification.select()))
    # for x in Notification.select():
    #     print(x)
    #     print(x.get_html())

    print("Unsent:", len(Notification.get_unsent()))

    # print()
    #
    # for x in Notification.get_unsent():
    #     print(x)
    #     x.set_as_send()
