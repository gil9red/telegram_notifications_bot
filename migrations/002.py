#!/usr/bin/env python3
# -*- coding: utf-8 -*-

__author__ = 'ipetrash'


# SOURCE: http://docs.peewee-orm.com/en/latest/peewee/playhouse.html#schema-migrations


from playhouse.migrate import SqliteDatabase, SqliteMigrator, BooleanField, migrate
from config import DB_FILE_NAME


db = SqliteDatabase(DB_FILE_NAME)
migrator = SqliteMigrator(db)


with db.atomic():
    migrate(
        migrator.add_column('notification', 'show_type', BooleanField(default=True)),
    )
