from telegram import Update
from telegram import ParseMode
from telegram.ext import CallbackContext
from telegram.ext import MessageHandler
from telegram.ext import Filters
from telegram.ext import CallbackQueryHandler
from telegram.ext import ConversationHandler

from bot.config import debug_requests
from db import get_approval_list
from db import get_user_chat_id_by_role
from db import set_approved_list
from db import delete_approval_list
from bot.keyboard import SUPERVISOR
from bot.keyboard import ARTICLE_APPROVING
from bot.keyboard import get_base_reply_keyboard
from bot.keyboard import get_article_list_inline_keyboard
from bot.keyboard import get_article_approve_inline_keyboard
from bot.keyboard import get_new_approved_article_notification_inline_keyboard
from bot.keyboard import get_conversation_cancel_reply_keyboard

MESSAGES_TO_DELETE = []

SEND_COMMENT = 1


@debug_requests
def supervisor_messages(update: Update, context: CallbackContext):
    if update.effective_message.text == SUPERVISOR['SHOW_ARTICLE_LIST_BUTTON']:
        show_approval_article_list_menu(update=update, context=context)
    else:
        update.message.reply_text('Упс... Кажется вы ввели неверную команду')


@debug_requests
def show_approval_article_list_menu(update: Update, context: CallbackContext):
    article_list = get_approval_list()
    if len(article_list) != 0:
        context.bot.send_message(
            chat_id=update.effective_message.chat_id,
            text='*Выберите статью из списка:*',
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=get_article_list_inline_keyboard(article_list),
        )
    else:
        update.message.reply_text(
            '*Сейчас нет статей, требующих проверки ✅*',
            parse_mode=ParseMode.MARKDOWN
        )


def supervisor_inline_keyboard(update: Update, context: CallbackContext):
    query = update.callback_query
    try:
        int(query.data)
        operation_type = 'Choosing article'
    except ValueError:
        data = query.data
        operation_type = data

    if operation_type == 'Choosing article':
        show_approval_article(update=update, context=context)
    elif operation_type == SUPERVISOR['SHOW_ARTICLE_LIST_BUTTON']:
        show_approval_article_list_menu(update=update, context=context)
    elif operation_type == ARTICLE_APPROVING['APPROVE']:
        send_approved_article(update=update, context=context)
        update_approval_list_menu(update=update, context=context)


@debug_requests
def show_approval_article(update: Update, context: CallbackContext):
    query = update.callback_query
    article_list = get_approval_list()
    article_index = int(query.data) - 1
    context.user_data['Menu_ID'] = query.message.message_id
    context.user_data['Article_ID'] = article_list[article_index]['id']
    context.user_data['Article_index'] = article_index

    context.bot.send_document(
        chat_id=update.effective_message.chat_id,
        document=article_list[article_index]['file_id'],
        caption=f'Автор: *{article_list[article_index]["author"]}*',
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=get_article_approve_inline_keyboard(),
    )


@debug_requests
def send_approved_article(update: Update, context: CallbackContext):
    query = update.callback_query
    set_approved_list(id=context.user_data['Article_ID'])
    coordinator_chat_id = get_user_chat_id_by_role(user_role='Coordinator')
    context.bot.send_message(
        chat_id=coordinator_chat_id,
        text='Поступил новый одобренный материал',
        reply_markup=get_new_approved_article_notification_inline_keyboard(),
    )
    context.bot.delete_message(
        chat_id=update.effective_message.chat_id,
        message_id=query.message.message_id
    )


@debug_requests
def update_approval_list_menu(update: Update, context: CallbackContext):
    article_list = get_approval_list()
    if len(article_list) != 0:
        context.bot.edit_message_text(
            chat_id=update.effective_message.chat_id,
            text='*Выберите статью из списка:*',
            reply_markup=get_article_list_inline_keyboard(article_list),
            message_id=context.user_data['Menu_ID']
        )
    else:
        context.bot.edit_message_text(
            chat_id=update.effective_message.chat_id,
            text='*Сейчас нет статей, требующих проверки ✅*',
            parse_mode=ParseMode.MARKDOWN,
            message_id=context.user_data['Menu_ID']
        )


@debug_requests
def disapprove_conversation_start(update: Update, context: CallbackContext):
    message = context.bot.send_message(
        chat_id=update.effective_message.chat_id,
        text='Напишите комментарий автору и укажите причину отказа:',
        reply_markup=get_conversation_cancel_reply_keyboard(),
    )
    MESSAGES_TO_DELETE.append(update.effective_message.message_id)
    MESSAGES_TO_DELETE.append(message.message_id)
    return SEND_COMMENT


@debug_requests
def send_disapproved_message(update: Update, context: CallbackContext):
    text = update.effective_message.text
    MESSAGES_TO_DELETE.append(update.effective_message.message_id)
    if text != 'Отменить':
        article_list = get_approval_list()
        article_index = context.user_data['Article_index']
        author_chat_id = article_list[article_index]['chat_id']
        file_id = article_list[article_index]['file_id']
        context.bot.send_document(
            chat_id=author_chat_id,
            document=file_id,
            caption='*Ваш материал был отклонён.*\n\n_Комментарий:_ ' + text,
            parse_mode=ParseMode.MARKDOWN
        )
        delete_approval_list(id=context.user_data['Article_ID'])
        delete_disapprove_messages(update=update, context=context, text=text)
        update_approval_list_menu(update=update, context=context)
        return ConversationHandler.END
    else:
        delete_disapprove_messages(update=update, context=context, text=text)
        update_approval_list_menu(update=update, context=context)
        return ConversationHandler.END


@debug_requests
def delete_disapprove_messages(update: Update, context: CallbackContext, text: str):
    if text != 'Отменить':
        update.message.reply_text(
            'Ваш комментарий был успешно отправлен автору',
            reply_markup=get_base_reply_keyboard(member_role='Supervisor')
        )
    else:
        update.message.reply_text(
            'Отмена',
            reply_markup=get_base_reply_keyboard(member_role='Supervisor')
        )
    for message_id in MESSAGES_TO_DELETE:
        context.bot.delete_message(
            chat_id=update.effective_message.chat_id,
            message_id=message_id,
        )
    MESSAGES_TO_DELETE.clear()


disapprove_article_conversation_handler = ConversationHandler(
    entry_points=[
        CallbackQueryHandler(callback=disapprove_conversation_start, pattern=ARTICLE_APPROVING['DISAPPROVE'])
    ],
    states={
        SEND_COMMENT: [
            MessageHandler(Filters.text, send_disapproved_message)
        ],
    },
    fallbacks=[],
    allow_reentry=True,
)
