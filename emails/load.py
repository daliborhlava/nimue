import os
import sys

import chromadb
import numpy as np

from chromadb import Settings

from langchain_openai import OpenAIEmbeddings

from langchain_chroma import Chroma
from langchain_community.document_loaders import TextLoader
from langchain_text_splitters import CharacterTextSplitter

import openai

import json

from shared import detect_encoding, num_tokens_from_string, tokens_price

COLLECTIONS_NAME = "emails"

secrets_file_name = 'project.secrets'
with open(secrets_file_name, "r") as secrets_file:
    secrets_data = json.load(secrets_file)

if os.getenv("OPENAI_API_KEY") is not None:
    openai.api_key = os.getenv("OPENAI_API_KEY")
else:
    raise Exception("OPENAI_API_KEY environment variable not found")

model = 'text-embedding-3-large'
import chromadb.utils.embedding_functions as embedding_functions
embedding_function = embedding_functions.OpenAIEmbeddingFunction(
                api_key=openai.api_key,
                model_name=model
            )

# When would this be used?
#embeddings = OpenAIEmbeddings(model=model) 

settings = Settings(allow_reset=True, anonymized_telemetry=False)
client = chromadb.HttpClient(host='192.168.1.51', port=6800, settings=settings)

collection = client.get_or_create_collection(name=COLLECTIONS_NAME, embedding_function=embedding_function)

# langchain_chroma = Chroma(
#     client=client,
#     collection_name=collection_name,
#     embedding_function=embedding_function,
# )

data_dir = secrets_data["data-dir"]
for item in os.listdir(data_dir):
    item_path = os.path.join(data_dir, item)

    encoding = detect_encoding(item_path)

    loader = TextLoader(item_path, encoding=encoding)
    docs = loader.load()

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