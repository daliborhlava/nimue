import sys
import os

from pathlib import Path

import pickle
import time

from tqdm import tqdm

import argparse

from langchain_community.document_loaders import TextLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter

import openai
from openai import OpenAI

import pandas as pd

import json

script_dir = os.path.dirname(os.path.abspath(__file__))
root_path = os.path.join(script_dir, "..")
sys.path.append(root_path)

from shared.helpers import detect_encoding, init_logger
from shared.ai import num_tokens_from_string, tokens_price, get_embedding

from shared.constants import (
    CCY, CCY_PRICE_PER_MIL_TOKENS,
    ANALYTICS_DIR, EMBEDDINGS_EXTENSION,
    EMBEDDING_API_MAX_TOKENS,
    EMBEDDING_MODEL, EMBEDDING_CHUNK_SIZE_TOKENS, EMBEDDING_CHUNK_OVERLAP_TOKENS,
    LOGS_DIR
)

logger = init_logger('embed', logger_dir=os.path.join(root_path, LOGS_DIR)

if (EMBEDDING_CHUNK_SIZE_TOKENS > EMBEDDING_API_MAX_TOKENS or
    EMBEDDING_CHUNK_OVERLAP_TOKENS > EMBEDDING_CHUNK_SIZE_TOKENS):
    msg = ("Invalid configuration: EMBEDDING_CHUNK_SIZE_TOKENS > EMBEDDING_API_MAX_TOKENS "
    "or EMBEDDING_CHUNK_OVERLAP_TOKENS > EMBEDDING_CHUNK_SIZE_TOKENS")
    logger.critical(msg)
    raise Exception(msg)

parser = argparse.ArgumentParser(description="Nimue Email Embedder")
parser.add_argument("-e", "--embed", help="Perform the embedding", action="store_true")
parser.add_argument("-o", "--overwrite", help="If embedding file already exists, regenerate it",
                    action="store_true")
parser.add_argument("-p", "--price-per-mil-tokens",
                    help=f"Price in {CCY} for embedding 1 million tokens " 
                    f"(default {CCY_PRICE_PER_MIL_TOKENS} {CCY})",
                    type=float, default=CCY_PRICE_PER_MIL_TOKENS)
parser.add_argument("-l", "--limit", help="Maximum files to process (default 0=unlimited)",
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

text_splitter = RecursiveCharacterTextSplitter(
    chunk_size=EMBEDDING_CHUNK_SIZE_TOKENS,
    chunk_overlap=EMBEDDING_CHUNK_OVERLAP_TOKENS,
    length_function=lambda text: num_tokens_from_string(text, "cl100k_base"),
)

secrets_file_name = 'project.secrets'
secrets_path = os.path.join(script_dir, "..", secrets_file_name)

with open(secrets_path, "r") as secrets_file:
    secrets_data = json.load(secrets_file)

stats = {
    'files-to-process': -1,
    'files-processed': -1,
    'tokens-unsplitted': 0,
    'tokens-splitted': 0,
    'price-unsplitted': 0,
    'price-splitted': 0,
    'price-overhead': -1,
    'chunks': 0,
    'files-embedded': 0,
    'errors-bad-requests': 0,
    'errors-api': 0,
    'errors-other': 0
}

start_time = time.perf_counter()

processed_dir = secrets_data["processed-dir"]
file_list = [f for f in Path(processed_dir).glob('**/*.txt')]
sorted_file_list = sorted(file_list)

if LIMIT_FILES > 0:
    sorted_file_list = sorted_file_list[:LIMIT_FILES]

stats['files-to-process'] = len(sorted_file_list)

logger.info('Starting...')
if PERFORM_EMBEDDING:
    logger.info('OPTION: Embedding enabled')
    logger.info(f"Price per million tokens: {PRICE_PER_MEGA_TOKENS}")
    if REGENERATE_IF_EXISTS:
        logger.info("OPTION: Regenerating embedding files if they already exist")
    else:
        logger.info("Skipping embedding generation if files already exist")
else:
    logger.info('Embedding generation disabled, use -e to enable')
    
if LIMIT_FILES > 0:
    logger.info(f"OPTION: Limiting files to process to {LIMIT_FILES:,}")

logger.info(f"Total files to process: {stats['files-to-process']:,}")

ctr = 1

df_token_data = []

for item in tqdm(sorted_file_list, desc="Processing files"):
    item_path = item.as_posix()

    encoding = detect_encoding(item_path)

    loader = TextLoader(item_path, encoding=encoding)
    docs = loader.load()

    original_text = docs[0].page_content

    tokens = num_tokens_from_string(original_text, "cl100k_base")
    stats['tokens-unsplitted'] += tokens

    chunks = text_splitter.split_text(original_text)
    chunks_cnt = len(chunks)
    stats['chunks'] += chunks_cnt

    tokens_splitted = sum([num_tokens_from_string(chunk, "cl100k_base") for chunk in chunks])
    stats['tokens-splitted'] += tokens_splitted

    logger.debug(f"{ctr:,}/{stats['files-to-process']:,}: Tokens: {tokens_splitted:,}, "
                 f"Chunks: {chunks_cnt}, Path: {item_path}")

    df_token_data.append({
        'ctr': ctr,
        'tokens_unsplitted': tokens,
        'tokens_splitted': tokens_splitted,
        'price_unsplitted': tokens_price(tokens, PRICE_PER_MEGA_TOKENS),
        'price_splitted': tokens_price(tokens_splitted, PRICE_PER_MEGA_TOKENS),
        'chunks': chunks_cnt,
        'name': item.name,
        'full_path': item_path
    })

    # Implement the making of embeding
    # after testing it not exists
    # or regen and owerwriting if needed
    if PERFORM_EMBEDDING:
        embeddings_file_path = item.with_suffix(f".{EMBEDDINGS_EXTENSION}").as_posix()

        # Conditional embedding generation
        if REGENERATE_IF_EXISTS or not os.path.exists(embeddings_file_path):
            embeddings = []
            
            for i, chunk in enumerate(chunks): 

                logger.debug(f"Chunk {i+1}/{chunks_cnt} -> {len(chunk)} characters")

                try:
                    embedding = get_embedding(client, chunk, model=EMBEDDING_MODEL)
                    embeddings.append((chunk,embedding))

                except openai.BadRequestError as e:
                    stats['errors-bad-requests'] += 1
                    logger.error(f"Bad request to OpenAI API: {e}")
                except openai.APIError as e:
                    stats['errors-api'] += 1
                    logger.error(f"OpenAI API error: {e}")
                except Exception as e:  # Catch-all for other errors
                    stats['errors-other'] += 1
                    logger.error(f"Unexpected error while creating embedding: {e}")
                    raise e

            if len(embeddings) != chunks_cnt:
                logger.error(f"Error during chunking -> not going to store embeddings for {item_path}")
                continue

            # Save the embedding in a pickle file
            with open(embeddings_file_path, 'wb') as f:
                pickle.dump(embeddings, f)

            stats['files-embedded'] += 1

            logger.debug(f"Embeddings created for: {item_path} at {embeddings_file_path}")
        else:
            logger.debug(f"Skipping embedding generation for: {item_path} (already exists). "
                         "Use parameter -o to regenerate.")

    ctr += 1

stats['files-processed'] = ctr - 1

total_price_unsplitted = tokens_price(stats['tokens-unsplitted'], PRICE_PER_MEGA_TOKENS)
stats['price-unsplitted'] = total_price_unsplitted

total_price_splitted = tokens_price(stats['tokens-splitted'], PRICE_PER_MEGA_TOKENS)
stats['price-splitted'] = total_price_splitted

logger.info(f"Total tokens: {stats['tokens-unsplitted']:,} -> price: {total_price_unsplitted:.2f} {CCY}")
logger.info(f"Total tokens (splitted): {stats['tokens-splitted']:,} -> price: {total_price_splitted:.2f} {CCY}")

overhead = total_price_splitted - total_price_unsplitted
stats['price-overhead'] = overhead
logger.info(f"Overhead: {overhead:.2f} {CCY}")

df = pd.DataFrame(df_token_data)

pickle_df_path = os.path.join(root_path, ANALYTICS_DIR, "tokens_df.pkl")
pickle.dump(df, open(pickle_df_path, "wb"))

csv_path = os.path.join(root_path, ANALYTICS_DIR, "tokens.csv")
df.to_csv(csv_path, index=False)

logger.info('Done')

logger.info(f'Stats: {stats}')

end_time = time.perf_counter()
elapsed_time = end_time - start_time

logger.info(f'Successfully completed in {elapsed_time/60:.1f} minutes.')
