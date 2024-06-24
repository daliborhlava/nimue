import sys
import os

import chromadb
from chromadb import Settings

import openai

import json

from constants import EMAIL_COLLECTION_NAME, EMBEDDING_MODEL

secrets_file_name = 'project.secrets'
with open(secrets_file_name, "r") as secrets_file:
    secrets_data = json.load(secrets_file)

vector_db_host = secrets_data["vector-db-host"]
vector_db_port = secrets_data["vector-db-port"]

if os.getenv("OPENAI_API_KEY") is not None:
    openai.api_key = os.getenv("OPENAI_API_KEY")
else:
    raise Exception("OPENAI_API_KEY environment variable not found")

import chromadb.utils.embedding_functions as embedding_functions
embedding_function = embedding_functions.OpenAIEmbeddingFunction(
                api_key=openai.api_key,
                model_name=EMBEDDING_MODEL
            )

settings = Settings(allow_reset=True, anonymized_telemetry=False)
client = chromadb.HttpClient(host=vector_db_host, port=vector_db_port, settings=settings)

collection = client.get_or_create_collection(name=EMAIL_COLLECTION_NAME, embedding_function=embedding_function)

result = collection.count()
print(f'Total documents: {result}')

get_doc = 16

# Retrieval Logic
if result == 0:
    print("No documents in the collection yet.")
    sys.exit()

results = collection.get(
    limit=get_doc+10,  # Get couple docs.
    include=["documents", "metadatas", "embeddings"]  # Include all relevant data.
)

first_document = results["documents"][get_doc]
first_metadata = results["metadatas"][get_doc]
first_embedding = results["embeddings"][get_doc]

print("Document:")
print(first_document)
print()

print("Metadata:")
print(first_metadata)
print()

print("Embedding (truncated for display):")
print(first_embedding[:5])  # Display the first few elements of the embedding
print()