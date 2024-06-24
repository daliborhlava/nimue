import sys
import os
import json

import argparse

import chromadb
from chromadb import Settings

import openai

from constants import EMAIL_COLLECTION_NAME, EMBEDDING_MODEL

default_results = 5

parser = argparse.ArgumentParser(description="Nimue Query CLI")
parser.add_argument("-q", "--query", help="Query to ask", type=str, required=True)
parser.add_argument("-r", "--results",
                    help=f"Maximum results to return to process (default {default_results})",
                    type=int, default=default_results)
args = parser.parse_args()

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

# Retrieval Logic
if result == 0:
    print("No documents in the collection yet.")
    sys.exit()

query = args.query
results = args.results

results = collection.get(
    query=query,
    limit=results,  # Get couple docs.
    include=["documents", "metadatas", "embeddings"]  # Include all relevant data.
)

for key in results['documents']:
    doc = results['documents'][key]
    metadata = results['metadatas'][key]
    embedding = results['embeddings'][key]

    print("Document Chunk:")
    print(doc)
    print()

    print("Metadata:")
    print(metadata)
    print()

    print("Embedding (truncated for display):")
    print(embedding[:5])  # Display the first few elements of the embedding
    print()

    print('==================')
    print()