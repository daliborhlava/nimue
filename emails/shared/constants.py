# Display currency. Has impact only on the display.
CCY = 'USD'

# Price per million tokens.
CCY_PRICE_PER_MIL_TOKENS = 0.13

# Mind the gitignore file if you change this.
# Relative to the project root.
ANALYTICS_DIR = "analytics/data"

# Logging directory.
# Relative to the project root.
LOGS_DIR = "logs"

# Placeholder for unknown values.
UNKNOWN_VALUE = '<missing>'

# Filename extension of email files (original, full content file).
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