from telegram import KeyboardButton
from telegram import ReplyKeyboardMarkup
from telegram import InlineKeyboardButton
from telegram import InlineKeyboardMarkup

from bot.config import debug_requests
from bot.db import get_cardmaker_article_count
from bot.db import get_users

AUTHOR = {
    'SEND_ARTICLE_BUTTON': 'Отправить материал ✉️',
    'USEFUL_INFO_BUTTON': 'Полезная информация 💡'
}

SUPERVISOR = {
    'SHOW_ARTICLE_LIST_BUTTON': 'Показать неодобренные статьи 🗂'
}

COORDINATOR = {
    'SHOW_ARTICLE_LIST_BUTTON': 'Показать одобренные статьи 🗂',
    'SEND_ARTICLE_BY_AUTHOR_BUTTON': 'Отправить материал за автора ✉️',
    'NEWSLETTER_BUTTON': 'Рассылка участникам 📤',
    'ADD_NEW_MEMBER': 'Добавить нового участника 👤',
    'REMOVE_MEMBER': 'Удалить участника ❌'
}

CARDMAKER = {
    'SHOW_ARTICLE_LIST_BUTTON': 'Показать статьи на оформление 🗂',
    'USEFUL_INFO_BUTTON': 'Полезная информация 💡'
}

ARTICLE_APPROVING = {
    'APPROVE': 'Одобрить ✅️',
    'DISAPPROVE': 'Отклонить ⛔️'
}

DEADLINE_OPTIONS = {
    'one_day': '1️⃣ день',
    'two_days': '2️⃣ дня',
    'three_days': '3️⃣ дня',
    'four_days': '4️⃣ дня',
}


@debug_requests
def get_author_reply_keyboard():
    keyboard = [
        [
            KeyboardButton(AUTHOR['SEND_ARTICLE_BUTTON']),
            KeyboardButton(AUTHOR['USEFUL_INFO_BUTTON']),
        ],
    ]
    return ReplyKeyboardMarkup(
        keyboard=keyboard,
        resize_keyboard=True,
    )


@debug_requests
def get_supervisor_reply_keyboard():
    keyboard = [
        [
            KeyboardButton(SUPERVISOR['SHOW_ARTICLE_LIST_BUTTON']),
        ],
    ]
    return ReplyKeyboardMarkup(
        keyboard=keyboard,
        resize_keyboard=True,
    )


@debug_requests
def get_coordinator_reply_keyboard():
    keyboard = [
        [
            KeyboardButton(COORDINATOR['SHOW_ARTICLE_LIST_BUTTON']),
            KeyboardButton(COORDINATOR['SEND_ARTICLE_BY_AUTHOR_BUTTON'])
        ],
        [
            KeyboardButton(COORDINATOR['NEWSLETTER_BUTTON']),
            KeyboardButton(COORDINATOR['ADD_NEW_MEMBER'])
        ],
        [
            KeyboardButton(COORDINATOR['REMOVE_MEMBER']),
        ]
    ]
    return ReplyKeyboardMarkup(
        keyboard=keyboard,
        resize_keyboard=True,
    )


@debug_requests
def get_cardmaker_reply_keyboard():
    keyboard = [
        [
            KeyboardButton(CARDMAKER['SHOW_ARTICLE_LIST_BUTTON']),
            KeyboardButton(CARDMAKER['USEFUL_INFO_BUTTON'])
        ],
    ]
    return ReplyKeyboardMarkup(
        keyboard=keyboard,
        resize_keyboard=True,
    )


@debug_requests
def get_base_reply_keyboard(member_role: str):
    working_keyboard = None

    if member_role == 'Author':
        working_keyboard = get_author_reply_keyboard()
    elif member_role == 'Supervisor':
        working_keyboard = get_supervisor_reply_keyboard()
    elif member_role == 'Coordinator':
        working_keyboard = get_coordinator_reply_keyboard()
    elif member_role == 'Cardmaker':
        working_keyboard = get_cardmaker_reply_keyboard()

    return working_keyboard


@debug_requests
def get_conversation_cancel_reply_keyboard():
    keyboard = [
        [
            KeyboardButton('Отменить'),
        ],
    ]
    return ReplyKeyboardMarkup(
        keyboard=keyboard,
        resize_keyboard=True,
    )


