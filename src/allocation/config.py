import inspect
import logging
import os


def get_redis_config():
    return (
        os.getenv('REDIS_HOST', 'localhost'),
        os.getenv('REDIS_PORT', 6379)
    )


def get_logger():
    caller_frame = inspect.stack()[1]
    caller_module = caller_frame.frame.f_globals["__name__"]
    logger = logging.getLogger(caller_module)

    if logger.hasHandlers():
        logger.handlers.clear()

    filename = os.path.join(os.getcwd(), 'logs.log')
    file_handler = logging.FileHandler(filename, mode='a')
    formatter = logging.Formatter('%(asctime)s -- %(levelname)s: %(message)s',
                                "%Y-%m-%d %H:%M:%S")
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)
    logger.setLevel(logging.DEBUG)
    return logger
