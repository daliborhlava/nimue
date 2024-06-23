import os
import json

import argparse

from pathlib import Path

import pickle
import time

import pandas as pd

from tqdm import tqdm

from extractors import process, ProcessorEmptyFileException, MalformedPseudoheaderException
from shared import init_logger
from constants import ANALYTICS_PATH

logger = init_logger()

parser = argparse.ArgumentParser(description="Nimue Email Processor")
parser.add_argument("-s", "--skip", help="Skip first N files", type=int, default=0)
args = parser.parse_args()

# In case resume is needed.
# Do not though that this will not populate analytics file properly,
# so it is required to start from scratch for the final run.
skip_first_n_files = args.skip
if skip_first_n_files > 0:
    logger.warning(f"Skipping first {skip_first_n_files} files. "
                   "Metadata construction will not be complete!")

secrets_file_name = 'project.secrets'
with open(secrets_file_name, "r") as secrets_file:
    secrets_data = json.load(secrets_file)

ingest_dir = secrets_data["ingest-dir"]
processed_dir = secrets_data["processed-dir"]

if not os.path.exists(processed_dir):
    os.makedirs(processed_dir, exist_ok=True)

start_time = time.perf_counter()

# We need to exclude Attachment/*.txt as these have different formats.
# If needed they can be processed separately.
file_list = [f for f in Path(ingest_dir).glob('**/*.txt') if "Attachment" not in f.parts]
absolute_total_count = len(file_list)

logger.info('Starting...')
logger.info(f"Total files to process: {absolute_total_count:,}")

sorted_file_list = sorted(file_list)

sorted_file_list = sorted_file_list[skip_first_n_files:]

ctr = 1
ctr_total = len(sorted_file_list)

pd_data_list = []
pd_data_list_with_duplicates = []

malformed_pseudoheader_list = []
empty_files_list = []

stats = {
    'total-files': absolute_total_count,
    'processed-files': 0,
    'malformed-pseudoheader': 0,
    'empty-files': 0,
    'duplicate-content': 0
}

for item in tqdm(sorted_file_list, desc="Processing files"):
    item_name = item.name
    item_path = item.as_posix()

    logger.debug(f"{stats['processed-files']:,}/{ctr_total:,}: {item_path}")
    stats['processed-files'] += 1

    try:
        metadata, contents = process(item_path)
    except ProcessorEmptyFileException as e:
        logger.error(f"{e}")
        stats['empty-files'] += 1
        empty_files_list.append(item_path)
        continue
    except MalformedPseudoheaderException as e:
        logger.error(f"{e}")
        stats['malformed-pseudoheader'] += 1
        malformed_pseudoheader_list.append(item_path)
        continue
    
    hash = metadata['hash']
    target_path = os.path.join(processed_dir, hash + ".txt")

    pd_data_list_with_duplicates.append(metadata)
    
    if os.path.exists(target_path):
        # A large number of these files are duplicates, so reporting as debug.
        logger.debug(f"File already exists -> skipping. Source: {item_path}")
        stats['duplicate-content'] += 1
        continue

    encoding = metadata['encoding']
    with open(target_path, 'w', encoding=encoding) as f:
        f.write(contents)

    metadata_path = os.path.join(processed_dir, hash + ".metadata.json")
    with open(metadata_path, 'w') as f:
        json.dump(metadata, f, indent=2)

    pd_data_list.append(metadata)

stats['metadata-files'] = len(pd_data_list)
stats['metadata-files-with-duplicates'] = len(pd_data_list_with_duplicates)

pickle_list_path = os.path.join(ANALYTICS_PATH, "results_list.pkl")
pickle_list_with_duplicates_path = os.path.join(ANALYTICS_PATH, "results_list_with_duplicates.pkl")

pickle.dump(pd_data_list, open(pickle_list_path, "wb"))
pickle.dump(pd_data_list_with_duplicates, open(pickle_list_with_duplicates_path, "wb"))

pickle_df_path = os.path.join(ANALYTICS_PATH, "results_df.pkl")
pickle_df_with_duplicates_path = os.path.join(ANALYTICS_PATH, "results_df_with_duplicates.pkl")

pickle.dump(pd.DataFrame(pd_data_list), open(pickle_df_path, "wb"))
pickle.dump(pd.DataFrame(pd_data_list_with_duplicates), open(pickle_df_with_duplicates_path, "wb"))

csv_path = os.path.join(ANALYTICS_PATH, "results.csv")
csv_with_duplicates_path = os.path.join(ANALYTICS_PATH, "results_with_duplicates.csv")

pd.DataFrame(pd_data_list).to_csv(csv_path, index=False)
pd.DataFrame(pd_data_list_with_duplicates).to_csv(csv_with_duplicates_path, index=False)

# Store lists of files with problems.
with open(os.path.join(ANALYTICS_PATH, "malformed_pseudoheader_list.log"), "w") as f:
    for item in malformed_pseudoheader_list:
        f.write(f"{item}\n")

with open(os.path.join(ANALYTICS_PATH, "empty_files_list.log"), "w") as f:
    for item in empty_files_list:
        f.write(f"{item}\n")

logger.info('Done')

logger.info('Stats:')
logger.info(stats)

end_time = time.perf_counter()
elapsed_time = end_time - start_time

logger.info(f'Successfully completed in {elapsed_time/60:.1f} minutes.')
