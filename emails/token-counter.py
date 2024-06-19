import os
import sys
import glob

from langchain_community.document_loaders import TextLoader

import pandas as pd

import json

from shared import detect_encoding, num_tokens_from_string, tokens_price

price_per_mil_token = 0.13

secrets_file_name = 'project.secrets'
with open(secrets_file_name, "r") as secrets_file:
    secrets_data = json.load(secrets_file)

total_tokens = 0

data_dir = secrets_data["data-dir"]
processed_dir = os.path.join(data_dir, 'ingest-processed')
file_list =  glob.glob(os.path.join(processed_dir, '*.txt'))
sorted_file_list = sorted(file_list)

ctr = 1
ctr_total = len(sorted_file_list)

df_data = []

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

    df_data.append({
        'ctr': ctr,
        'tokens': tokens,
        'tokens_price': tokens_price(tokens, price_per_mil_token),
        'name': item
    })

    ctr += 1

print()
print('================')
print()

total_price = tokens_price(total_tokens, price_per_mil_token)
print(f"{total_tokens:,} -> {total_price:,} USD")

pd.DataFrame.from_records(df_data).to_csv('tokens.csv', index=False)