query_embeddings = [np.random.rand(128).astype(np.float32)]  # Sample query embedding
results = collection.query(
    query_embeddings=query_embeddings,
    n_results=3  # Number of results to return
)
print(results)