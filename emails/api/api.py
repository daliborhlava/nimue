import os
import sys

import json

import openai

from flask import Flask, request, jsonify, render_template
from flask_cors import CORS

script_dir = os.path.dirname(os.path.abspath(__file__))
root_path = os.path.join(script_dir, "..")
sys.path.append(root_path)

from shared.constants import EMAIL_COLLECTION_NAME, EMBEDDING_MODEL
from shared.vectordb import VectorStore

if os.getenv("OPENAI_API_KEY") is not None:
    openai.api_key = os.getenv("OPENAI_API_KEY")
else:
    raise Exception("OPENAI_API_KEY environment variable not found")

secrets_file_name = 'project.secrets'
secrets_path = os.path.join(script_dir, "..", secrets_file_name)

with open(secrets_path, "r") as secrets_file:
    secrets_data = json.load(secrets_file)

vector_db_host = secrets_data["vector-db-host"]
vector_db_port = secrets_data["vector-db-port"]

import chromadb.utils.embedding_functions as embedding_functions
embedding_function = embedding_functions.OpenAIEmbeddingFunction(
                        api_key=openai.api_key,
                        model_name=EMBEDDING_MODEL
                    )

vector_store = VectorStore(vector_db_host, vector_db_port,
                           embedding_function, EMAIL_COLLECTION_NAME)

app = Flask(__name__)
CORS(app)


# Search Endpoint
@app.route('/api/search', methods=['GET'])
def search():
    query = request.args.get('query', '')
    n_results = request.args.get('n_results', 3)

    results = vector_store.query(query, n_results)

    return jsonify(results)


# Frontend Route
@app.route('/')
def index():
    return render_template('index.html')


if __name__ == '__main__':
    app.run(debug=True)