def get_new_approve_article_notification_inline_keyboard():
    keyboard = [
        [
            InlineKeyboardButton(SUPERVISOR['SHOW_ARTICLE_LIST_BUTTON'],
                                 callback_data=SUPERVISOR['SHOW_ARTICLE_LIST_BUTTON'])
        ],
    ]
    return InlineKeyboardMarkup(keyboard)


def get_article_list_inline_keyboard(article_list: list):
    keyboard = []
    i = 1

    for article in article_list:
        if 'deadline' in article:
            text = f'Статья №{i}. Дедлайн: {article["deadline"]} по МСК'
            keyboard.append([InlineKeyboardButton(text, callback_data=f'Cardmaker {i}')])
        else:
            text = f'Статья №{i}. Автор: {article["author"]}'
            keyboard.append([InlineKeyboardButton(text, callback_data=f'Coordinator {i}')])
        i += 1

    return InlineKeyboardMarkup(keyboard)


def get_article_approve_inline_keyboard():
    keyboard = [
        [
            InlineKeyboardButton(ARTICLE_APPROVING['APPROVE'], callback_data=ARTICLE_APPROVING['APPROVE']),
            InlineKeyboardButton(ARTICLE_APPROVING['DISAPPROVE'], callback_data=ARTICLE_APPROVING['DISAPPROVE']),
        ],
    ]

    return InlineKeyboardMarkup(keyboard)


def get_new_approved_article_notification_inline_keyboard():
    keyboard = [
        [
            InlineKeyboardButton(COORDINATOR['SHOW_ARTICLE_LIST_BUTTON'],
                                 callback_data=COORDINATOR['SHOW_ARTICLE_LIST_BUTTON'])
        ]
    ]

    return InlineKeyboardMarkup(keyboard)


def get_cardmaker_list_inline_keyboard(cardmaker_list: list):
    keyboard = []

    for cardmaker in cardmaker_list:
        count = str(get_cardmaker_article_count(cardmaker=cardmaker['name']))
        text = 'Картмейкер: ' + cardmaker['name'] + ' (' + count + ')'

        keyboard.append([InlineKeyboardButton(text, callback_data=cardmaker['name'])])

    return InlineKeyboardMarkup(keyboard)


def get_cardmaker_deadline_inline_keyboard():
    keyboard = [
        [
            InlineKeyboardButton(DEADLINE_OPTIONS['one_day'], callback_data='1_day'),
            InlineKeyboardButton(DEADLINE_OPTIONS['two_days'], callback_data='2_days'),
        ],
        [
            InlineKeyboardButton(DEADLINE_OPTIONS['three_days'], callback_data='3_days'),
            InlineKeyboardButton(DEADLINE_OPTIONS['four_days'], callback_data='4_days'),
        ]
    ]

    return InlineKeyboardMarkup(keyboard)


def get_new_to_design_article_notification_inline_keyboard():
    keyboard = [
        [
            InlineKeyboardButton(CARDMAKER['SHOW_ARTICLE_LIST_BUTTON'],
                                 callback_data=CARDMAKER['SHOW_ARTICLE_LIST_BUTTON'])
        ],
    ]

    return InlineKeyboardMarkup(keyboard)


def get_cardmaker_ready_article_inline_keyboard():
    keyboard = [
        [
            InlineKeyboardButton('Оформлено ✅', callback_data='Article is ready')
        ],
    ]

    return InlineKeyboardMarkup(keyboard)


def get_choose_newsletter_type():
    keyboard = [
        [
            InlineKeyboardButton('Авторам', callback_data='For authors')
        ],
        [
            InlineKeyboardButton('Картмейкерам', callback_data='For cardmakers')
        ],
    ]
    return InlineKeyboardMarkup(keyboard)


def get_new_member_choose_role():
    keyboard = [
        [
            InlineKeyboardButton('Автор', callback_data='Author')
        ],
        [
            InlineKeyboardButton('Картмейкер', callback_data='Cardmaker')
        ],
    ]
    return InlineKeyboardMarkup(keyboard)


def get_members_to_remove_inline_keyboard():
    keyboard = []
    users = get_users()
    for user in users:
        keyboard.append([InlineKeyboardButton(f'{user[0]} ({user[1]})', callback_data=f'Remove {user[0]}')])

    return InlineKeyboardMarkup(keyboard)