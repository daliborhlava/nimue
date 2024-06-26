import sys
import os
import json

import openai

import argparse

import openai

from shared.constants import EMAIL_COLLECTION_NAME, EMBEDDING_MODEL
from shared.vectordb import VectorStore

if os.getenv("OPENAI_API_KEY") is not None:
    openai.api_key = os.getenv("OPENAI_API_KEY")
else:
    raise Exception("OPENAI_API_KEY environment variable not found")

default_results = 3

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

query = args.query
results = args.results

import chromadb.utils.embedding_functions as embedding_functions
embedding_function = embedding_functions.OpenAIEmbeddingFunction(
                        api_key=openai.api_key,
                        model_name=EMBEDDING_MODEL
                    )

vector_store = VectorStore(vector_db_host, vector_db_port,
                           embedding_function, EMAIL_COLLECTION_NAME)

results = vector_store.query(query, results)

if len(results) == 0:  # Check if any results were found
    print(f"No results found for query: '{query}'")
    sys.exit(-1)

for i, result in enumerate(results):

    print(f"\nResult {i+1}:")
    print("-" * 10)  # Separator
    print("Document Chunk:")
    print(result['document'])
    print("\nMetadata:")
    print(result['metadata'])
    print("=" * 20)  # Separator
