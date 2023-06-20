#!/usr/bin/env python3
# -*- coding: utf-8 -*-

__author__ = "ipetrash"


import unittest

from peewee import SqliteDatabase
from playhouse.sqlite_ext import SqliteExtDatabase

import regexp_patterns as P

from common import TypeEnum
from db import NotificationGroup, Notification, Search


DEBUG = False


class TestRegexpPatterns(unittest.TestCase):
    MAX_PAGE = 9999
    MAX_ID = 999_999_999_999
    MAX_DATA_SIZE = 64

    def do_check_callback_data_value(self, pattern, *args):
        callback_data_value = P.fill_string_pattern(pattern, *args)

        size_callback_data = len(bytes(callback_data_value, "utf-8"))
        DEBUG and print(f"    Size {size_callback_data} of {callback_data_value!r}\n")
        self.assertTrue(
            size_callback_data <= self.MAX_DATA_SIZE,
            f"Превышение размера callback_data для {pattern}. Размер: {size_callback_data}",
        )

    def test_pattern_authors_page(self):
        with self.subTest("Nulls"):
            self.assertEqual(
                "notify page=1 group#None",
                P.fill_string_pattern(P.PATTERN_NOTIFICATION_PAGE, 1, None),
            )

        with self.subTest("Max"):
            self.do_check_callback_data_value(
                P.PATTERN_NOTIFICATION_PAGE, self.MAX_PAGE, self.MAX_ID
            )

    def test_pattern_search_page(self):
        self.assertEqual(
            "notify search=1 page=1",
            P.fill_string_pattern(P.PATTERN_SEARCH_PAGE, 1, 1),
        )

        self.do_check_callback_data_value(
            P.PATTERN_SEARCH_PAGE, self.MAX_ID, self.MAX_PAGE
        )


