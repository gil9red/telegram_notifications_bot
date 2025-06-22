#!/usr/bin/env python3
# -*- coding: utf-8 -*-

__author__ = "ipetrash"


import os
import time
import re

from datetime import datetime
from threading import Thread

from peewee import fn, SQL

# pip install python-telegram-bot
from telegram import Update, Bot, ParseMode, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Updater,
    MessageHandler,
    CommandHandler,
    CallbackQueryHandler,
    Filters,
    CallbackContext,
    Defaults,
)
from telegram.error import BadRequest

import db

from config import (
    MESS_MAX_LENGTH,
    INLINE_BUTTON_TEXT_URL,
    INLINE_BUTTON_TEXT_DELETE,
    MESSAGE_ACCESS_DENIED,
    MESSAGE_UNKNOWN_COMMAND,
    USER_ID,
    TOKEN,
)
from common import (
    get_logger,
    log_func,
    access_check,
    reply_error,
    TypeEnum,
    get_user_id,
    is_admin,
)
from regexp_patterns import (
    fill_string_pattern,
    PATTERN_NOTIFICATION_PAGE,
    PATTERN_DELETE_MESSAGE,
    COMMAND_START,
    COMMAND_HELP,
    COMMAND_STATS,
    COMMAND_START_NOTIFICATION,
    COMMAND_STOP_NOTIFICATION,
    COMMAND_SEARCH,
    PATTERN_REPLY_SEARCH,
    PATTERN_SEARCH_PAGE,
    COMMAND_FIND,
    PATTERN_REPLY_FIND,
)
from third_party.telegram_bot_pagination import InlineKeyboardPaginator
from third_party.is_equal_inline_keyboards import is_equal_inline_keyboards


def datetime_to_str(dt: datetime) -> str:
    return f"{dt:%d.%m.%Y %H:%M:%S}"


def get_int_from_match(match: re.Match, name: str, default: int = None) -> int:
    try:
        return int(match[name])
    except:
        return default


DATA = {
    "BOT": None,
    "IS_WORKING": True,
}

INLINE_BUTTON_DELETE = InlineKeyboardButton(
    INLINE_BUTTON_TEXT_DELETE, callback_data=PATTERN_DELETE_MESSAGE
)


log = get_logger(__file__)


def get_buttons_for_notify(
    notify: db.Notification,
    allow_delete_button: bool = True,
) -> list[InlineKeyboardButton]:
    buttons = []
    if notify.url:
        buttons.append(InlineKeyboardButton(INLINE_BUTTON_TEXT_URL, url=notify.url))
    if notify.has_delete_button and allow_delete_button:
        buttons.append(INLINE_BUTTON_DELETE)

    return buttons


def get_paginator_for_notify(
    notify: db.Notification,
    buttons: list[InlineKeyboardButton],
) -> InlineKeyboardPaginator:
    page = notify.get_index_in_group() + 1
    total = notify.group.get_total_notifications()
    pattern = PATTERN_NOTIFICATION_PAGE

    paginator = InlineKeyboardPaginator(
        page_count=total,
        current_page=page,
        data_pattern=fill_string_pattern(pattern, "{page}", notify.group.id),
    )
    if buttons:
        paginator.add_before(*buttons)

    return paginator


def get_paginator_for_search(
    page: int,
    total: int,
    search: db.Search,
    buttons: list[InlineKeyboardButton],
) -> InlineKeyboardPaginator:
    pattern = PATTERN_SEARCH_PAGE

    paginator = InlineKeyboardPaginator(
        page_count=total,
        current_page=page,
        data_pattern=fill_string_pattern(pattern, search.id, "{page}"),
    )
    if buttons:
        paginator.add_before(*buttons)

    return paginator


def get_context_value(context: CallbackContext) -> str | None:
    value = None
    try:
        # Значение вытаскиваем из регулярки
        if context.match:
            value = context.match.group(1)
        else:
            # Значение из значений команды
            value = " ".join(context.args)
    except:
        pass

    return value


