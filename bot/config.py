import importlib
import os
import sys

import logging.config
from logging import getLogger


def load_config():
    conf_name = os.environ.get('TG_CONF')
    if conf_name is None:
        conf_name = 'development'
    try:
        r = importlib.import_module(f'settings.{conf_name}')
        print(f'Loaded config {conf_name} - OK')
        return r
    except (TypeError, ImportError, ValueError):
        print(f'Invalid config {conf_name}')
        sys.exit(1)



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
