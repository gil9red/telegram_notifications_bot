#!/usr/bin/env python3
# -*- coding: utf-8 -*-

__author__ = "ipetrash"


import os

from pathlib import Path

DIR: Path = Path(__file__).resolve().parent

TOKEN_PATH: Path = DIR / "TOKEN.txt"
TOKEN: str = os.environ.get("TOKEN") or TOKEN_PATH.read_text("utf-8").strip()

USER_ID_PATH: Path = DIR / "USER_ID.txt"
USER_ID: int | None = None
try:
    USER_ID = int(os.environ.get("USER_ID") or USER_ID_PATH.read_text("utf-8").strip())
except:
    # Отсутствие значения учитывается в функциях отправки и при работе бота
    pass

# Создание папки для базы данных
DB_DIR_NAME: Path = DIR / "database"
DB_DIR_NAME.mkdir(parents=True, exist_ok=True)

# Путь к файлу базы данных
DB_FILE_NAME: str = str(DB_DIR_NAME / "database.sqlite")

# Example: "127.0.0.1:10016"
ADDRESS_PATH: Path = DIR / "ADDRESS.txt"
try:
    ADDRESS = os.environ.get("ADDRESS") or ADDRESS_PATH.read_text("utf-8").strip()
    HOST, PORT = ADDRESS.split(":")
    PORT = int(PORT)
except:
    HOST: str = "127.0.0.1"
    PORT: int = 10016

MESS_MAX_LENGTH: int = 4096

INLINE_BUTTON_TEXT_URL = "🔗 Открыть ссылку"
INLINE_BUTTON_TEXT_DELETE = "❌ Удалить"

MESSAGE_UNKNOWN_COMMAND = "Неизвестная команда"
MESSAGE_ACCESS_DENIED = "Этот чат не имеет доступа к функциям бота"
MESSAGE_ALLOWED_FOR_USERS_ONLY = "Разрешено только для пользователей"
MESSAGE_ERROR_TEXT = "Возникла какая-то проблема. Попробуйте повторить запрос или попробовать чуть позже..."