def send_notify(
    bot: Bot,
    notify: db.Notification,
    reply_markup: str | None,
    chat_id: int = USER_ID,
    as_new_message: bool = True,
    message_id: int = None,
    reply_to_message_id: int = None,
    add_sending_datetime: bool = False,
):
    text = notify.get_html()

    if add_sending_datetime and notify.sending_datetime:
        text += f"\n\n{datetime_to_str(notify.sending_datetime)}"

    if len(text) > MESS_MAX_LENGTH:
        text = text[: MESS_MAX_LENGTH - 3] + "..."

    parse_mode = ParseMode.HTML

    if as_new_message:
        bot.send_message(
            chat_id=chat_id,
            text=text,
            parse_mode=parse_mode,
            reply_markup=reply_markup,
            reply_to_message_id=reply_to_message_id,
        )
    else:
        bot.edit_message_text(
            chat_id=chat_id,
            message_id=message_id,
            text=text,
            parse_mode=parse_mode,
            reply_markup=reply_markup,
        )


def sending_notifications():
    while True:
        bot: Bot | None = DATA["BOT"]
        if not bot or not USER_ID:
            time.sleep(0.001)
            continue

        try:
            for notify in db.Notification.get_unsent():
                # Пауза, если IS_WORKING = False
                while not DATA["IS_WORKING"]:
                    time.sleep(0.001)
                    continue

                buttons = get_buttons_for_notify(notify)

                # Если уведомление находится в группе
                # Нужно вернуть только первое уведомление с пагинацией
                if notify.group:
                    # Если на текущий момент не все уведомления из группы находятся в базе
                    if not notify.group.is_complete():
                        continue

                    # Если уведомление не первое в группе, то не возвращаем его
                    # Но помечаем как отправленное
                    if not notify.is_first_in_group():
                        notify.set_as_send()
                        continue

                    paginator = get_paginator_for_notify(notify, buttons)
                    reply_markup = paginator.markup

                else:
                    reply_markup = (
                        InlineKeyboardMarkup.from_row(buttons) if buttons else None
                    )

                send_notify(bot, notify, reply_markup)
                notify.set_as_send()

                time.sleep(1)

        except Exception as e:
            log.exception("")

            if USER_ID:
                text = f"⚠ При отправке уведомления возникла ошибка: {e}"

                try:
                    bot.send_message(USER_ID, text)
                except Exception:
                    log.exception("Ошибка при отправке уведомления об ошибке")

                time.sleep(60)

        finally:
            time.sleep(1)


def reply_sending_notification_status(update: Update):
    text = (
        f"Рассылка уведомлений: <b>"
        + ("запущена" if DATA["IS_WORKING"] else "остановлена")
        + "</b>"
    )
    update.effective_message.reply_html(text)


@log_func(log)
def on_start(update: Update, _: CallbackContext):
    user_id = get_user_id(update)

    if not USER_ID:
        text = f"USER_ID: {user_id}"
    elif is_admin(user_id):
        lines = (
            "Команды:",
            f" * /{COMMAND_STATS} для просмотра статистики",
            f" * /{COMMAND_STOP_NOTIFICATION} для остановки рассылки уведомлений",
            f" * /{COMMAND_START_NOTIFICATION} для возобновления рассылки уведомлений",
            (
                f" * /{COMMAND_SEARCH}, /{COMMAND_FIND}, "
                f"{PATTERN_REPLY_SEARCH.pattern!r} или"
                f" {PATTERN_REPLY_FIND.pattern!r} для поиска уведомлений"
            ),
        )
        text = "\n".join(lines)
    else:
        text = MESSAGE_ACCESS_DENIED

    update.effective_message.reply_text(text)


