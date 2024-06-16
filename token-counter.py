import os
import sys

import tiktoken

from langchain_community.document_loaders import TextLoader

import json
import chardet

price_per_mil_token = 0.13

secrets_file_name = 'project.secrets'
with open(secrets_file_name, "r") as secrets_file:
    secrets_data = json.load(secrets_file)


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

total_tokens = 0

data_dir = secrets_data["data-dir"]
file_list = os.listdir(data_dir)
sorted_file_list = sorted(file_list)

ctr = 1
ctr_total = len(sorted_file_list)

for item in sorted_file_list:
    item_path = os.path.join(data_dir, item)

    encoding = detect_encoding(item_path)

    loader = TextLoader(item_path, encoding=encoding)
    docs = loader.load()

    doc_ctr = 0
    original_text = ""
    for doc in docs:
        assert doc_ctr == 0, "Only one document per file is supported."
        original_text += doc.page_content

        doc_ctr += 1

    tokens = num_tokens_from_string(original_text, "cl100k_base")
    total_tokens += tokens

    total_price = tokens_price(total_tokens, price_per_mil_token)

    print(f"{ctr:,}/{ctr_total:,}: +{tokens:,} = {total_tokens:,} -> {total_price:,} USD; path: {item_path}")

    ctr += 1

print()
print('================')
print()

total_price = tokens_price(total_tokens, price_per_mil_token)
print(f"{total_tokens:,} -> {total_price:,} USD")