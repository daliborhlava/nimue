# Mind the gitignore file if you change this.
ANALYTICS_PATH = "./analytics"

# Placeholder for unknown values.
UNKNOWN_VALUE = '<missing>'

# Filename extension of email files.
EMAIL_EXTENSION = 'txt'

# Filename extension of metadata files.
METADATA_EXTENSION = 'json'

# Filename extension of embedding files.
EMBEDDINGS_EXTENSION = 'pkl'

# Embedding model to use.
EMBEDDING_MODEL = 'text-embedding-3-large'

# Maximum limit remote API can offer.
EMBEDDING_API_MAX_TOKENS = 8192

# Maximum chunk size per embedding.
# Please mind the EMBEDDING_API_MAX_TOKENS.
EMBEDDING_CHUNK_SIZE_TOKENS = 512

# Overlap between chunks.
EMBEDDING_CHUNK_OVERLAP_TOKENS = 128

# Vector database collection name.
EMAIL_COLLECTION_NAME = "emails"