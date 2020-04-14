from datetime import datetime, timedelta
import time

from telegram import Update
from telegram import ParseMode
from telegram.ext import CallbackContext
from telegram.ext import CallbackQueryHandler
from telegram.ext import MessageHandler
from telegram.ext import ConversationHandler
from telegram.ext import Filters
from telegram.ext.dispatcher import run_async

from bot.config import debug_requests
from bot.db import get_approved_list
from bot.db import get_cardmakers_list
from bot.db import member_chat_id
from bot.db import set_list_to_design
from bot.db import get_article_readiness
from bot.db import delete_list_to_design
from bot.db import get_newsletter_chat_ids
from bot.db import set_weekly_useful_info
from bot.db import set_user_info
from bot.db import remove_user
from bot.keyboard import COORDINATOR
from bot.keyboard import get_article_list_inline_keyboard
from bot.keyboard import get_cardmaker_list_inline_keyboard
from bot.keyboard import get_cardmaker_deadline_inline_keyboard
from bot.keyboard import get_new_to_design_article_notification_inline_keyboard
from bot.keyboard import get_base_reply_keyboard
from bot.keyboard import get_conversation_cancel_reply_keyboard
from bot.keyboard import get_choose_newsletter_type
from bot.keyboard import get_new_member_choose_role
from bot.keyboard import get_members_to_remove_inline_keyboard
from bot.author import author_document_handler

AUTHOR_NAME, COORDINATOR_DOCUMENT = 1, 2

NEWSLETTER_TEXT = 1

NEW_MEMBER_NAME, NEW_MEMBER_ROLE, NEW_MEMBER_ID = 1, 2, 3


@debug_requests
def coordinator_messages(update: Update, context: CallbackContext):
    if update.effective_message.text == COORDINATOR['SHOW_ARTICLE_LIST_BUTTON']:
        show_approved_list(update=update, context=context)
    elif update.effective_message.text == COORDINATOR['NEWSLETTER_BUTTON']:
        choose_newsletter_type(update=update, context=context)
    elif update.effective_message.text == COORDINATOR['REMOVE_MEMBER']:
        choose_member_to_remove(update=update, context=context)
    else:
        update.message.reply_text('Упс... Кажется вы ввели неверную команду')


@debug_requests
def show_approved_list(update: Update, context: CallbackContext):
    article_list = get_approved_list()
    if len(article_list) != 0:
        context.bot.send_message(
            chat_id=update.effective_message.chat_id,
            text='*Выберите статью из списка:*',
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=get_article_list_inline_keyboard(article_list),
        )
    else:
        update.message.reply_text(
            '*Сейчас нет статей, требующих проверки*',
            parse_mode=ParseMode.MARKDOWN
        )


@debug_requests
def choose_newsletter_type(update: Update, context: CallbackContext):
    update.message.reply_text(
        '*Выберите тип рассылки:*',
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=get_choose_newsletter_type()
    )


@debug_requests
def choose_member_to_remove(update: Update, context: CallbackContext):
    update.message.reply_text(
        '*Выберите участника, которого требуется удалить из системы:*',
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=get_members_to_remove_inline_keyboard()
    )


@debug_requests
def coordinator_inline_keyboard(update: Update, context: CallbackContext):
    query = update.callback_query
    try:
        int(query.data) - 1
        operation_type = 'Choosing article'
    except ValueError:
        data = query.data
        operation_type = data

    if operation_type == 'Choosing article':
        show_cardmakers_list(update=update, context=context)
    elif was_selected_cardmaker(operation_type=operation_type):
        show_date_list(update=update, context=context)
    elif was_selected_deadline(operation_type=operation_type):
        send_to_cardmaker(update=update, context=context)
    elif was_selected_member_to_remove(operation_type=operation_type):
        remove_member(update=update, context=context)
    elif COORDINATOR['SHOW_ARTICLE_LIST_BUTTON']:
        show_approved_list(update=update, context=context)



@debug_requests
def was_selected_cardmaker(operation_type: str):
    cardmaker_list = get_cardmakers_list()
    for cardmaker in cardmaker_list:
        if cardmaker['name'] == operation_type:
            return True
    return False


@debug_requests
def was_selected_deadline(operation_type: str):
    return operation_type == '1_day' or operation_type == '2_days' or operation_type == '3_days' or operation_type == '4_days'


@debug_requests
def was_selected_member_to_remove(operation_type: str):
    return 'Remove' in operation_type


@debug_requests
def show_cardmakers_list(update: Update, context: CallbackContext):
    query = update.callback_query
    cardmaker_list = get_cardmakers_list()
    article_list = get_approved_list()
    article_index = int(query.data) - 1
    context.user_data['Article_ID'] = article_list[article_index]['id']
    context.user_data['Article_index'] = article_index

    update.callback_query.edit_message_text(
        text='Выберите картмейкера:',
        reply_markup=get_cardmaker_list_inline_keyboard(cardmaker_list)
    )


