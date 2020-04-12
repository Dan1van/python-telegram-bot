from telegram import Update
from telegram import ParseMode
from telegram.ext import CallbackContext
from telegram.ext import ConversationHandler
from telegram.ext import MessageHandler
from telegram.ext import Filters

from bot.config import debug_requests
from bot.db import get_user_chat_id_by_role
from bot.db import set_approval_list
from bot.db import get_weekly_useful_info
from bot.db import set_approval_list_by_coordinator
from bot.keyboard import AUTHOR
from bot.keyboard import get_conversation_cancel_reply_keyboard
from bot.keyboard import get_base_reply_keyboard
from bot.keyboard import get_new_approve_article_notification_inline_keyboard

AUTHOR_DOCUMENT = 2


@debug_requests
def author_send_document_start(update: Update, context: CallbackContext):
    if context.user_data['Role'] == 'Author':
        update.message.reply_text(
            'Отправьте материал в формате *.docx*',
            reply_markup=get_conversation_cancel_reply_keyboard(),
            parse_mode=ParseMode.MARKDOWN,
        )

        return AUTHOR_DOCUMENT
    else:
        update.message.reply_text(
            'Упс... Кажется вы ввели неверную команду'
        )

        return ConversationHandler.END


@debug_requests
def author_document_handler(update: Update, context: CallbackContext):
    if update.message.text != 'Отменить':
        try:
            return author_try_send_document(update=update, context=context)
        except AttributeError:
            return author_sending_document_error(update=update, context=context)
    else:
        return sending_document_conversation_cancel_handler(update=update, context=context)


def author_try_send_document(update: Update, context: CallbackContext):
    file_id = update.message.document.file_id
    file_mime_type = update.message.document.mime_type

    if is_docx(file_type=file_mime_type):
        add_new_article_to_approve(update=update, context=context, file_id=file_id)
        send_new_article_notification_to_supervisor(update=update, context=context)

        return ConversationHandler.END
    else:
        return author_sending_document_error(update=update, context=context)


def is_docx(file_type: str):
    return file_type == 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'


def add_new_article_to_approve(update: Update, context: CallbackContext, file_id: str):
    if context.user_data['Role'] == 'Author':
        set_approval_list(author_name=context.user_data['Name'], file_id=file_id)
    elif context.user_data['Role'] == 'Coordinator':
        print(context.user_data['send_by_author_name'])
        set_approval_list_by_coordinator(author_name=context.user_data['send_by_author_name'], file_id=file_id)
    update.message.reply_text(
        'Ваш материал был успешно отправлен на обработку',
        reply_markup=get_base_reply_keyboard(context.user_data['Role']),
    )


def send_new_article_notification_to_supervisor(update: Update, context: CallbackContext):
    supervisor_chat_id = get_user_chat_id_by_role(user_role='Supervisor')
    context.bot.send_message(
        chat_id=supervisor_chat_id,
        text='Поступил новый материал на одобрение',
        reply_markup=get_new_approve_article_notification_inline_keyboard(),
    )


@debug_requests
def author_sending_document_error(update: Update, context: CallbackContext):
    update.message.reply_text('Упс... Это не документ. Попробуйте снова')

    return AUTHOR_DOCUMENT


@debug_requests
def sending_document_conversation_cancel_handler(update: Update, context: CallbackContext):
    update.message.reply_text(
        'Отправка материала была отменена',
        reply_markup=get_base_reply_keyboard(context.user_data['Role']),
    )

    return ConversationHandler.END


send_document_handler = ConversationHandler(
    entry_points=[
        MessageHandler(Filters.regex(AUTHOR['SEND_ARTICLE_BUTTON']), author_send_document_start),
    ],
    states={
        AUTHOR_DOCUMENT: [
            MessageHandler(Filters.all, author_document_handler, pass_user_data=True)
        ],
    },
    fallbacks=[]
)


@debug_requests
def author_messages(update: Update, context: CallbackContext):
    if update.effective_message.text == AUTHOR['USEFUL_INFO_BUTTON']:
        send_author_useful_info(update=update, context=context)
    else:
        update.message.reply_text('Упс... Кажется вы ввели неверную команду')


@debug_requests
def send_author_useful_info(update: Update, context: CallbackContext):
    send_teaching_material(update=update, context=context)
    send_weekly_useful_materials(update=update, context=context)


@debug_requests
def send_teaching_material(update: Update, context: CallbackContext):
    update.message.reply_text(
        '<b>Методический материал для авторов:</b>\n\n<a '
        'href="https://drive.google.com/file/d/1LqcPFLVYFiPzbsiivBSsqq0TQtku1RAa/view?usp=sharing">Ссылка на '
        'документ</a>\n',
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