@log_func(log)
@access_check(log)
def on_stats(update: Update, _: CallbackContext):
    message = update.effective_message
    chat_id = get_user_id(update)

    filters = [db.Notification.chat_id == chat_id]
    count: int = db.Notification.select().where(*filters).count()
    first_append_datetime: datetime = (
        db.Notification
        .select(db.Notification.append_datetime)
        .where(*filters)
        .order_by(db.Notification.append_datetime)
        .first()
        .append_datetime
    )
    last_append_datetime: datetime = (
        db.Notification
        .select(db.Notification.append_datetime)
        .where(*filters)
        .order_by(db.Notification.append_datetime.desc())
        .first()
        .append_datetime
    )

    query_year_by_number = (
        db.Notification.select(
            fn.STRFTIME("%Y", db.Notification.append_datetime).alias("year"),
            fn.COUNT(db.Notification.id),
        )
        .where(*filters)
        .group_by(SQL("year"))
        .order_by(SQL("year").desc())
    )
    years_info: str = "\n".join(
        f"    <b>{year}</b>: {number}"
        for year, number in query_year_by_number.tuples()
    )

    text = f"""
{TypeEnum.INFO.emoji} <b>Статистика уведомлений</b>
<b>Отправлено</b>: {count}
{years_info}
<b>Первое</b>: {datetime_to_str(first_append_datetime)}
<b>Последнее</b>: {datetime_to_str(last_append_datetime)}
    """.strip()

    message.reply_text(
        text,
        parse_mode=ParseMode.HTML,
        quote=True,
    )


@log_func(log)
@access_check(log)
def on_start_notification(update: Update, _: CallbackContext):
    DATA["IS_WORKING"] = True
    reply_sending_notification_status(update)


@log_func(log)
@access_check(log)
def on_stop_notification(update: Update, _: CallbackContext):
    DATA["IS_WORKING"] = False
    reply_sending_notification_status(update)


@log_func(log)
@access_check(log)
def on_search(update: Update, context: CallbackContext):
    message = update.effective_message

    text = get_context_value(context)
    if not text:
        message.reply_text(
            f"{TypeEnum.ERROR.emoji} Не введен текст для поиска!",
            quote=True,
        )
        return

    search, ids = db.Notification.search(text)
    if not search:
        message.reply_text(
            f"{TypeEnum.INFO.emoji} Не найдено!",
            quote=True,
        )
        return

    notify = db.Notification.get_by_id(ids[0])
    buttons = get_buttons_for_notify(notify, allow_delete_button=False)

    paginator = get_paginator_for_search(
        page=1,
        total=len(ids),
        search=search,
        buttons=buttons,
    )
    send_notify(
        bot=context.bot,
        notify=notify,
        reply_markup=paginator.markup,
        reply_to_message_id=message.message_id,
        add_sending_datetime=True,
    )


@log_func(log)
def on_callback_search_pagination(update: Update, context: CallbackContext):
    query = update.callback_query
    if query:
        query.answer()

    page = get_int_from_match(context.match, "page")
    by_search_id = get_int_from_match(context.match, "search_id")

    # NOTE: По сути, переход по кнопкам пагинации вызывает новый поиск
    #       Что может увеличивать количество результатов
    #       Обойти можно, если при первом поиске запомнить все id уведомлений
    #       и по ним переходить в пагинаторе
    search = db.Search.get_by_id(by_search_id)
    _, ids = db.Notification.search(search.text)

    notify = db.Notification.get_by_search(regex=search, page=page)
    buttons = get_buttons_for_notify(notify, allow_delete_button=False)

    paginator = get_paginator_for_search(
        page=page,
        total=len(ids),
        search=search,
        buttons=buttons,
    )
    reply_markup = paginator.markup

    # Fix error: "telegram.error.BadRequest: Message is not modified"
    if is_equal_inline_keyboards(reply_markup, query.message.reply_markup):
        return

    try:
        send_notify(
            context.bot,
            notify,
            reply_markup,
            as_new_message=False,
            message_id=update.effective_message.message_id,
            add_sending_datetime=True,
        )
    except BadRequest as e:
        if "Message is not modified" in str(e):
            return

        raise e


