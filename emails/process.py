import os
import sys
import hashlib
import json
import glob

import numpy as np
import pandas as pd

from shared import detect_encoding
from extractors import extract_mail_metadata_method1

secrets_file_name = 'project.secrets'
with open(secrets_file_name, "r") as secrets_file:
    secrets_data = json.load(secrets_file)

data_dir = secrets_data["data-dir"]
source_dir = os.path.join(data_dir, "ingest-raw")
target_dir = os.path.join(data_dir, "ingest-processed")

if not os.path.exists(target_dir):
    os.makedirs(target_dir, exist_ok=True)  

file_list = glob.glob(os.path.join(source_dir, '*.txt'))
sorted_file_list = sorted(file_list)

# Temp/optional, for debug.
sorted_file_list = sorted_file_list[4000:]

ctr = 1
ctr_total = len(sorted_file_list)

pd_data_list = []

for item in sorted_file_list:
    item_path = os.path.join(source_dir, item)

    print(f"{ctr:,}/{ctr_total:,}: {item}")
    ctr += 1

    encoding = detect_encoding(item_path)

    contents = None
    with open(item_path, 'r', encoding=encoding) as f:
        contents = f.read()

    if contents is None or contents.strip() == "":
        raise Exception(f"Empty file: {item_path}")

    # Calculate md5 hash of the file contents to use as a unique identifier.
    hash = hashlib.md5(contents.encode()).hexdigest()

    target_path = os.path.join(target_dir, hash + ".txt")

    if os.path.exists(target_path):
        print(f"File already exists -> skipping. Source: {item_path}")
        continue

    metadata = extract_mail_metadata_method1(item, contents)

    metadata['encoding'] = encoding
    metadata['hash'] = hash
    metadata['content-length'] = len(contents)

    with open(target_path, 'w', encoding=encoding) as f:
        f.write(contents)

    metadata_path = os.path.join(target_dir, hash + ".metadata.json")
    with open(metadata_path, 'w') as f:
        json.dump(metadata, f, indent=2)

    pd_data_list.append(metadata)

csv_path = os.path.join(data_dir, "results.csv")
pd.DataFrame(pd_data_list).to_csv(csv_path, index=False)

print('Done!')