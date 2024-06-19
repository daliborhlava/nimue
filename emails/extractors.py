from datetime import datetime
import pytz

import re

def extract_email_info(email_string):
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

    lines = email_string.splitlines()[:10]  # Get first 4 lines
    
    # Initialize an empty dictionary to store the extracted data.
    extracted_data = {}

    # Iterate over the lines in the email string.
    for line in lines:
        parts = line.split(' : ', 1)  # Split on the first colon

        if len(parts) == 2:  # Ensure a colon was found
            key, value = parts

            if len(key) > 20:
                continue  # Skip lines that are too long to be keys.

            extracted_data[key.strip().lower()] = value.strip().strip('"')  # Clean up and store

    # Handle date and time.
    try:
        local_timezone = pytz.timezone('CET')  # TZ for the date in the email. 
        naive_datetime = datetime.strptime(extracted_data['date'], "%m/%d/%Y %I:%M:%S %p")
        local_datetime = local_timezone.localize(naive_datetime)
        extracted_data['date (utc)'] = local_datetime.astimezone(pytz.utc).isoformat()
    except OverflowError:
        extracted_data['date (utc)'] = '0001-01-01T00:00:00+00:00'

    # Check for unexpected keys.
    for key, val in extracted_data.items():
        if key not in ['date', 'from', 'to', 'subject', 'attachment', 'date (utc)',
                       'cc', 'bcc',
                       # And the weird ones:
                       '﻿auto time', 'typ', '· upozornění']:
            raise Exception(f'Unexpected key: ->{key}<-.')

    return extracted_data


def extract_mail_metadata_method1(name: str, contents: str):
    """
    Extracts metadata from an email file using a specific method.
    Sample naming: 1-3-2017__Jane doe_ _Jane.Doe@example.com__RE_ XXX XX - lorem ipsum
    """

    extracted_data = extract_email_info(contents)
   
    # TODO: still captures leading _.
    from_email = ""
    email_pattern = r"_(?P<email>[\w._+-]+@[\w-]+\.[\w.-]+)_"
    match = re.search(email_pattern, name)

    if match:
        from_email = match.group(0)
    else:
        raise Exception("No from email found - adjust regex / fix naming options")

    from_str = extracted_data['from']
    to_str = extracted_data.get('to', '')
    to_email = to_str  # Currently no other way to source to.
    cc = extracted_data.get('cc', '')
    bcc = extracted_data.get('bcc', '')
    subject = extracted_data['subject']
    datetime_utc = extracted_data['date (utc)']
    attachments = extracted_data.get('attachments', '').strip(';')

    metadata = {
        "source": name,
        "from_str": from_str,
        "from_email": from_email,
        "to_str": to_str,
        "to_email": to_email,
        "cc": cc,
        "bcc": bcc,
        "subject": subject,
        "datetime_utc": datetime_utc,
        "attachments": attachments,
        "attachments-count": len(attachments.split(';')) if len(attachments) > 0 else 0,
    }

    return metadata
