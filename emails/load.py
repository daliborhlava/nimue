from pathlib import Path

import pickle
import time
import json

import argparse
from tqdm import tqdm

import chromadb

from chromadb import Settings

from shared import init_logger, detect_encoding
from constants import EMAIL_COLLECTION_NAME, EMAIL_EXTENSION, METADATA_EXTENSION, EMBEDDING_EXTENSION

logger = init_logger('load')

parser = argparse.ArgumentParser(description="Nimue Email Loader")
parser.add_argument("-l", "--limit", help="Maximum files to process (default 0=unlimited)",
                    type=int, default=0)
args = parser.parse_args()

LIMIT_FILES = args.limit

secrets_file_name = 'project.secrets'
with open(secrets_file_name, "r") as secrets_file:
    secrets_data = json.load(secrets_file)

vector_db_host = secrets_data["vector-db-host"]
vector_db_port = secrets_data["vector-db-port"]

stats = {
    'total-files-to-process': -1,
    'total-files-processed': -1
}

start_time = time.perf_counter()

settings = Settings(allow_reset=True, anonymized_telemetry=False)
client = chromadb.HttpClient(host=vector_db_host, port=vector_db_port, settings=settings)

collection = client.get_or_create_collection(name=EMAIL_COLLECTION_NAME)

processed_dir = secrets_data["processed-dir"]
file_list = [f for f in Path(processed_dir).glob(f'**/*.{EMBEDDING_EXTENSION}')]
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

    embedding_file_path = item.with_suffix(f'.{EMBEDDING_EXTENSION}').as_posix()
    with open(embedding_file_path, "rb") as embedding_file:
        embedding = pickle.load(embedding_file)

    # Could be done in batch, but for now we do it one by one.
    collection.add(ids=[item_path], embeddings=[embedding], metadatas=[metadata], documents=[contents])

    ctr += 1

stats['total-files-processed'] = ctr - 1

logger.info('Done')

logger.info(f'Stats: {stats}')

end_time = time.perf_counter()
elapsed_time = end_time - start_time

logger.info(f'Successfully completed in {elapsed_time/60:.1f} minutes.')
