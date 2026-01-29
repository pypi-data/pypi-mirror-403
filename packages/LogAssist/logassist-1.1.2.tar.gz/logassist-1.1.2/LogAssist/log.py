import os
import sys
import logging
from logging.handlers import TimedRotatingFileHandler

logger = logging.getLogger(__name__)
initialized = False

global_config = {
    "base": {
        "name": "MyLogger",
        "level": "debug",
    },
    "console": {
        "level": "debug",
        "format": "%(asctime)s[%(levelname)s]%(message)s"
    },
    "file_timed": {
        "level": "info",
        "format": "%(asctime)s[%(levelname)s]%(message)s",
        "file_name": "default.log",
        "when": "midnight",
        "interval": 1,
        "backup_count": 30
    }
}


def _get_file_timed_handler(config):
    """
    Create a timed rotating file handler with the given configuration.

    :param config: A dictionary containing the configuration for the file handler.
    :return: A configured TimedRotatingFileHandler.
    """
    log_level = config['level'].upper()
    log_format = config['format']

    log_dir = os.path.dirname(config['file_name'])

    if log_dir != '' and not os.path.exists(log_dir):
        os.makedirs(log_dir)

    handler = TimedRotatingFileHandler(
        config['file_name'], when=config['when'], interval=config['interval'], backupCount=config['backup_count'], encoding='utf-8')

    level = getattr(logging, log_level, logging.NOTSET)
    handler.setLevel(level)
    handler.setFormatter(logging.Formatter(log_format))

    return handler


def _get_console_handler(config):
    """
    Create a console handler with the given configuration.

    :param config: A dictionary containing the configuration for the console handler.
    :return: A configured StreamHandler for console output.
    """
    console_handler = logging.StreamHandler()

    log_level = config['level'].upper()
    log_format = config['format']

    level = getattr(logging, log_level, logging.NOTSET)
    console_handler.setLevel(level)
    console_handler.setFormatter(logging.Formatter(log_format))
    console_handler.stream = open(sys.stdout.fileno(), mode='w', encoding='utf-8', buffering=1)

    return console_handler


def logger_init(config=None):
    """
    Initialize the logger with the given configuration.

    :param config: A dictionary containing the logger configuration. If None, uses global_config.
    """
    global initialized
    global global_config

    if initialized:
        return

    if config is None:
        config = global_config

    logger.handlers.clear()
    logger.setLevel(config['base']['level'].upper())

    timed_config = config.get("file_timed", None)
    console_config = config.get("console", None)

    if timed_config:
        logger.addHandler(_get_file_timed_handler(timed_config))
    if console_config:
        logger.addHandler(_get_console_handler(console_config))

    initialized = True


def _chk_msg(tag="", msg=None) -> str:
    """
    Check and format the message for logging.

    :param tag: A tag to prepend to the message.
    :param msg: The message to log.
    :return: A formatted message string.
    """
    global initialized
    if not initialized:
        logger_init()

    if msg:
        msg = f'[{tag}] {msg}'
    else:
        msg = tag
    return msg


def exception(tag="", msg=None):
    """
    Log an error message and raise an exception.

    :param tag: A tag to prepend to the message.
    :param msg: The message to log.
    """
    msg = _chk_msg(tag, msg)
    logger.error(msg)
    raise Exception(msg)


def error(tag="", msg=None):
    """
    Log an error message.

    :param tag: A tag to prepend to the message.
    :param msg: The message to log.
    """
    msg = _chk_msg(tag, msg)
    logger.error(msg)


def warn(tag="", msg=None):
    """
    Log a warning message.

    :param tag: A tag to prepend to the message.
    :param msg: The message to log.
    """
    msg = _chk_msg(tag, msg)
    logger.warn(msg)


def info(tag="", msg=None):
    """
    Log an info message.

    :param tag: A tag to prepend to the message.
    :param msg: The message to log.
    """
    msg = _chk_msg(tag, msg)
    logger.info(msg)


def debug(tag="", msg=None):
    """
    Log a debug message.

    :param tag: A tag to prepend to the message.
    :param msg: The message to log.
    """
    msg = _chk_msg(tag, msg)
    logger.debug(msg)
