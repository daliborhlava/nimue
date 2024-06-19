import os
import sys
import hashlib

import numpy as np

import json

from shared import detect_encoding

secrets_file_name = 'project.secrets'
with open(secrets_file_name, "r") as secrets_file:
    secrets_data = json.load(secrets_file)

source_dir = os.path.join(secrets_data["data-dir"], "ingest-raw")
target_dir = os.path.join(secrets_data["data-dir"], "ingest-processed")

for item in os.listdir(source_dir):
    item_path = os.path.join(source_dir, item)

    encoding = detect_encoding(item_path)

    contents = None
    with open(item_path, 'r', encoding=encoding) as f:
        result = f.read()

    if contents is None or contents.strip() == "":
        raise Exception(f"Empty file: {item_path}")

    # Calculate md5 hash of the file contents to use as a unique identifier.
    hash = hashlib.md5(contents.encode()).hexdigest()

    target_path = os.path.join(target_dir, hash + ".txt")

    if os.path.exists(target_path):
        raise Exception(f"File already exists: {target_path}, source: {item_path}")

    # File name example: 1-3-2017__Jane doe_ _Jane.Doe@example.com__RE_ XXX XX - lorem ipsum
    from_str = ""
    from_email = ""
    to_str = ""
    to_email = ""
    subject = ""
    date = ""

    metadata = {
        "source": item,
        "from": from_str,
        "from_email": from_email,
        "to": to_email,
        "to_str": to_str,
        "subject": subject,
        "date": date,
        "attachment-count": -1,  # TODO, if possible?
        "content-hash": hash,
        "content-length": len(contents),
        "encoding": encoding,
    }

    doc_ctr = 0
    original_text = ""
    for doc in docs:
        assert doc_ctr == 0, "Only one document per file is supported."
        original_text += doc.page_content

        # TODO: update metadata here, like from/to/subject for emails
        # update the metadata for a document
        # docs[0].metadata = {
        #     "source": "../../how_to/state_of_the_union.txt",
        #     "new_value": "hello world",
        # }
        doc.metadata['test'] = 'YES'

        collection.add(
            ids=[item_path], metadatas=doc.metadata, documents=doc.page_content
        )

        doc_ctr += 1

    


sys.exit(-1)



loader = TextLoader("../../how_to/state_of_the_union.txt")
documents = loader.load()





######################33


# Sample embeddings (replace with your actual embeddings)
embeddings = [
    list(np.random.rand(128).astype(np.float32)),  
    list(np.random.rand(128).astype(np.float32)),
    list(np.random.rand(128).astype(np.float32))
]

# Sample documents (replace with your actual documents)
documents = ['This is document 1', 'Another document here', 'One more for the road']

# Sample metadata (replace with your actual metadata)
metadatas = [
    {'source': 'web', 'topic': 'technology'},
    {'source': 'book', 'author': 'Jane Doe'},
    {'source': 'article', 'publication': 'Science Journal'}
]

# Add embeddings with documents and metadata to the collection
collection.add(
    documents=documents,
    metadatas=metadatas,
    ids=['id1', 'id2', 'id3']  # Optional: provide unique IDs for your documents
)