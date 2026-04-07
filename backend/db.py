import os
import psycopg2
from psycopg2.extras import RealDictCursor
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql:///linknotes")


def get_conn():
    return psycopg2.connect(DATABASE_URL, cursor_factory=RealDictCursor)


def init_db():
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS notes (
            id SERIAL PRIMARY KEY,
            title VARCHAR(255) NOT NULL UNIQUE,
            content TEXT NOT NULL DEFAULT '',
            created_at TIMESTAMP DEFAULT NOW(),
            updated_at TIMESTAMP DEFAULT NOW()
        );

        CREATE TABLE IF NOT EXISTS links (
            id SERIAL PRIMARY KEY,
            source_note_id INTEGER NOT NULL REFERENCES notes(id) ON DELETE CASCADE,
            target_note_id INTEGER NOT NULL REFERENCES notes(id) ON DELETE CASCADE,
            UNIQUE(source_note_id, target_note_id)
        );

        CREATE INDEX IF NOT EXISTS idx_links_source ON links(source_note_id);
        CREATE INDEX IF NOT EXISTS idx_links_target ON links(target_note_id);
    """)
    conn.commit()
    cur.close()
    conn.close()
