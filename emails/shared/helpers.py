import os

import chardet
import logging


def init_logger(logger_name: str = None, logger_dir: str = None) -> logging.Logger:
    if logger_name is None:
        logger_name = __name__

    logger_path = f'{logger_name}.log'
    if logger_dir is not None:
        logger_path = os.path.join(logger_dir, logger_path)

    logger = logging.getLogger(logger_name)
    logger.setLevel(logging.DEBUG)

    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s', datefmt="%Y-%m-%d %H:%M:%S")

    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(formatter)

    # Might need to be changed if emails are in differnet format.
    file_handler = logging.FileHandler(logger_path, encoding='UTF-8 SIG', mode='w')
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(formatter)

    logger.addHandler(console_handler)
    logger.addHandler(file_handler)

    return logger


def detect_encoding(file_path):
    with open(file_path, 'rb') as f:
        result = chardet.detect(f.read())
    return result['encoding']