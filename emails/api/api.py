import os
import sys

import json

from flask import Flask, request, jsonify, render_template
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

# # Mock Text Documents
# documents = [
#     {"id": 1, "text": "The quick brown fox jumps over the lazy dog.", "metadata": {"author": "John Doe", "date": "2017-01-01"}},
#     {"id": 2, "text": "Lorem ipsum dolor sit amet, consectetur adipiscing elit.", "metadata": {"author": "John Dear", "date": "2018-01-01"}},
#     {"id": 3, "text": "The five boxing wizards jump quickly.", "metadata": {"author": "John Cear", "date": "2019-01-01"}},
#     {"id": 4, "text": "Foxy fox, foxing with foxers.", "metadata": {"author": "John Mear", "date": "2020-01-01"}},
#     {"id": 5, "text": "Foxeeeeers! Foxers.", "metadata": {"author": "John Rear", "date": "2021-01-01"}}
# ]

script_dir = os.path.dirname(os.path.abspath(__file__))
root_path = os.path.join(script_dir, "..")
sys.path.append(root_path)

secrets_file_name = 'project.secrets'
secrets_path = os.path.join(script_dir, "..", secrets_file_name)

with open(secrets_path, "r") as secrets_file:
    secrets_data = json.load(secrets_file)

from shared.constants import EMAIL_COLLECTION_NAME, EMBEDDING_MODEL

# Search Endpoint
@app.route('/search', methods=['GET'])
def search():
    query = request.args.get('query', '')
    n_results = request.args.get('n_results', 3)

    results = [doc for doc in documents if query.lower() in doc['text'].lower()]

    return jsonify(results[:n_results])


# Frontend Route
@app.route('/')
def index():
    return render_template('index.html')


if __name__ == '__main__':
    app.run(debug=True)