

import logging

logging.basicConfig(format='[%(levelname)8s][%(name)s] %(message)s')

loggers = []


def set_level(level):
    for logger in loggers:
        logger.setLevel(level)