@debug_requests
def show_date_list(update: Update, context: CallbackContext):
    context.user_data['Cardmaker_name'] = update.callback_query.data

    update.callback_query.edit_message_text(
        text='Выберите дедлайн:',
        reply_markup=get_cardmaker_deadline_inline_keyboard(),
    )


@debug_requests
def send_to_cardmaker(update: Update, context: CallbackContext):
    chat_id = member_chat_id(member_name=context.user_data['Cardmaker_name'])
    date, days_count = define_date(operation_type=update.callback_query.data)
    set_list_to_design(id=context.user_data['Article_ID'], cardmaker=context.user_data['Cardmaker_name'], date=date)
    article_list = get_approved_list()
    update.callback_query.edit_message_text(
        text='*Выберите статью из списка:*',
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=get_article_list_inline_keyboard(article_list),
    )
    context.bot.send_message(
        chat_id=update.effective_message.chat_id,
        text='Статья была успешно отправлена на оформление'
    )
    context.bot.send_message(
        chat_id=chat_id,
        text='Вам была отправлена статья на оформление',
        reply_markup=get_new_to_design_article_notification_inline_keyboard()
    )
    one_hour_to_deadline_notification(update=update, context=context, chat_id=chat_id, days_count=days_count,
                                      article_id=context.user_data['Article_ID'])


@debug_requests
def define_date(operation_type: str):
    days_to_plus = 0
    if operation_type == '1_day':
        days_to_plus = 1
    elif operation_type == '2_days':
        days_to_plus = 2
    elif operation_type == '3_days':
        days_to_plus = 3
    elif operation_type == '4_days':
        days_to_plus = 4
    deadline = datetime.now() + timedelta(days=days_to_plus)
    deadline = deadline.strftime('%d.%m.%y до %H:00')
    return deadline, days_to_plus


@run_async
def one_hour_to_deadline_notification(update: Update, context: CallbackContext, chat_id: int, days_count: int,
                                      article_id: int):
    time.sleep(60 * 10 * days_count)
    if get_article_readiness(id=article_id) == 0:
        context.bot.send_message(
            chat_id=chat_id,
            text='1 час до дедлайна 😱!',
            reply_markup=get_new_to_design_article_notification_inline_keyboard()
        )
        deadline_notification(update=update, context=context, chat_id=chat_id, article_id=article_id)
    else:
        delete_list_to_design(id=article_id)


@run_async
def deadline_notification(update: Update, context: CallbackContext, chat_id: int, article_id: int):
    time.sleep(60)
    if get_article_readiness(id=article_id):
        context.bot.send_message(
            chat_id=chat_id,
            text='Вы провалили дедлайн 😢!',
            reply_markup=get_new_to_design_article_notification_inline_keyboard()
        )
    else:
        delete_list_to_design(id=article_id)


@debug_requests
def remove_member(update: Update, context: CallbackContext):
    user = update.callback_query.data.split()[1] + ' ' + update.callback_query.data.split()[2]
    remove_user(member_name=user)
    update.callback_query.edit_message_text(
        text='Вы успешно удалили ' + user,
        reply_markup=get_members_to_remove_inline_keyboard()
    )

@debug_requests
def send_article_by_author_conv_start(update: Update, context: CallbackContext):
    update.message.reply_text(
        'Введите имя автора:',
        reply_markup=get_conversation_cancel_reply_keyboard(),

    )
    return AUTHOR_NAME


@debug_requests
def set_author_name_conv_handler(update: Update, context: CallbackContext):
    text = update.effective_message.text
    if text != 'Отменить':
        context.user_data['send_by_author_name'] = text
        update.message.reply_text('Отправьте материал в формате *docx*:')
        return COORDINATOR_DOCUMENT
    else:
        update.message.reply_text(
            'Отправка материала была отменена',
            reply_markup=get_base_reply_keyboard(member_role=context.user_data['Role'])
        )
        return ConversationHandler.END


send_article_by_author_handler = ConversationHandler(
    entry_points=[
        MessageHandler(Filters.regex(COORDINATOR['SEND_ARTICLE_BY_AUTHOR_BUTTON']), send_article_by_author_conv_start)
    ],
    states={
        AUTHOR_NAME: [
            MessageHandler(Filters.all, set_author_name_conv_handler, pass_user_data=True)
        ],
        COORDINATOR_DOCUMENT: [
            MessageHandler(Filters.all, author_document_handler, pass_user_data=True)
        ],
    },
    fallbacks=[],
)


@debug_requests
def send_newsletter_start(update: Update, context: CallbackContext):
    context.bot.send_message(
        chat_id=update.effective_message.chat_id,
        text='Введите текст рассылки:',
        reply_markup=get_conversation_cancel_reply_keyboard()
    )
    context.user_data['newsletter_type'] = update.callback_query.data

    return NEWSLETTER_TEXT


