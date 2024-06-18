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

collection_name = "temp_collection"

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

collection = client.get_or_create_collection(name=collection_name, embedding_function=embedding_function)

# langchain_chroma = Chroma(
#     client=client,
#     collection_name=collection_name,
#     embedding_function=embedding_function,
# )

query_text = 'kdy jsem naposled koupil mentolove krystaly?'

results = collection.query(
    query_texts=[query_text],
    n_results=1
)

print(results["distances"][0])
print()
print(results)