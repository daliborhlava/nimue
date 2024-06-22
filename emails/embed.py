import os

from pathlib import Path

import pickle
import time

from tqdm import tqdm

from langchain_community.document_loaders import TextLoader

import pandas as pd

import json

from shared import detect_encoding, num_tokens_from_string, tokens_price, init_logger
from constants import ANALYTICS_PATH

JUST_COUNT = True
REGENERATE_IF_EXISTS = False
PRICE_PER_MEGA_TOKENS = 0.13

logger = init_logger()

secrets_file_name = 'project.secrets'
with open(secrets_file_name, "r") as secrets_file:
    secrets_data = json.load(secrets_file)

stats = {
    'total-tokens': 0
}

start_time = time.perf_counter()

processed_dir = secrets_data["processed-dir"]
file_list = [f for f in Path(processed_dir).glob('**/*.txt')]
sorted_file_list = sorted(file_list)

stats['total-files'] = len(sorted_file_list)

logger.info('Starting...')
logger.info(f"Total files to process: {stats['total-files']:,}")

ctr = 1
ctr_total = len(sorted_file_list)

df_token_data = []

for item in tqdm(sorted_file_list, desc="Processing files"):
    item_path = item.as_posix()

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
    stats['total-tokens'] += tokens

    logger.debug(f"{ctr:,}/{ctr_total:,}: +{tokens:,}; path: {item_path}")

    df_token_data.append({
        'ctr': ctr,
        'tokens': tokens,
        'tokens_price': tokens_price(tokens, PRICE_PER_MEGA_TOKENS),
        'name': item.name,
        'full-path': item_path
    })

    # Implement the making of embeding
    # after testing it not exists
    # or regen and owerwriting if needed
    if not JUST_COUNT:
        1/0
        pass

    ctr += 1

total_price = tokens_price(stats['total-tokens'], PRICE_PER_MEGA_TOKENS)
logger.info(f"Result: {stats['total-tokens']:,} -> {total_price:,} USD")

df = pd.DataFrame(df_token_data)

pickle_df_path = os.path.join(ANALYTICS_PATH, "tokens_df.pkl")
pickle.dump(df, open(pickle_df_path, "wb"))

csv_path = os.path.join(ANALYTICS_PATH, "tokens.csv")
df.to_csv(csv_path, index=False)

stats['total-price'] = total_price

logger.info('Done')

logger.info(f'Stats: {stats}')

end_time = time.perf_counter()
elapsed_time = end_time - start_time

logger.info(f'Successfully completed in {elapsed_time/60:.1f} minutes.')