class TestDbNotificationGroup(unittest.TestCase):
    def setUp(self):
        self.models = [NotificationGroup, Notification]
        self.test_db = SqliteDatabase(":memory:")
        self.test_db.bind(self.models, bind_refs=False, bind_backrefs=False)
        self.test_db.connect()
        self.test_db.create_tables(self.models)

    def test_add(self):
        with self.subTest("Ok"):
            name = "test group 1"
            max_number = 2
            group = NotificationGroup.add(name=name, max_number=max_number)

            self.assertIsNotNone(group)
            self.assertEqual(name, group.name)
            self.assertEqual(max_number, group.max_number)

            self.assertEqual(
                group, NotificationGroup.add(name="test group 1", max_number=2)
            )

        with self.subTest("Max number = 1"):
            self.assertIsNone(
                NotificationGroup.add(name="test group 404", max_number=1)
            )

        with self.subTest("Max number is not defined for new group"):
            with self.assertRaises(Exception):
                NotificationGroup.add(name="test group 404")

        with self.subTest("Max number is 0 for new group"):
            with self.assertRaises(Exception):
                NotificationGroup.add(name="test group 404", max_number=0)

    def test_get_by(self):
        name = "test group 1"

        self.assertIsNone(NotificationGroup.get_by(name=name))

        group = NotificationGroup.add(name="test group 1", max_number=999)

        self.assertEqual(group, NotificationGroup.get_by(name=name))

    def test_get_total_notifications(self):
        group = NotificationGroup.add(name="test group 1", max_number=10)

        notifications = [
            Notification.add(
                chat_id=1,
                name="test",
                message=f"message #{i}",
                group=group,
            )
            for i in range(group.max_number)
        ]
        self.assertEqual(len(notifications), group.get_total_notifications())

    def test_is_complete(self):
        group = NotificationGroup.add(name="test group 1", max_number=10)
        self.assertFalse(group.is_complete())

        for i in range(group.max_number // 2):
            Notification.add(
                chat_id=1,
                name="test",
                message=f"message #{i}",
                group=group,
            )
        self.assertFalse(group.is_complete())

        for i in range(group.max_number // 2):
            Notification.add(
                chat_id=1,
                name="test",
                message=f"message #{i}",
                group=group,
            )
        self.assertTrue(group.is_complete())

    def test_get_notification(self):
        group = NotificationGroup.add(name="test group 1", max_number=10)

        notifications = [
            Notification.add(
                chat_id=1,
                name="test",
                message=f"message #{i}",
                group=group,
            )
            for i in range(group.max_number)
        ]
        self.assertEqual(notifications[0], group.get_notification(0))
        self.assertEqual(notifications[-1], group.get_notification(-1))


class TestDbNotification(unittest.TestCase):
    def setUp(self):
        self.models = [NotificationGroup, Notification, Search]
        self.test_db = SqliteExtDatabase(":memory:", regexp_function=True)
        self.test_db.bind(self.models, bind_refs=False, bind_backrefs=False)
        self.test_db.connect()
        self.test_db.create_tables(self.models)

    def test_add(self):
        chat_id = 123
        name = "test"
        message = "message 1"

        group_name = "group 1"
        group_max_number = 3

        with self.subTest("All fields"):
            type = TypeEnum.INFO
            url = "https://example.com"
            has_delete_button = True
            show_type = True

            notification = Notification.add(
                chat_id=chat_id,
                name=name,
                message=message,
                type=type,
                url=url,
                has_delete_button=has_delete_button,
                show_type=show_type,
                group=group_name,
                group_max_number=group_max_number,
            )
            self.assertIsNotNone(notification)
            self.assertEqual(chat_id, notification.chat_id)
            self.assertEqual(name, notification.name)
            self.assertEqual(message, notification.message)
            self.assertEqual(type, notification.type)
            self.assertEqual(url, notification.url)
            self.assertEqual(has_delete_button, notification.has_delete_button)
            self.assertEqual(show_type, notification.show_type)
            self.assertEqual(group_name, notification.group.name)
            self.assertEqual(group_max_number, notification.group.max_number)

        with self.subTest("Invalid group"):
            notification = Notification.add(
                chat_id=chat_id,
                name=name,
                message=message,
                type=type,
                url=url,
                group="",
                group_max_number=group_max_number,
            )
            self.assertIsNotNone(notification)
            self.assertIsNone(notification.group)

        with self.subTest("Group as object"):
            group = NotificationGroup.add(
                name=group_name,
                max_number=group_max_number,
            )
            notification = Notification.add(
                chat_id=chat_id,
                name=name,
                message=message,
                type=type,
                url=url,
                has_delete_button=has_delete_button,
                show_type=show_type,
                group=group,
            )
            self.assertEqual(group, notification.group)
            self.assertEqual(group.name, notification.group.name)
            self.assertEqual(group.max_number, notification.group.max_number)

        with self.subTest("Excess of the maximum number"):
            with self.assertRaises(Exception):
                for _ in range(group_max_number + 1):
                    Notification.add(
                        chat_id=chat_id,
                        name=name,
                        message=message,
                        group=group_name,
                        group_max_number=group_max_number,
                    )

    def test_get_unsent(self):
        chat_id = 123
        name = "test"
        message = "message 1"

        items = [
            Notification.add(
                chat_id=chat_id,
                name=name,
                message=message,
            )
            for _ in range(3)
        ]
        self.assertEqual(items, Notification.get_unsent())

    def test_set_as_send(self):
        chat_id = 123
        name = "test"
        message = "message 1"

        items = [
            Notification.add(
                chat_id=chat_id,
                name=name,
                message=message,
            )
            for _ in range(3)
        ]
        self.assertEqual(items, Notification.get_unsent())

        for notify in items:
            notify.set_as_send()

        self.assertFalse(Notification.get_unsent())

    def test_get_index_in_group(self):
        with self.subTest("Ok"):
            group = NotificationGroup.add(name="test group 1", max_number=10)

            notifications = [
                Notification.add(
                    chat_id=1,
                    name="test",
                    message=f"message #{i}",
                    group=group,
                )
                for i in range(group.max_number)
            ]
            for notify in notifications:
                idx = notify.get_index_in_group()
                self.assertEqual(notify, notify.group.get_notification(idx))

        with self.subTest("Without group"):
            notify = Notification.add(
                chat_id=1,
                name="test",
                message=f"message",
            )
            self.assertEqual(-1, notify.get_index_in_group())

    def test_get_html(self):
        chat_id = 123
        name = "test"
        message = "message 1"

        with self.subTest("show_type=True"):
            notify = Notification.add(
                chat_id=chat_id,
                name=name,
                message=message,
                show_type=True,
            )
            text = notify.get_html()
            self.assertTrue(text)
            self.assertIn(notify.type.emoji, text)
            self.assertIn(notify.name, text)
            self.assertIn(notify.message, text)

        with self.subTest("show_type=False"):
            notify = Notification.add(
                chat_id=chat_id,
                name=name,
                message=message,
                show_type=False,
            )
            text = notify.get_html()
            self.assertTrue(text)
            self.assertNotIn(notify.type.emoji, text)
            self.assertIn(notify.name, text)
            self.assertIn(notify.message, text)

    def test_is_first_in_group(self):
        chat_id = 123
        name = "test"
        message = "message 1"

        group_name = "group 1"
        group_max_number = 3

        items = [
            Notification.add(
                chat_id=chat_id,
                name=name,
                message=message,
                group=group_name,
                group_max_number=group_max_number,
            )
            for _ in range(group_max_number)
        ]
        self.assertTrue(items[0].is_first_in_group())
        self.assertFalse(items[1].is_first_in_group())
        self.assertFalse(items[2].is_first_in_group())

        notify_without_group = Notification.add(
            chat_id=chat_id,
            name=name,
            message=message,
        )
        self.assertFalse(notify_without_group.is_first_in_group())

    def test_search(self):
        text_en = "Hel.+rld"
        self.assertIsNone(Search.get_by(text_en))

        text_ru = "При.+ир"
        self.assertIsNone(Search.get_by(text_ru))

        chat_id = 123
        notification_1 = Notification.add(chat_id, name=text_en, message=text_ru)
        notification_2 = Notification.add(chat_id, name=text_ru, message=text_en)
        expected = [notification_1.id, notification_2.id]
        expected.sort()

        for text in [text_en, text_ru]:
            with self.subTest(text=text):
                search, actual = Notification.search(text)
                self.assertIsNotNone(search)
                self.assertEqual(expected, actual)

                search = Search.get_by(text)
                self.assertIsNotNone(search)

    def test_get_by_search(self):
        with self.subTest("Not found"):
            search, ids = Notification.search("NOT FOUND")
            self.assertIsNone(search)
            self.assertTrue(len(ids) == 0)

        text_en = "Hel.+rld"
        text_ru = "При.+ир"

        chat_id = 123
        notification_1 = Notification.add(chat_id, name=text_en, message=text_ru)
        notification_2 = Notification.add(chat_id, name=text_ru, message=text_en)

        for text in [text_en, text_ru]:
            with self.subTest(text=text):
                # Добавим записи в таблицу Search
                search, _ = Notification.search(text)
                self.assertIsNotNone(search)

                search2 = Search.get_by(text)
                self.assertIsNotNone(search2)

                self.assertEqual(search, search2)

                actual = Notification.get_by_search(text, page=1)
                self.assertEqual(notification_1, actual)

                actual = Notification.get_by_search(text, page=2)
                self.assertEqual(notification_2, actual)

                actual = Notification.get_by_search(search, page=1)
                self.assertEqual(notification_1, actual)

                actual = Notification.get_by_search(search, page=2)
                self.assertEqual(notification_2, actual)


class TestDbSearch(unittest.TestCase):
    def setUp(self):
        self.models = [Search]
        self.test_db = SqliteDatabase(":memory:")
        self.test_db.bind(self.models, bind_refs=False, bind_backrefs=False)
        self.test_db.connect()
        self.test_db.create_tables(self.models)

    def test_add(self):
        text = "Hello World!"
        search1 = Search.add(text=text)
        self.assertIsNotNone(search1)

        search2 = Search.add(text=text)
        self.assertIsNotNone(search2)

        self.assertEqual(search1, search2)

    def test_get_by(self):
        text = "Hello World!"
        self.assertIsNone(Search.get_by(text=text))

        search1 = Search.add(text=text)

        search2 = Search.get_by(text=text)
        self.assertIsNotNone(search2)

        self.assertEqual(search1, search2)


if __name__ == "__main__":
    unittest.main()
