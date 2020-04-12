import logging.config
from logging import getLogger

TG_TOKEN = '1128654519:AAGoKI1M5bobkcKu5USZVO8HP-q4jEimtlM'
TG_API_URL = 'http://telegg.ru/orig/bot'

LOGGING = {
    'disable_existing_loggers': True,
    'version': 1,
    'formatters': {
        'verbose': {
            'format': '%(levelname)s %(module)s.%(funcName)s | %(asctime)s | %(message)s',
            'datefmt': '%Y-%m-d %H-%M-%S'
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'level': 'DEBUG',
            'formatter': 'verbose',
        },
    },
    'loggers': {
        '': {
            'handlers': ['console'],
            'level': 'INFO',
            'propagate': False,
        },
    },
}
logging.config.dictConfig(LOGGING)


def debug_requests(f):
    def inner(*args, **kwargs):
        try:
            getLogger(__name__).info(f'Обращение в функцию {f.__name__}')
            return f(*args, **kwargs)
        except Exception as e:
            getLogger(__name__).exception(f'Ошибка в обработчике {f.__name__}')
            raise e

    return inner
