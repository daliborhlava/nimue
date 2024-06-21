import os
import json

from pathlib import Path

import pandas as pd

from extractors import process, ProcessorEmptyFileException

# In case resume is needed.
SKIP_FIRST_FILES = 0

secrets_file_name = 'project.secrets'
with open(secrets_file_name, "r") as secrets_file:
    secrets_data = json.load(secrets_file)

ingest_dir = secrets_data["ingest-dir"]
processed_dir = secrets_data["processed-dir"]

if not os.path.exists(processed_dir):
    os.makedirs(processed_dir, exist_ok=True)  

file_list = [f for f in Path(ingest_dir).glob('**/*.txt')]
sorted_file_list = sorted(file_list)
sorted_file_list = sorted_file_list[SKIP_FIRST_FILES:]

ctr = 1
ctr_total = len(sorted_file_list)

pd_data_list = []

stats = {
    'total-files': ctr_total,
    'processed-files': 0,
    'empty-files': 0
}

for item in sorted_file_list:
    item_name = item.name
    item_path = item.as_posix()

    print(f"{stats['processed-files']:,}/{ctr_total:,}: {item_name}")
    stats['processed-files'] += 1

    try:
        metadata, contents = process(item_path)
    except ProcessorEmptyFileException as e:
        print(f"{e}")
        stats['empty-files'] += 1
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

csv_path = os.path.join("./analytics", "results.csv")
pd.DataFrame(pd_data_list).to_csv(csv_path, index=False)

print('Stats:')
print(stats)
print()

print('Done!')