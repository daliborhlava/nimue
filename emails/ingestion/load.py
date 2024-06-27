import sys
import os
from pathlib import Path

import pickle
import time
import json

import argparse
from tqdm import tqdm

script_dir = os.path.dirname(os.path.abspath(__file__))
root_path = os.path.join(script_dir, "..")
sys.path.append(root_path)

from shared.helpers import init_logger, detect_encoding
from shared.vectordb import VectorStore
from shared.constants import (
    EMAIL_COLLECTION_NAME, EMAIL_EXTENSION,
    METADATA_EXTENSION, EMBEDDINGS_EXTENSION,
    LOGS_DIR
)

logger = init_logger('load', logger_dir=os.path.join(root_path, LOGS_DIR))

parser = argparse.ArgumentParser(description="Nimue Email Loader")
parser.add_argument("-l", "--limit", help="Maximum files to process (default 0=unlimited)",
                    type=int, default=0)
args = parser.parse_args()

LIMIT_FILES = args.limit

secrets_file_name = 'project.secrets'
secrets_path = os.path.join(script_dir, "..", secrets_file_name)

with open(secrets_path, "r") as secrets_file:
    secrets_data = json.load(secrets_file)

vector_db_host = secrets_data["vector-db-host"]
vector_db_port = secrets_data["vector-db-port"]

vector_store = VectorStore(vector_db_host, vector_db_port,
                           None, EMAIL_COLLECTION_NAME)

stats = {
    'total-files-to-process': -1,
    'total-files-processed': -1,
    'chunks-processed': 0,
    'documents-inserted': 0,
}

start_time = time.perf_counter()

# This can delete the collection if needed.
#vector_store.delete_collection()

processed_dir = secrets_data["processed-dir"]
file_list = [f for f in Path(processed_dir).glob(f'**/*.{EMBEDDINGS_EXTENSION}')]
sorted_file_list = sorted(file_list)

if LIMIT_FILES > 0:
    sorted_file_list = sorted_file_list[:LIMIT_FILES]

stats['total-files-to-process'] = len(sorted_file_list)

logger.info('Starting...')

if LIMIT_FILES > 0:
    logger.info(f"OPTION: Limiting files to process to {LIMIT_FILES:,}")

logger.info(f"Total files to process: {stats['total-files-to-process']:,}")

ctr = 1

for item in tqdm(sorted_file_list, desc="Processing files"):

    item_path = item.as_posix()

    logger.debug(f"{ctr:,}/{stats['total-files-to-process']:,}: {item_path}")

    email_file_path = item.with_suffix(f'.{EMAIL_EXTENSION}').as_posix()
    encoding = detect_encoding(email_file_path)
    with open(email_file_path, "r", encoding=encoding) as email_file:
        contents = email_file.read()

    metadata_file_path = item.with_suffix(f'.{METADATA_EXTENSION}').as_posix()
    # Encoding should be the same (processor does it that way).
    with open(metadata_file_path, "r", encoding=encoding) as metadata_file:
        metadata = json.load(metadata_file)

    embeddings_file_path = item.with_suffix(f'.{EMBEDDINGS_EXTENSION}').as_posix()
    with open(embeddings_file_path, "rb") as embeddings_file:
        chunks_embeddings = pickle.load(embeddings_file)

    stats['chunks-processed'] += len(chunks_embeddings)

    embedding_no = 1
    hsh = metadata['hash']

    for (chunk, embedding) in chunks_embeddings:
        metadata_chunk = metadata.copy()
        metadata_chunk['chunk'] = embedding_no
        metadata_chunk['total_chunks'] = len(chunks_embeddings)
        
        vector_store.add_single(id=f"{hsh}-{embedding_no}", embedding=embedding,
                       metadata=metadata_chunk, document=chunk)

        embedding_no += 1
        stats['documents-inserted'] += 1

    ctr += 1

stats['total-files-processed'] = ctr - 1

logger.info('Done')

logger.info(f'Stats: {stats}')

end_time = time.perf_counter()
elapsed_time = end_time - start_time

logger.info(f'Successfully completed in {elapsed_time/60:.1f} minutes.')
