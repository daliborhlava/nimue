import os
import sys
import hashlib
import re
import json

from datetime import datetime
import pytz

import numpy as np
import pandas as pd

from shared import detect_encoding


def extract_email_info(email_string):
    """Extracts date, sender, recipient, and subject from an email string."""

    lines = email_string.splitlines()[:5]  # Get first 4 lines
    
    # Initialize an empty dictionary to store the extracted data.
    extracted_data = {}

    # Iterate over the lines in the email string.
    for line in lines:
        parts = line.split(':', 1)  # Split on the first colon

        if len(parts) == 2:  # Ensure a colon was found
            key, value = parts
            extracted_data[key.strip()] = value.strip().strip('"')  # Clean up and store

    # Handle date and time
    local_timezone = pytz.timezone('CET')  # TZ for the date in the email. 
    naive_datetime = datetime.strptime(extracted_data['Date'], "%m/%d/%Y %I:%M:%S %p")
    local_datetime = local_timezone.localize(naive_datetime)
    extracted_data['Date (UTC)'] = local_datetime.astimezone(pytz.utc).isoformat()

    return extracted_data

secrets_file_name = 'project.secrets'
with open(secrets_file_name, "r") as secrets_file:
    secrets_data = json.load(secrets_file)

data_dir = secrets_data["data-dir"]
source_dir = os.path.join(data_dir, "ingest-raw")
target_dir = os.path.join(data_dir, "ingest-processed")

file_list = os.listdir(source_dir)
sorted_file_list = sorted(file_list)

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
        raise Exception(f"File already exists: {target_path}, source: {item_path}")
    
    extracted_data = extract_email_info(contents)

    # File name example: 1-3-2017__Jane doe_ _Jane.Doe@example.com__RE_ XXX XX - lorem ipsum
    from_str = extracted_data['From']

    from_email = ""
    email_pattern = r"_(?P<email>[\w.-]+@[\w-]+\.[\w.-]+)_"
    match = re.search(email_pattern, item)

    if match:
        email = match.group(0)
        print(email)  
    else:
        raise Exception("No email found - adjust regex / fix naming options")

    to_str = extracted_data['To']
    to_email = extracted_data['To']  # Currently no other way to source to.
    subject = extracted_data['Subject']
    datetime_utc = extracted_data['Date (UTC)']
    attachments = extracted_data.get('Attachments', '')

    metadata = {
        "source": item,
        "from": from_str,
        "from_email": from_email,
        "to": to_email,
        "to_str": to_str,
        "subject": subject,
        "datetime_utc": datetime_utc,
        "attachments": attachments,
        "attachments-count": len(attachments.split(';')),
        "content-hash": hash,
        "content-length": len(contents),
        "encoding": encoding,
    }

    with open(target_path, 'w') as f:
        f.write(contents)

    metadata_path = os.path.join(target_dir, hash + ".metadata.json")
    with open(metadata_path, 'w') as f:
        json.dump(metadata, f, indent=2)

    pd_data_list.append(metadata)

csv_path = os.path.join(data_dir, "results.csv")
pd.DataFrame(pd_data_list).to_csv(csv_path, index=False)

print('Done!')