from telegram import Update
from telegram import ParseMode
from telegram import InputMediaDocument
from telegram.ext import CallbackContext

from bot.config import debug_requests
from bot.keyboard import CARDMAKER
from bot.keyboard import get_article_list_inline_keyboard
from bot.keyboard import get_cardmaker_ready_article_inline_keyboard
from bot.db import get_list_to_design
from bot.db import set_article_readiness
from bot.db import get_weekly_useful_info
from bot.db import get_file_from_list_to_design
from bot.db import get_author_chat_id_from_list_to_design
from bot.db import get_user_chat_id_by_role

CHOOSE_ARTICLE_MESSAGE = 'Выберите статью из списка:'
ARTICLE_LIST_EMPTY_MESSAGE = 'Сейчас нет статей, требующих оформления'

IS_CHECKING_TO_DESIGN = False


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
        '''
        <b>Методический материал для картмейкеров:</b>
        
        
        <b><a href="https://drive.google.com/file/d/1Ezg0ts9GGYMBUf6QSWqsnDNnZBrdD3bK/view?usp=sharing">
        Ссылка на документ
        </a></b>
        
        ''',
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
        int(query.data.split()[1])
        operation_type = 'Choosing article'
    except (ValueError, IndexError):
        data = query.data
        operation_type = data

    if operation_type == 'Choosing article':
        show_to_design_article(update, context)
    elif operation_type == 'Article is ready':
        send_notification_to_coordinator_and_author(update, context)
        update_cardmaker_menu(update, context)
    elif operation_type == CARDMAKER['SHOW_ARTICLE_LIST_BUTTON']:
        show_to_design_list(update, context)


@debug_requests
def show_to_design_article(update: Update, context: CallbackContext):
    query = update.callback_query

    context.user_data['CARDMAKER_MENU_MESSAGE_ID'] = query.message.message_id
    article_list = get_list_to_design(cardmaker=context.user_data['Name'])
    article_index = int(query.data.split()[1]) - 1
    context.user_data['CARDMAKER_ARTICLE_ID'] = article_list[article_index]['id']
    global IS_CHECKING_TO_DESIGN
    if not IS_CHECKING_TO_DESIGN:
        context.user_data['Checking_article_message'] = context.bot.send_document(
            chat_id=update.effective_message.chat_id,
            document=article_list[article_index]['file_id'],
            caption=f'Автор: *{article_list[article_index]["author"]}*\n\nДедлайн: *{article_list[article_index]["deadline"]}*',
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=get_cardmaker_ready_article_inline_keyboard(),
        )
        IS_CHECKING_TO_DESIGN = True
    else:
        context.bot.edit_message_media(
            media=InputMediaDocument(
                media=article_list[article_index]['file_id'],
                caption=f'Автор: *{article_list[article_index]["author"]}*',
                parse_mode=ParseMode.MARKDOWN,
            ),
            chat_id=update.effective_message.chat_id,
            message_id=context.user_data['Checking_article_message'].message_id,
            reply_markup=get_cardmaker_ready_article_inline_keyboard(),
        )


@debug_requests
def send_notification_to_coordinator_and_author(update: Update, context: CallbackContext):
    coordinator_chat_id = get_user_chat_id_by_role(user_role='Coordinator')
    file_id = get_file_from_list_to_design(article_id=context.user_data['CARDMAKER_ARTICLE_ID'])
    context.bot.send_document(
        chat_id=coordinator_chat_id,
        document=file_id,
        caption=f'*✉️ {context.user_data["Name"]} уведомляет о готовности статьи*',
        parse_mode=ParseMode.MARKDOWN
    )
    author_chat_id = get_author_chat_id_from_list_to_design(article_id=context.user_data['CARDMAKER_ARTICLE_ID'])
    context.bot.send_document(
        chat_id=author_chat_id,
        document=file_id,
        caption=f'*✉️ Ваша статья готова и в ближайщее время будет опубликована на канале*',
        parse_mode=ParseMode.MARKDOWN
    )
    global IS_CHECKING_TO_DESIGN
    IS_CHECKING_TO_DESIGN = False


@debug_requests
def update_cardmaker_menu(update: Update, context: CallbackContext):
    context.bot.delete_message(
        chat_id=update.effective_message.chat_id,
        message_id=update.callback_query.message.message_id
    )
    set_article_readiness(article_id=context.user_data['CARDMAKER_ARTICLE_ID'])
    article_list = get_list_to_design(cardmaker=context.user_data['Name'])
    if len(article_list) != 0:
        context.bot.edit_message_text(
            chat_id=update.effective_message.chat_id,
            text=CHOOSE_ARTICLE_MESSAGE,
            reply_markup=get_article_list_inline_keyboard(article_list),
            message_id=context.user_data['CARDMAKER_MENU_MESSAGE_ID']
        )
    else:
        context.bot.edit_message_text(
            chat_id=update.effective_message.chat_id,
            text=ARTICLE_LIST_EMPTY_MESSAGE,
            parse_mode=ParseMode.MARKDOWN,
            message_id=context.user_data['CARDMAKER_MENU_MESSAGE_ID']
        )
