# Mind the gitignore file if you change this.
ANALYTICS_PATH = "./analytics"

# Placeholder for unknown values.
UNKNOWN_VALUE = '<missing>'

# Filename extension of email files.
EMAIL_EXTENSION = 'txt'

# Filename extension of metadata files.
METADATA_EXTENSION = 'json'

# Filename extension of embedding files.
EMBEDDING_EXTENSION = 'pkl'

# Embedding model to use.
EMBEDDING_MODEL = 'text-embedding-3-large'

# Maximum chunk size per embedding.
EMBEDDING_CHUNK_SIZE = 8192  # NOTE: OpenAI limit is 8192 tokens.

# Vector database collection name.
EMAIL_COLLECTION_NAME = "emails"