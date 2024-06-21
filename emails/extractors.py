from datetime import datetime
import pytz

import re

import hashlib
import os

from shared import detect_encoding

KEY_MAX_LENGTH = 15  # Maximum length of a key in the pseudoheader.
PSEUDOHEADER_SCAN_LINES = 10  # Maximum number of lines in the pseudoheader.

UNKNOWN = '<missing>'  # Placeholder for unknown values.


class ProcessorEmptyFileException(Exception):
    pass

class MalformedPseudoheaderException(Exception):
    pass


def process(item_path: str) -> dict:
    encoding = detect_encoding(item_path)

    contents = None
    with open(item_path, 'r', encoding=encoding) as f:
        contents = f.read()

    if contents is None or contents.strip() == "":
        raise ProcessorEmptyFileException(f"Empty file: {item_path}")

    # Calculate md5 hash of the file contents to use as a unique identifier.
    hash = hashlib.md5(contents.encode()).hexdigest()

    name = os.path.basename(item_path)
    metadata = extract_mail_metadata(name, contents)

    metadata['encoding'] = encoding
    metadata['hash'] = hash
    metadata['content-length'] = len(contents)

    return metadata, contents


def extract_mail_metadata(name: str, contents: str) -> dict:

    """ Extracts email metadata from available data and combines them. """
    metadata_name = extract_mail_info_from_name_method1(name)
    metadata_contents = extract_email_info_from_contents_method1(contents)

    to = metadata_contents.get('to', UNKNOWN)
    attachments = metadata_contents.get('attachments', '').strip(';')

    metadata = {
        "source": name,
        "from_str": metadata_contents.get('from', UNKNOWN),
        "from_email": metadata_name['from_email'],  # Unknown handled already inside.
        "to_str": to,
        "to_email": to,  # Currently no other way to source to.
        "cc": metadata_contents.get('cc', ''),
        "bcc": metadata_contents.get('bcc', ''),
        "subject": metadata_contents.get('subject', UNKNOWN),
        "datetime_utc": metadata_contents['date (utc)'],
        "attachments": attachments,
        "attachments-count": len(attachments.split(';')) if len(attachments) > 0 else 0,
    }

    return metadata


def extract_email_info_from_contents_method1(email_string):
    """
    Extracts date, sender, recipient, and subject from an email string.
    Sample file contents:
    Date : 1/1/2013 6:30:08 AM
    From : Jane Doe
    To : John Doe
    Subject : XXX
    Auto time: 1.1.2013 4:37:00
    Attachment : vypis_517057_1_20161231.pdf;uroky.pdf;
    """

    lines = email_string.splitlines()
    pseudoheader = lines[:PSEUDOHEADER_SCAN_LINES]  # Extract the pseudoheader (first x lines containing key : value).

    pseudoheader_terminator = 0
    did_break = False
    for line in pseudoheader:
        colon_index = line.find(':')
        if colon_index == -1 or colon_index > KEY_MAX_LENGTH:
            did_break = True
            break
        pseudoheader_terminator += 1
    
    if pseudoheader_terminator == 1:
        # Special handling for malformed emails where pseudoheader does not break lines.

        # Possibly also CC/BCC handling, but have not seen malformed emails with those yet.
        s = (lines[0].replace('Date : ', '\nDate : ')
                .replace('From : ', '\nFrom : ')
                .replace('To : ', '\nTo : ')
                .replace('Subject : ', '\nSubject : '))

        pseudoheader = s.splitlines()

    elif pseudoheader_terminator < 3:
        raise MalformedPseudoheaderException("Too few lines in the pseudoheader -> something wrong?.")
    else:
        pseudoheader = pseudoheader[:pseudoheader_terminator]
    
    # Initialize an empty dictionary to store the extracted data.
    extracted_data = {}

    allowed_keys = ['date', 'from', 'to', 'subject', 'attachment', 'date (utc)',
                       'cc', 'bcc']

    # Iterate over the lines in the email string.
    for line in pseudoheader:
        parts = line.split(' : ', 1)  # Split on the first colon

        if len(parts) == 2:  # Ensure a colon was found
            key, value = parts

            if len(key) > KEY_MAX_LENGTH:
                continue  # Skip lines that are too long to be keys.

            if key not in allowed_keys:
                continue

            extracted_data[key.strip().lower()] = value.strip().strip('"')  # Clean up and store

    # Handle date and time.
    try:
        local_timezone = pytz.timezone('CET')  # TZ for the date in the email. 
        naive_datetime = datetime.strptime(extracted_data['date'], "%m/%d/%Y %I:%M:%S %p")
        local_datetime = local_timezone.localize(naive_datetime)
        extracted_data['date (utc)'] = local_datetime.astimezone(pytz.utc).isoformat()
    except OverflowError:
        extracted_data['date (utc)'] = '0001-01-01T00:00:00+00:00'

    return extracted_data


def extract_mail_info_from_name_method1(name: str) -> dict:
    """
    Extracts metadata from an email name using a specific method.
    Sample naming: 1-3-2017__Jane doe_ _Jane.Doe@example.com__RE_ XXX XX - lorem ipsum
    """

    # Extract the email from the name.
    email_pattern = r"_\s*_?(?P<email>[\w._+-]+@[\w-]+\.[\w.-]+)\s*_"
    match = re.search(email_pattern, name)
    from_email = match.group(1) if match else UNKNOWN

    metadata = {
        "from_email": from_email,
    }

    return metadata
