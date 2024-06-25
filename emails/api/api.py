from flask import Flask, request, jsonify, render_template
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

# Mock Text Documents
documents = [
    {"id": 1, "text": "The quick brown fox jumps over the lazy dog."},
    {"id": 2, "text": "Lorem ipsum dolor sit amet, consectetur adipiscing elit."},
    {"id": 3, "text": "The five boxing wizards jump quickly."}
]

# Search Endpoint
@app.route('/search', methods=['GET'])
def search():
    query = request.args.get('query', '')
    results = [doc for doc in documents if query.lower() in doc['text'].lower()]
    return jsonify(results)

# Frontend Route
@app.route('/')
def index():
    return render_template('index.html')

if __name__ == '__main__':
    app.run(debug=True)