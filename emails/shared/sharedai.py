import openai
from typing import List

import tiktoken


def num_tokens_from_string(string: str, encoding_name: str) -> int:
    """Returns the number of tokens in a text string."""
    encoding = tiktoken.get_encoding(encoding_name)
    num_tokens = len(encoding.encode(string))
    return num_tokens


def tokens_price(tokens: int, price_per_mil_token: float) -> float:
    """Returns the total price for a given number of tokens."""
    total_price = tokens * price_per_mil_token / 1_000_000
    return total_price


#@retry(wait=wait_random_exponential(min=1, max=20), stop=stop_after_attempt(6))
def get_embedding(client: openai.OpenAI, text: str, model="text-embedding-3-small") -> List[float]:

    # replace newlines, which can negatively affect performance.
    text = text.replace("\n", " ")

    return client.embeddings.create(input=[text], model=model).data[0].embedding