import os

from pathlib import Path

import pickle
import time

from tqdm import tqdm

import argparse

from langchain_community.document_loaders import TextLoader

import openai
from openai import OpenAI

import pandas as pd

import json

from shared import detect_encoding, num_tokens_from_string, tokens_price, init_logger, get_embedding
from constants import ANALYTICS_PATH, EMBEDDING_EXTENSION, EMBEDDING_MODEL

logger = init_logger('embed')

parser = argparse.ArgumentParser(description="Nimue Email Embedder")
parser.add_argument("-e", "--embed", help="Perform the embedding", action="store_true")
parser.add_argument("-o", "--overwrite", help="If embedding file already exists, regenerate it",
                    action="store_true")
parser.add_argument("-p", "--price-per-mil-tokens", help="Price for embedding 1 million tokens (default 0.13 USD)",
                    type=float, default=0.13)
parser.add_argument("-l", "--limit", help="Maximum files to process (default 0 = unlimited)",
                    type=int, default=0)
args = parser.parse_args()

if args.embed:
    if os.getenv("OPENAI_API_KEY") is not None:
        client = OpenAI()
        client.api_key = os.getenv("OPENAI_API_KEY")
    else:
        msg = "OPENAI_API_KEY environment variable not found"
        logger.critical(msg)
        raise Exception(msg)

PERFORM_EMBEDDING = args.embed
REGENERATE_IF_EXISTS = args.overwrite
PRICE_PER_MEGA_TOKENS = args.price_per_mil_tokens
LIMIT_FILES = args.limit

secrets_file_name = 'project.secrets'
with open(secrets_file_name, "r") as secrets_file:
    secrets_data = json.load(secrets_file)

stats = {
    'total-files-to-process': -1,
    'total-files-processed': -1,
    'total-tokens': 0,
    'total-files-embedded': 0
}

start_time = time.perf_counter()

processed_dir = secrets_data["processed-dir"]
file_list = [f for f in Path(processed_dir).glob('**/*.txt')]
sorted_file_list = sorted(file_list)

if LIMIT_FILES > 0:
    sorted_file_list = sorted_file_list[:LIMIT_FILES]

stats['total-files-to-process'] = len(sorted_file_list)

logger.info('Starting...')
if PERFORM_EMBEDDING:
    logger.info('Embedding enabled')
    logger.info(f"Price per million tokens: {PRICE_PER_MEGA_TOKENS}")
    if REGENERATE_IF_EXISTS:
        logger.info("Regenerating embedding files if they already exist")
    else:
        logger.info("Skipping embedding generation if files already exist")
else:
    logger.info('Embedding generation disabled, use -e to enable')
    
if LIMIT_FILES > 0:
    logger.info(f"Limiting files to process to {LIMIT_FILES:,}")

logger.info(f"Total files to process: {stats['total-files-to-process']:,}")

ctr = 1

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

    logger.debug(f"{ctr:,}/{stats['total-files-to-process']:,}: +{tokens:,}; path: {item_path}")

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
    if PERFORM_EMBEDDING:
        embedding_file_path = item.with_suffix(f".{EMBEDDING_EXTENSION}").as_posix()

        # Conditional embedding generation
        if REGENERATE_IF_EXISTS or not os.path.exists(embedding_file_path):
            try:
                embedding = get_embedding(client, original_text, model=EMBEDDING_MODEL)
                stats['total-files-embedded'] += 1

                # Save the embedding in a pickle file
                with open(embedding_file_path, 'wb') as f:
                    pickle.dump(embedding, f)

                logger.debug(f"Embedding created for: {item_path} at {embedding_file_path}")

            except openai.BadRequestError as e:
                logger.error(f"Bad request to OpenAI API: {e}")
            except openai.APIError as e:
                logger.error(f"OpenAI API error: {e}")
            except Exception as e:  # Catch-all for other errors
                logger.error(f"Unexpected error while creating embedding: {e}")
                raise e
        else:
            logger.debug(f"Skipping embedding generation for: {item_path} (already exists). "
                         "Use parameter -o to regenerate.")

    ctr += 1

stats['total-files-processed'] = ctr - 1


total_price = tokens_price(stats['total-tokens'], PRICE_PER_MEGA_TOKENS)
logger.info(f"Total tokens: {stats['total-tokens']:,} -> price: {total_price:,} USD")

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
