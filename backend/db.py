import os
import psycopg2
from psycopg2.extras import RealDictCursor
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql:///linknotes")


def get_conn():
    return psycopg2.connect(DATABASE_URL, cursor_factory=RealDictCursor)


SCHEMA_SQL = """
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

ALTER TABLE notes ADD COLUMN IF NOT EXISTS search_vector tsvector
    GENERATED ALWAYS AS (
        setweight(to_tsvector('english', coalesce(title, '')), 'A') ||
        setweight(to_tsvector('english', coalesce(content, '')), 'B')
    ) STORED;

CREATE INDEX IF NOT EXISTS idx_notes_search ON notes USING GIN(search_vector);

CREATE UNLOGGED TABLE IF NOT EXISTS pr_state (
    id int PRIMARY KEY,
    curr float NOT NULL,
    nxt float
);
"""


PAGERANK_FN_SQL = """
CREATE OR REPLACE FUNCTION compute_pagerank(
    damping float DEFAULT 0.85,
    max_iter int DEFAULT 30,
    tolerance float DEFAULT 0.0001
) RETURNS TABLE(note_id int, score float) AS $$
DECLARE
    total int;
    iter int := 0;
    delta float := 1.0;
BEGIN
    SELECT count(*) INTO total FROM notes;
    IF total = 0 THEN
        RETURN;
    END IF;

    DELETE FROM pr_state;
    INSERT INTO pr_state (id, curr, nxt)
        SELECT n.id, 1.0 / total, 0 FROM notes n;

    WHILE iter < max_iter AND delta > tolerance LOOP
        UPDATE pr_state s SET nxt = sub.new_rank
        FROM (
            SELECT
                nt.id,
                (1.0 - damping) / total + damping * COALESCE(c.contrib, 0) AS new_rank
            FROM notes nt
            LEFT JOIN (
                SELECT l.target_note_id AS id, SUM(p.curr / od.deg) AS contrib
                FROM pr_state p
                JOIN links l ON l.source_note_id = p.id
                JOIN (
                    SELECT source_note_id, COUNT(*)::float AS deg
                    FROM links GROUP BY source_note_id
                ) od ON od.source_note_id = p.id
                GROUP BY l.target_note_id
            ) c ON c.id = nt.id
        ) sub
        WHERE s.id = sub.id;

        SELECT COALESCE(SUM(ABS(curr - nxt)), 0) INTO delta FROM pr_state;
        UPDATE pr_state SET curr = nxt;

        iter := iter + 1;
    END LOOP;

    RETURN QUERY SELECT s.id, s.curr FROM pr_state s;
END;
$$ LANGUAGE plpgsql;
"""


MATVIEW_SQL = """
CREATE MATERIALIZED VIEW IF NOT EXISTS page_rank AS
WITH r AS MATERIALIZED (SELECT note_id, score FROM compute_pagerank()),
     m AS (SELECT COALESCE(NULLIF(MAX(score), 0), 1) AS max_score FROM r)
SELECT
    r.note_id,
    r.score AS raw_score,
    r.score / m.max_score AS score
FROM r CROSS JOIN m;

CREATE UNIQUE INDEX IF NOT EXISTS idx_page_rank_id ON page_rank(note_id);
CREATE INDEX IF NOT EXISTS idx_page_rank_score ON page_rank(score DESC);
"""


def init_db():
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(SCHEMA_SQL)
    cur.execute(PAGERANK_FN_SQL)
    cur.execute(MATVIEW_SQL)
    conn.commit()
    cur.close()
    conn.close()


def refresh_rankings():
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("REFRESH MATERIALIZED VIEW page_rank;")
    conn.commit()
    cur.close()
    conn.close()
