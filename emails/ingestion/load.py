from pathlib import Path

import pickle
import time
import json

import argparse
from tqdm import tqdm

import chromadb

from chromadb import Settings

from shared import init_logger, detect_encoding
from emails.shared.constants import EMAIL_COLLECTION_NAME, EMAIL_EXTENSION, METADATA_EXTENSION, EMBEDDINGS_EXTENSION

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
    'total-files-processed': -1,
    'chunks-processed': 0,
    'documents-inserted': 0,
}

start_time = time.perf_counter()

settings = Settings(allow_reset=True, anonymized_telemetry=False)
client = chromadb.HttpClient(host=vector_db_host, port=vector_db_port, settings=settings)

# This can delete the collection if needed.
#client.delete_collection(name=EMAIL_COLLECTION_NAME)

collection = client.get_or_create_collection(name=EMAIL_COLLECTION_NAME)

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

        # Could be done in batch, but for now we do it one by one.
        collection.add(ids=[f"{hsh}-{embedding_no}"], embeddings=[embedding],
                       metadatas=[metadata_chunk], documents=[chunk])

        embedding_no += 1
        stats['documents-inserted'] += 1

    ctr += 1

stats['total-files-processed'] = ctr - 1

logger.info('Done')

logger.info(f'Stats: {stats}')

end_time = time.perf_counter()
elapsed_time = end_time - start_time

logger.info(f'Successfully completed in {elapsed_time/60:.1f} minutes.')
