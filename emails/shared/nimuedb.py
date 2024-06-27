import os

import psycopg2
import numpy as np

import openai

if os.getenv("OPENAI_API_KEY") is not None:
    openai.api_key = os.getenv("OPENAI_API_KEY")
else:
    raise Exception("OPENAI_API_KEY environment variable not found")

DB_URI_FMT = "postgresql+pgvector://<username>:<password>@<host>:<port>/<database_name>"

DATABASE_NAME = "nimue_emails"
TABLE_NAME_EMAILS = "emails"
TABLE_NAME_EMBEDDINGS = "emails_vec"

VECTOR_DIMENSIONS = 3072

embedding_function = lambda x: np.random.rand(VECTOR_DIMENSIONS)


class NimueDb:
    def __init__(self,
                 username: str,
                 password: str,
                 host: str,
                 port: int = 5432):
        
        self.db_uri = (DB_URI_FMT.replace("<username>", username)
                       .replace("<password>", password)
                       .replace("<host>", host)
                       .replace("<port>", str(port))
                       .replace("<database_name>", DATABASE_NAME))
        
        self.connection = psycopg2.connect(self.db_uri)
        self.cursor = self.connection.cursor()


    def _ensure_table_exists(self):
        create_table_query = f"""
            CREATE TABLE IF NOT EXISTS {self.table_name} (
                id TEXT PRIMARY KEY,
                embedding VECTOR({self.vector_dimension}),
                metadata JSONB,
                document TEXT
            );
        """
        self.cursor.execute(create_table_query)
        self.connection.commit()

    def drop_collection(self):
        drop_table_query = f"""
            DROP TABLE IF EXISTS {COLLECTION_NAME};
        """
        self.cursor.execute(drop_table_query)
        self.connection.commit()

    def add_single(self, id: str, embedding: np.ndarray, metadata: dict, document: str):
        insert_query = f"""
            INSERT INTO {COLLECTION_NAME} (id, embedding, metadata, document)
            VALUES (%s, %s, %s, %s);
        """
        self.cursor.execute(
            insert_query, 
            (id, embedding.tolist(), psycopg2.extras.Json(metadata), document)
        )
        self.connection.commit()

    def query(self, query_embedding: np.ndarray, n_results: int = 10) -> list[dict]:
        # Cosine similarity search (adjust if using different metric)
        search_query = f"""
            SELECT id, embedding, metadata, document, 1 - (embedding <-> %s) AS distance
            FROM {COLLECTION_NAME}
            ORDER BY embedding <-> %s
            LIMIT %s;
        """
        self.cursor.execute(search_query, (query_embedding.tolist(), query_embedding.tolist(), n_results))
        results = self.cursor.fetchall()

        return [
            {
                'id': row[0],
                'distance': row[4], 
                'metadata': row[2],
                'document': row[3],
            }
            for row in results
        ]