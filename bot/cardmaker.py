from telegram import Update
from telegram import ParseMode
from telegram.ext import CallbackContext

from bot.config import debug_requests
from bot.keyboard import CARDMAKER
from bot.keyboard import get_article_list_inline_keyboard
from bot.keyboard import get_cardmaker_ready_article_inline_keyboard
from bot.db import get_list_to_design
from bot.db import get_user_info
from bot.db import set_article_readiness
from bot.db import get_weekly_useful_info

CHOOSE_ARTICLE_MESSAGE = 'Выберите статью из списка:'
ARTICLE_LIST_EMPTY_MESSAGE = 'Сейчас нет статей, требующих оформления'

CARDMAKER_MENU_MESSAGE_ID = 0
CARDMAKER_ARTICLE_ID = 0


@debug_requests
def cardmaker_messages(update: Update, context: CallbackContext):
    if update.effective_message.text == CARDMAKER['SHOW_ARTICLE_LIST_BUTTON']:
        show_to_design_list(update=update, context=context)
    elif update.effective_message.text == CARDMAKER['USEFUL_INFO_BUTTON']:
        send_cardmaker_useful_info(update=update, context=context)
    else:
        update.message.reply_text('Упс... Кажется вы ввели неверную команду')


@debug_requests
def show_to_design_list(update: Update, context: CallbackContext):
    if context.user_data['Role'] == 'Cardmaker':
        article_list = get_list_to_design(cardmaker=context.user_data['Name'])
        if len(article_list) != 0:
            context.bot.send_message(
                chat_id=update.effective_message.chat_id,
                text=CHOOSE_ARTICLE_MESSAGE,
                reply_markup=get_article_list_inline_keyboard(article_list),
                parse_mode=ParseMode.MARKDOWN,

            )
        else:
            update.message.reply_text(
                ARTICLE_LIST_EMPTY_MESSAGE,
                parse_mode=ParseMode.MARKDOWN
            )


@debug_requests
def send_cardmaker_useful_info(update: Update, context: CallbackContext):
    send_teaching_material(update=update, context=context)
    send_weekly_useful_materials(update=update, context=context)


@debug_requests
def send_teaching_material(update: Update, context: CallbackContext):
    update.message.reply_text(
        '<b>Методический материал для картмейкеров:</b>\n\n<a href="https://drive.google.com/file/d/1Ezg0ts9GGYMBUf6QSWqsnDNnZBrdD3bK/view?usp=sharing">Ссылка на документ</a>\n',
        parse_mode=ParseMode.HTML
    )


@debug_requests
def send_weekly_useful_materials(update: Update, context: CallbackContext):
    text = get_weekly_useful_info(info_type=context.user_data['Role'])
    if text != 'None':
        update.message.reply_text(
            text,
            parse_mode=ParseMode.HTML,
        )


@debug_requests
def cardmaker_inline_keyboard(update: Update, context: CallbackContext):
    query = update.callback_query

    try:
        int(query.data) - 1
        operation_type = 'Choosing article'
    except ValueError:
        data = query.data
        operation_type = data

    if operation_type == 'Choosing article':
        show_to_design_article(update, context)
    elif operation_type == 'Article is ready':
        send_notification_to_coordinator(update, context)
        update_cardmaker_menu(update, context)
    elif operation_type == CARDMAKER['SHOW_ARTICLE_LIST_BUTTON']:
        show_to_design_list(update, context)


@debug_requests
def show_to_design_article(update: Update, context: CallbackContext):
    query = update.callback_query
    global CARDMAKER_MENU_MESSAGE_ID
    CARDMAKER_MENU_MESSAGE_ID = query.message.message_id
    article_list = get_list_to_design(cardmaker=context.user_data['Name'])
    article_index = int(query.data) - 1
    global CARDMAKER_ARTICLE_ID
    CARDMAKER_ARTICLE_ID = article_list[article_index]['id']
    context.bot.send_document(
        chat_id=update.effective_message.chat_id,
        document=article_list[article_index]['file_id'],
        caption=f'Автор: *{article_list[article_index]["author"]}*\n\nДедлайн: *{article_list[article_index]["deadline"]}*',
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=get_cardmaker_ready_article_inline_keyboard(),
    )


@debug_requests
def send_notification_to_coordinator(update: Update, context: CallbackContext):
    coordinator_info = get_user_info(user_id=442046856)
    coordinator_chat_id = coordinator_info[2]
    context.bot.send_message(
        chat_id=coordinator_chat_id,
        text=f'✉️ {context.user_data["Name"]} уведомляет о готовности статьи'
    )


@debug_requests
def update_cardmaker_menu(update: Update, context: CallbackContext):
    context.bot.delete_message(
        chat_id=update.effective_message.chat_id,
        message_id=update.callback_query.message.message_id
    )
    set_article_readiness(id=CARDMAKER_ARTICLE_ID)
    article_list = get_list_to_design(cardmaker=context.user_data['Name'])
    if len(article_list) != 0:
        context.bot.edit_message_text(
            chat_id=update.effective_message.chat_id,
            text=CHOOSE_ARTICLE_MESSAGE,
            reply_markup=get_article_list_inline_keyboard(article_list),
            message_id=CARDMAKER_MENU_MESSAGE_ID
        )
    else:
        context.bot.edit_message_text(
            chat_id=update.effective_message.chat_id,
            text=ARTICLE_LIST_EMPTY_MESSAGE,
            parse_mode=ParseMode.MARKDOWN,
            message_id=CARDMAKER_MENU_MESSAGE_ID
        )