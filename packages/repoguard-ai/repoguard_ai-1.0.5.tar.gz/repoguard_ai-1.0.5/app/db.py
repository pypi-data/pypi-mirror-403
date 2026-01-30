import psycopg2
import os


def get_conn():
    return psycopg2.connect(os.getenv("DATABASE_URL"))

def init_db():
    connect=get_conn()
    with connect.cursor() as cur:
     cur.execute("""
        CREATE TABLE IF NOT EXISTS doc_chunks(
                id SERIAL PRIMARY KEY,
                repo_id TEXT NOT NULL,
                authority TEXT NOT NULL,
                heading TEXT NOT NULL,
                content TEXT NOT NULL,
                embedding REAL[] NOT NULL
        );
    """)
    connect.commit()
    connect.close()

init_db()