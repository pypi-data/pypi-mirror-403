import os
from app.utils.search import Chunk

def load_chunks(conn,repo_id:str)->list[Chunk]:
    with conn.cursor() as curr:
        curr.execute(
            """
            SELECT authority,heading,content,embedding
            FROM doc_chunks
            WHERE repo_id=%s
            """,
            (repo_id,)
        )
        rows=curr.fetchall()

    chunks=[]
    for authority,heading,content,embedding in rows:
        chunks.append(
            Chunk(
                authority=authority,
                heading=heading,
                content=content,
                embedding=embedding
            )
        )
    return chunks