from typing import Callable, Any

import chromadb
from chromadb import Settings

# ABC could be added and this could be just one of the implementations
# if ever more than this one is needed.
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
        
    def drop_collection(self):
        self.client.delete_collection(name=self.collection.name)


    def add_single(self, id: str, embedding: Any, metadata: dict, document: str):
        self.collection.add(ids=[id], embeddings=[embedding],
                            metadatas=[metadata], documents=[document])

        
    def query(self, query: str, results: int) -> dict:
        results = self.collection.query(
            query_texts=query,
            n_results=results,

            # Also available: "embeddings" and others.
            include=["documents", "metadatas", "distances"]
        )

        # Tranform the results into list of results.
        if not results["documents"]:
            return []
        
        documents = results["documents"][0]
        metadatas = results["metadatas"][0]
        distances = results["distances"][0]

        results_fmt = []

        for k,v in enumerate(documents):

            # Get the corresponding items.
            metadata = metadatas[k]
            document = documents[k]
            distance = distances[k]

            results_fmt.append({
                'document': document,
                "metadata": metadata,
                'distance': distance
            })
    
        return results_fmt