@debug_requests
def send_newsletter(update: Update, context: CallbackContext):
    text = update.effective_message.text
    if text != 'Отменить':

        chat_id_list = get_newsletter_chat_ids(newsletter_type=context.user_data['newsletter_type'])
        for chat_id in chat_id_list:
            context.bot.send_message(
                chat_id=chat_id,
                text=text,
                parse_mode=ParseMode.HTML
            )

        if context.user_data['newsletter_type'] == 'For authors':
            set_weekly_useful_info(info_type='Author', text=text)
        else:
            set_weekly_useful_info(info_type='Cardmaker', text=text)

        context.bot.send_message(
            chat_id=update.effective_message.chat_id,
            text='Сообщение было успешно разослано!',
            reply_markup=get_base_reply_keyboard(context.user_data['Role'])
        )
        return ConversationHandler.END
    else:
        update.message.reply_text(
            'Отправка материала была отменена',
            reply_markup=get_base_reply_keyboard(member_role=context.user_data['Role'])
        )
        return ConversationHandler.END


send_newsletter_handler = ConversationHandler(
    entry_points=[
        CallbackQueryHandler(callback=send_newsletter_start, pattern='For *')
    ],
    states={
        NEWSLETTER_TEXT: [
            MessageHandler(Filters.all, send_newsletter)
        ]
    },
    fallbacks=[]
)


@debug_requests
def setup_new_member_start(update: Update, context: CallbackContext):
    context.bot.send_message(
        chat_id=update.effective_message.chat_id,
        text='Введите имя участника:',
        reply_markup=get_conversation_cancel_reply_keyboard(),
    )

    return NEW_MEMBER_NAME


@debug_requests
def setup_new_member_name_conv_handler(update: Update, context: CallbackContext):
    text = update.effective_message.text

    if text != 'Отменить':
        context.user_data['New_member_name'] = text
        context.bot.send_message(
            chat_id=update.effective_message.chat_id,
            text='Выберите роль нового участника:',
            reply_markup=get_new_member_choose_role()
        )

        return NEW_MEMBER_ROLE
    else:
        context.bot.send_message(
            chat_id=update.effective_message.chat_id,
            text='Отмена',
            reply_markup=get_base_reply_keyboard(member_role=context.user_data['Role'])
        )

        return ConversationHandler.END


@debug_requests
def setup_new_member_role_conv_handler(update: Update, context: CallbackContext):
    context.user_data['New_member_role'] = update.callback_query.data

    context.bot.send_message(
        chat_id=update.effective_message.chat_id,
        text='Введите user id участника',
    )

    return NEW_MEMBER_ID


@debug_requests
def setup_new_member_role_error_conv_handler(update: Update, context: CallbackContext):
    text = update.effective_message.text
    if text == 'Отменить':
        context.bot.send_message(
            chat_id=update.effective_message.chat_id,
            text='Отмена',
            reply_markup=get_base_reply_keyboard(member_role=context.user_data['Role'])
        )

        return ConversationHandler.END
    else:
        context.bot.send_message(
            chat_id=update.effective_message.chat_id,
            text='Попробуйте снова!'
        )

        return NEW_MEMBER_ROLE


@debug_requests
def setup_new_member_id_conv_handler(update: Update, context: CallbackContext):
    text = update.effective_message.text
    if text != 'Отменить':
        try:
            context.user_data['New_member_id'] = int(text)
        except ValueError:
            context.bot.send_message(
                chat_id=update.effective_message.chat_id,
                text='Неверное id, попробуйте снова!',
            )

            return NEW_MEMBER_ID

        set_user_info(user_id=context.user_data['New_member_id'],
                      member_name=context.user_data['New_member_name'],
                      role=context.user_data['New_member_role'])

        context.bot.send_message(
            chat_id=update.effective_message.chat_id,
            text='Новый участник успешно добавлен в базу данных!',
            reply_markup=get_base_reply_keyboard(member_role=context.user_data['Role'])
        )

        return ConversationHandler.END


setup_new_member = ConversationHandler(
    entry_points=[
        MessageHandler(Filters.regex(COORDINATOR['ADD_NEW_MEMBER']), setup_new_member_start)
    ],
    states={
        NEW_MEMBER_NAME: [
            MessageHandler(Filters.all, setup_new_member_name_conv_handler, pass_user_data=True)
        ],
        NEW_MEMBER_ROLE: [
            CallbackQueryHandler(callback=setup_new_member_role_conv_handler, pass_user_data=True),
            MessageHandler(Filters.all, setup_new_member_role_error_conv_handler, pass_user_data=True)
        ],
        NEW_MEMBER_ID: [
            MessageHandler(Filters.all, setup_new_member_id_conv_handler, pass_user_data=True)
        ],
    },
    fallbacks=[],
)
