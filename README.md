# python-telegram-bot
Телеграм-бот разработанный для компании Haknem (http://haknem.com/). Требуется для автоматизации процесса подачи статей авторов, их проверки и публикации.

Принцип работы бота:

Существует 4 роли: 
* Автор статьи
* Руководитель (Оценивает статью и одобряет ее или отклоняет)
* Координатор (Человек, ответствененый за публикацию статей)
* Картмейкер (Человек, ответсвенный за оформление "карточки" статьи)

В итоге одобренная и опубликованная статья проходит путь:

Автор --> Руководитель --> Координатор --> Картмейкер --> Координатор
## Установка
settings/production.py

`TG_TOKEN = '1128654519:AAGoKI1M5bobkcKu5USZVO2HP-q4jEimtlM'`

Требуется ввести токен своего телеграм-бота.

Затем запустить bot/main.py.
____
# English
Telegram-bot developed for Haknem company (http://haknem.com/). This bot was designed to automate the process of sending articles, their verification and publication. 
## Install
settings/production.py

`TG_TOKEN = '1128654519:AAGoKI1M5bobkcKu5USZVO2HP-q4jEimtlM'`

It's required to enter your bot's token.

Then start bot/main.py process.
