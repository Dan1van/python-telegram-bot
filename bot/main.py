from telegram import Bot
from telegram import Update
from telegram.ext import CommandHandler
from telegram.ext import MessageHandler
from telegram.ext import CallbackContext
from telegram.ext import CallbackQueryHandler
from telegram.ext import Filters
from telegram.ext import Updater
from telegram.utils.request import Request

from bot.config import load_config
from bot.config import debug_requests
from db import init_db
from db import get_user_info
from db import set_user_chat_id
from bot.keyboard import get_base_reply_keyboard
from bot.author import send_document_handler
from bot.author import author_messages
from bot.supervisor import disapprove_article_conversation_handler
from bot.supervisor import supervisor_inline_keyboard
from bot.supervisor import supervisor_messages
from bot.coordinator import coordinator_inline_keyboard
from bot.coordinator import coordinator_messages
from bot.coordinator import send_article_by_author_handler
from bot.coordinator import send_newsletter_handler
from bot.coordinator import setup_new_member
from bot.cardmaker import cardmaker_inline_keyboard
from bot.cardmaker import cardmaker_messages


@debug_requests
def start(update: Update, context: CallbackContext):
    try:
        authorize_user_in_system(update=update, context=context)
    except TypeError:
        update.message.reply_text('Упс... Кажется Вы ошиблись ботом.')


@debug_requests
def authorize_user_in_system(update: Update, context: CallbackContext):
    set_user_chat_id(user_id=update.effective_user.id, chat_id=update.effective_chat.id)
    context.user_data['Name'], context.user_data['Role'], context.user_data['Chat_ID'] = get_user_info(
        user_id=update.effective_user.id)
    user_name = context.user_data['Name'].split()
    update.message.reply_text(
        f"{user_name[0]}, Вас приветствует бот «Хакнем Школа»!",
        reply_markup=get_base_reply_keyboard(member_role=context.user_data['Role']),
    )


@debug_requests
def messages(update: Update, context: CallbackContext):
    if context.user_data['Role'] == 'Supervisor':
        supervisor_messages(update=update, context=context)
    elif context.user_data['Role'] == 'Coordinator':
        coordinator_messages(update=update, context=context)
    elif context.user_data['Role'] == 'Cardmaker':
        cardmaker_messages(update=update, context=context)
    elif context.user_data['Role'] == 'Author':
        author_messages(update=update, context=context)


@debug_requests
def inline_keyboard(update: Update, context: CallbackContext):
    if context.user_data['Role'] == 'Supervisor':
        supervisor_inline_keyboard(update=update, context=context)
    elif context.user_data['Role'] == 'Coordinator':
        coordinator_inline_keyboard(update=update, context=context)
    elif context.user_data['Role'] == 'Cardmaker':
        cardmaker_inline_keyboard(update=update, context=context)
    elif context.user_data['Role'] == 'Author':
        pass


@debug_requests
def help_func(update: Update, context: CallbackContext):
    context.bot.send_message(
        chat_id=update.effective_message.chat_id,
        text='По всем вопросам обращаться: @dan1van'
    )


@debug_requests
def main():
    config = load_config()
    req = Request(
        connect_timeout=0.5,
    )
    bot = Bot(
        request=req,
        token=config.TG_TOKEN,
        base_url=config.TG_API_URL,
    )
    updater = Updater(
        bot=bot,
        use_context=True,
    )
    init_db()

    start_handler = CommandHandler('start', start)
    messages_handler = MessageHandler(Filters.all, messages)
    inline_keyboard_handler = CallbackQueryHandler(callback=inline_keyboard)
    help_handler = CommandHandler('help', help_func)

    dp = updater.dispatcher
    dp.add_handler(start_handler)
    dp.add_handler(help_handler)
    dp.add_handler(send_document_handler)
    dp.add_handler(disapprove_article_conversation_handler)
    dp.add_handler(send_article_by_author_handler)
    dp.add_handler(send_newsletter_handler)
    dp.add_handler(setup_new_member)
    dp.add_handler(inline_keyboard_handler)
    dp.add_handler(messages_handler)

    updater.start_polling()
    updater.idle()


if __name__ == '__main__':
    main()
