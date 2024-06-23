import tiktoken
import chardet
import logging

from typing import List, Optional

import openai


def init_logger(logger_name: str = None) -> logging.Logger:
    if logger_name is None:
        logger_name = __name__

    logger = logging.getLogger(logger_name)
    logger.setLevel(logging.DEBUG)

    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s', datefmt="%Y-%m-%d %H:%M:%S")

    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(formatter)

    # Might need to be changed if emails are in differnet format.
    file_handler = logging.FileHandler(f'{logger_name}.log', encoding='UTF-8 SIG', mode='w')
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(formatter)

    logger.addHandler(console_handler)
    logger.addHandler(file_handler)

    return logger


def num_tokens_from_string(string: str, encoding_name: str) -> int:
    """Returns the number of tokens in a text string."""
    encoding = tiktoken.get_encoding(encoding_name)
    num_tokens = len(encoding.encode(string))
    return num_tokens


def tokens_price(tokens: int, price_per_mil_token: float) -> float:
    """Returns the total price for a given number of tokens."""
    total_price = tokens * price_per_mil_token / 1_000_000
    return total_price


def detect_encoding(file_path):
    with open(file_path, 'rb') as f:
        result = chardet.detect(f.read())
    return result['encoding']


#@retry(wait=wait_random_exponential(min=1, max=20), stop=stop_after_attempt(6))
def get_embedding(client: openai.OpenAI, text: str, model="text-embedding-3-small") -> List[float]:

    # replace newlines, which can negatively affect performance.
    text = text.replace("\n", " ")

    return client.embeddings.create(input=[text], model=model).data[0].embedding