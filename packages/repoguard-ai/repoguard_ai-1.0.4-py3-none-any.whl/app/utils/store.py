import os
import psycopg2
from app.models.chunk import Chunk
from app.db import get_conn

def store_chunks(con,repo_id:str,chunks:list[Chunk]):
    con=get_conn()
    with con.cursor() as cur:
        for chunk in chunks:
            cur.execute(
                """
                INSERT INTO doc_chunks (repo_id,authority, heading, content, embedding)
                VALUES (%s,%s, %s, %s, %s)
                """,
                (
                    repo_id,
                    chunk.authority,
                    chunk.heading,
                    chunk.content,
                    chunk.embedding
                )
            )
    con.commit()