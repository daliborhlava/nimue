import os
import json

from pathlib import Path

import pandas as pd

from extractors import process, ProcessorEmptyFileException, MalformedPseudoheaderException

# In case resume is needed.
SKIP_FIRST_FILES = 89200

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

malformed_pseudoheader_list = []
empty_files_list = []

stats = {
    'total-files': ctr_total,
    'processed-files': 0,
    'malformed-pseudooheader': 0,
    'empty-files': 0
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
        stats['malformed-pseudooheader'] += 1
        malformed_pseudoheader_list.append(item_path)
        continue
    
    hash = metadata['hash']
    target_path = os.path.join(processed_dir, hash + ".txt")
    
    if os.path.exists(target_path):
        print(f"File already exists -> skipping. Source: {item_path}")
        continue

    encoding = metadata['encoding']
    with open(target_path, 'w', encoding=encoding) as f:
        f.write(contents)

    metadata_path = os.path.join(processed_dir, hash + ".metadata.json")
    with open(metadata_path, 'w') as f:
        json.dump(metadata, f, indent=2)

    pd_data_list.append(metadata)

csv_path = os.path.join(ANALYTICS_PATH, "results.csv")
pd.DataFrame(pd_data_list).to_csv(csv_path, index=False)

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