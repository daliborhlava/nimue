import tiktoken
import chardet

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