@log_func(log)
def on_callback_delete_message(update: Update, _: CallbackContext):
    query = update.callback_query

    try:
        query.delete_message()
    except BadRequest as e:
        if "Message can't be deleted for everyone" in str(e):
            text = "Нельзя удалить сообщение, т.к. оно слишком старое. Остается только вручную его удалить"
        else:
            text = f"При попытке удаления сообщения возникла ошибка: {str(e)!r}"

        query.answer(
            text=text,
            show_alert=True,
        )
        return

    query.answer()


@log_func(log)
def on_change_notification_page(update: Update, context: CallbackContext):
    query = update.callback_query
    if query:
        query.answer()

    page = get_int_from_match(context.match, "page")
    by_group_id = get_int_from_match(context.match, "group_id")

    group: db.NotificationGroup = db.NotificationGroup.get_by_id(by_group_id)
    notify = group.get_notification(page - 1)
    buttons = get_buttons_for_notify(notify)

    paginator = get_paginator_for_notify(notify, buttons)
    reply_markup = paginator.markup

    # Fix error: "telegram.error.BadRequest: Message is not modified"
    if is_equal_inline_keyboards(reply_markup, query.message.reply_markup):
        return

    try:
        send_notify(
            context.bot,
            notify,
            reply_markup,
            as_new_message=False,
            message_id=update.effective_message.message_id,
        )
    except BadRequest as e:
        if "Message is not modified" in str(e):
            return

        raise e


@log_func(log)
@access_check(log)
def on_request(update: Update, _: CallbackContext):
    message = update.effective_message
    message.reply_text(MESSAGE_UNKNOWN_COMMAND)


def on_error(update: Update, context: CallbackContext):
    reply_error(log, update, context)


def main():
    log.debug("Start")

    cpu_count = os.cpu_count()
    workers = cpu_count
    log.debug(f"System: CPU_COUNT={cpu_count}, WORKERS={workers}")
    log.debug(f"USER_ID={USER_ID}")

    updater = Updater(
        TOKEN,
        workers=workers,
        defaults=Defaults(run_async=True),
    )
    bot = updater.bot
    log.debug(f"Bot name {bot.first_name!r} ({bot.name})")

    DATA["BOT"] = bot

    dp = updater.dispatcher

    dp.add_handler(CommandHandler(COMMAND_START, on_start))
    dp.add_handler(CommandHandler(COMMAND_HELP, on_start))

    dp.add_handler(
        CommandHandler(COMMAND_STATS, on_stats)
    )

    dp.add_handler(CommandHandler(COMMAND_START_NOTIFICATION, on_start_notification))
    dp.add_handler(CommandHandler(COMMAND_STOP_NOTIFICATION, on_stop_notification))

    dp.add_handler(CommandHandler(COMMAND_SEARCH, on_search))
    dp.add_handler(CommandHandler(COMMAND_FIND, on_search))
    dp.add_handler(MessageHandler(Filters.regex(PATTERN_REPLY_SEARCH), on_search))
    dp.add_handler(MessageHandler(Filters.regex(PATTERN_REPLY_FIND), on_search))
    dp.add_handler(
        CallbackQueryHandler(on_callback_search_pagination, pattern=PATTERN_SEARCH_PAGE)
    )

    dp.add_handler(
        CallbackQueryHandler(on_callback_delete_message, pattern=PATTERN_DELETE_MESSAGE)
    )
    dp.add_handler(
        CallbackQueryHandler(
            on_change_notification_page, pattern=PATTERN_NOTIFICATION_PAGE
        )
    )
    dp.add_handler(MessageHandler(Filters.text, on_request))

    dp.add_error_handler(on_error)

    updater.start_polling()
    updater.idle()

    log.debug("Finish")


if __name__ == "__main__":
    Thread(target=sending_notifications).start()

    while True:
        try:
            main()
        except:
            log.exception("")

            timeout = 15
            log.info(f"Restarting the bot after {timeout} seconds")
            time.sleep(timeout)
