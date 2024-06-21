import os
import sys
import json
import glob

import pandas as pd

from extractors import process, ProcessorEmptyFileException

# In case resume is needed.
SKIP_FIRST_FILES = 4895+3540

secrets_file_name = 'project.secrets'
with open(secrets_file_name, "r") as secrets_file:
    secrets_data = json.load(secrets_file)

data_dir = secrets_data["data-dir"]
source_dir = os.path.join(data_dir, "ingest-raw")
target_dir = os.path.join(data_dir, "ingest-processed")
errors_dir = os.path.join(data_dir, "errors")

if not os.path.exists(target_dir):
    os.makedirs(target_dir, exist_ok=True)  

if not os.path.exists(target_dir):
    os.makedirs(errors_dir, exist_ok=True)  

file_list = glob.glob(os.path.join(source_dir, '*.txt'))
sorted_file_list = sorted(file_list)
sorted_file_list = sorted_file_list[SKIP_FIRST_FILES:]

ctr = 1
ctr_total = len(sorted_file_list)

pd_data_list = []

for item in sorted_file_list:
    item_path = os.path.join(source_dir, item)

    print(f"{ctr:,}/{ctr_total:,}: {item}")
    ctr += 1

    try:
        metadata, contents = process(item_path)
    except ProcessorEmptyFileException as e:
        print(f"Error: {e}")
        error_path = os.path.join(errors_dir, os.path.basename(item))
        os.rename(item_path, error_path)
        continue
    
    hash = metadata['hash']
    target_path = os.path.join(target_dir, hash + ".txt")
    
    if os.path.exists(target_path):
        print(f"File already exists -> skipping. Source: {item_path}")
        continue

    encoding = metadata['encoding']
    with open(target_path, 'w', encoding=encoding) as f:
        f.write(contents)

    metadata_path = os.path.join(target_dir, hash + ".metadata.json")
    with open(metadata_path, 'w') as f:
        json.dump(metadata, f, indent=2)

    pd_data_list.append(metadata)

csv_path = os.path.join(data_dir, "results.csv")
pd.DataFrame(pd_data_list).to_csv(csv_path, index=False)

print('Done!')