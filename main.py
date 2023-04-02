#!/usr/bin/env python3
# -*- coding: utf-8 -*-

__author__ = 'ipetrash'


import os
import time

from threading import Thread

# pip install python-telegram-bot
from telegram import Update, Bot, ParseMode, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Updater, MessageHandler, CommandHandler, CallbackQueryHandler, Filters, CallbackContext, Defaults
)

import config
import db

from config import MESS_MAX_LENGTH, INLINE_BUTTON_TEXT_URL, INLINE_BUTTON_TEXT_DELETE
from common import get_logger, log_func, reply_error, TypeEnum


DATA = {
    'BOT': None,
    'IS_WORKING': True,
}

PATTERN_DELETE_MESSAGE = 'delete_message'
INLINE_BUTTON_DELETE = InlineKeyboardButton(INLINE_BUTTON_TEXT_DELETE, callback_data=PATTERN_DELETE_MESSAGE)


log = get_logger(__file__)


def get_chat_id(update: Update) -> int:
    return update.effective_chat.id


def sending_notifications():
    while True:
        bot: Bot = DATA['BOT']
        if not bot or not config.CHAT_ID:
            continue

        try:
            for notify in db.Notification.get_unsent():
                # Пауза, если IS_WORKING = False
                while not DATA['IS_WORKING']:
                    time.sleep(0.001)
                    continue

                buttons = []
                if notify.url:
                    buttons.append(InlineKeyboardButton(INLINE_BUTTON_TEXT_URL, url=notify.url))
                if notify.has_delete_button:
                    buttons.append(INLINE_BUTTON_DELETE)
                reply_markup = InlineKeyboardMarkup.from_row(buttons) if buttons else None

                text = notify.get_html()
                for n in range(0, len(text), MESS_MAX_LENGTH):
                    mess = text[n: n + MESS_MAX_LENGTH]
                    bot.send_message(config.CHAT_ID, mess, parse_mode=ParseMode.HTML, reply_markup=reply_markup)
                notify.set_as_send()

                time.sleep(1)

        except Exception as e:
            log.exception('')

            if config.CHAT_ID:
                text = f'⚠ При отправке уведомления возникла ошибка: {e}'

                try:
                    bot.send_message(config.CHAT_ID, text)
                except Exception:
                    log.exception('Ошибка при отправке уведомления об ошибке')

                time.sleep(60)

        finally:
            time.sleep(1)


@log_func(log)
def on_start(update: Update, _: CallbackContext):
    if not config.CHAT_ID:
        update.effective_message.reply_text('Введите что-нибудь для получения chat_id')


@log_func(log)
def on_show_notification_count(update: Update, _: CallbackContext):
    message = update.effective_message
    chat_id = get_chat_id(update)
    count = db.Notification.select().where(db.Notification.chat_id == chat_id).count()

    message.reply_text(f'{TypeEnum.INFO.emoji} Было отправлено {count} уведомлений', quote=True)


@log_func(log)
def on_callback_delete_message(update: Update, _: CallbackContext):
    query = update.callback_query
    if query:
        query.answer()

    query.delete_message()


@log_func(log)
def on_request(update: Update, _: CallbackContext):
    message = update.effective_message

    chat_id = get_chat_id(update)

    # Если чат не задан
    if not config.CHAT_ID:
        text = f'CHAT_ID: {chat_id}'
    elif chat_id == config.CHAT_ID:
        command = message.text.lower()
        if command == 'start':
            DATA['IS_WORKING'] = True
        elif command == 'stop':
            DATA['IS_WORKING'] = False

        is_working = DATA['IS_WORKING']
        text = (
            f'Поддерживаемые команды: <b>start</b>, <b>stop</b>\n'
            f'Рассылка уведомлений: <b>' + ('запущена' if is_working else 'остановлена') + '</b>'
        )
    else:
        text = 'Этот чат не имеет доступа к функциям бота'

    message.reply_html(text)


def on_error(update: Update, context: CallbackContext):
    reply_error(log, update, context)


def main():
    log.debug('Start')

    cpu_count = os.cpu_count()
    workers = cpu_count
    log.debug(f'System: CPU_COUNT={cpu_count}, WORKERS={workers}')
    log.debug(f'CHAT_ID={config.CHAT_ID}')

    updater = Updater(
        config.TOKEN,
        workers=workers,
        defaults=Defaults(run_async=True),
    )
    bot = updater.bot
    log.debug(f'Bot name {bot.first_name!r} ({bot.name})')

    DATA['BOT'] = bot

    dp = updater.dispatcher

    dp.add_handler(CommandHandler('start', on_start))
    dp.add_handler(CommandHandler('show_notification_count', on_show_notification_count))
    dp.add_handler(CallbackQueryHandler(on_callback_delete_message, pattern=PATTERN_DELETE_MESSAGE))
    dp.add_handler(MessageHandler(Filters.text, on_request))

    dp.add_error_handler(on_error)

    updater.start_polling()
    updater.idle()

    log.debug('Finish')


if __name__ == '__main__':
    Thread(target=sending_notifications).start()

    while True:
        try:
            main()
        except:
            log.exception('')

            timeout = 15
            log.info(f'Restarting the bot after {timeout} seconds')
            time.sleep(timeout)
