import os
import json

from pathlib import Path

import pickle

import pandas as pd

from extractors import process, ProcessorEmptyFileException, MalformedPseudoheaderException

# In case resume is needed.
# Do not though that this will not populate analytics file properly,
# so it is required to start from scratch for the final run.
SKIP_FIRST_FILES = 0

# Mind the gitignore file if you change this.
ANALYTICS_PATH = "./analytics"

secrets_file_name = 'project.secrets'
with open(secrets_file_name, "r") as secrets_file:
    secrets_data = json.load(secrets_file)

ingest_dir = secrets_data["ingest-dir"]
processed_dir = secrets_data["processed-dir"]

if not os.path.exists(processed_dir):
    os.makedirs(processed_dir, exist_ok=True)  

# We need to exclude Attachment/*.txt as these have different formats.
# If needed they can be processed separately.
file_list = [f for f in Path(ingest_dir).glob('**/*.txt') if "Attachment" not in f.parts]
sorted_file_list = sorted(file_list)
sorted_file_list = sorted_file_list[SKIP_FIRST_FILES:]

ctr = 1
ctr_total = len(sorted_file_list)

pd_data_list = []
pd_data_list_with_duplicates = []

malformed_pseudoheader_list = []
empty_files_list = []

stats = {
    'total-files': ctr_total,
    'processed-files': 0,
    'malformed-pseudoheader': 0,
    'empty-files': 0,
    'duplicate-content': 0
}

for item in sorted_file_list:
    item_name = item.name
    item_path = item.as_posix()

    print(f"{stats['processed-files']:,}/{ctr_total:,}: {item_path}")
    stats['processed-files'] += 1

    try:
        metadata, contents = process(item_path)
    except ProcessorEmptyFileException as e:
        print(f"{e}")
        stats['empty-files'] += 1
        empty_files_list.append(item_path)
        continue
    except MalformedPseudoheaderException as e:
        print(f"{e}")
        stats['malformed-pseudoheader'] += 1
        malformed_pseudoheader_list.append(item_path)
        continue
    
    hash = metadata['hash']
    target_path = os.path.join(processed_dir, hash + ".txt")

    pd_data_list_with_duplicates.append(metadata)
    
    if os.path.exists(target_path):
        print(f"File already exists -> skipping. Source: {item_path}")
        stats['duplicate-content'] += 1
        continue

    encoding = metadata['encoding']
    with open(target_path, 'w', encoding=encoding) as f:
        f.write(contents)

    metadata_path = os.path.join(processed_dir, hash + ".metadata.json")
    with open(metadata_path, 'w') as f:
        json.dump(metadata, f, indent=2)

    pd_data_list.append(metadata)

pickle_path = os.path.join(ANALYTICS_PATH, "results.df")
pickle_with_duplicates_path = os.path.join(ANALYTICS_PATH, "results_with_duplicates.df")

csv_path = os.path.join(ANALYTICS_PATH, "results.csv")
csv_with_duplicates_path = os.path.join(ANALYTICS_PATH, "results_with_duplicates.csv")

pickle.dump(pd_data_list, open(pickle_path, "wb"))
pickle.dump(pd_data_list_with_duplicates, open(pickle_with_duplicates_path, "wb"))

pd.DataFrame(pd_data_list).to_csv(csv_path, index=False)
pd.DataFrame(pd_data_list_with_duplicates).to_csv(csv_with_duplicates_path, index=False)

# Store lists of files with problems.
with open(os.path.join(ANALYTICS_PATH, "malformed_pseudoheader_list.log"), "w") as f:
    for item in malformed_pseudoheader_list:
        f.write(f"{item}\n")

with open(os.path.join(ANALYTICS_PATH, "empty_files_list.log"), "w") as f:
    for item in empty_files_list:
        f.write(f"{item}\n")

print('Stats:')
print(stats)
print()

print('Done!')