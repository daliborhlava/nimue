from typing import Callable, Any

import chromadb
from chromadb import Settings

class VectorStore:
    def __init__(self, host: str, port: int,
                 embedding_function: Callable[..., Any],
                 collection_name: str):
        self.host = host
        self.port = port

        settings = Settings(allow_reset=True, anonymized_telemetry=False)
        self.client = chromadb.HttpClient(host=self.host, port=self.port, settings=settings)

        self.collection = self.client.get_or_create_collection(
                                name=collection_name,
                                embedding_function=embedding_function
                            )
        
    def query_vector_db(self, query: str, results: int) -> dict:
        results = self.collection.query(
            query_texts=query,
            n_results=results,

            # Also available: "embeddings" and others.
            include=["documents", "metadatas"]
        )

        # Tranform the results into list of results.
        if not results["documents"]:
            return []
        
        documents = results["documents"][0]
        metadatas = results["metadatas"][0]

        results_fmt = []

        for k,v in enumerate(documents):
            metadata = metadatas[k]  # Get the corresponding metadata
            document = documents[k]  # Get the corresponding document

            results_fmt.append({
                "document": document,
                "metadata": metadata
            })
    
        return results_fmt