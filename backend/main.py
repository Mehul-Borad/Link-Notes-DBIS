import os
import re
import uuid
from fastapi import FastAPI, HTTPException, UploadFile, File, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from db import get_conn, init_db

UPLOADS_DIR = os.path.join(os.path.dirname(__file__), "uploads")
os.makedirs(UPLOADS_DIR, exist_ok=True)

ALLOWED_EXTS = {".png", ".jpg", ".jpeg", ".gif", ".webp", ".pdf"}
MAX_UPLOAD_BYTES = 20 * 1024 * 1024

app = FastAPI(title="LinkNotes API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/uploads", StaticFiles(directory=UPLOADS_DIR), name="uploads")

LINK_PATTERN = re.compile(r"\[\[([^\|\]]+)(?:\|[^\]]+)?\]\]")


class NoteCreate(BaseModel):
    title: str
    content: str = ""


class NoteUpdate(BaseModel):
    title: str | None = None
    content: str | None = None


def parse_links(content: str) -> list[str]:
    """Extract all [[Link Target]] references from note content."""
    return LINK_PATTERN.findall(content)


def sync_links(conn, note_id: int, content: str):
    """Parse links from content and update the links table."""
    cur = conn.cursor()
    # Remove old links from this note
    cur.execute("DELETE FROM links WHERE source_note_id = %s", (note_id,))

    targets = parse_links(content)
    for target_title in targets:
        # Only create link if target note exists
        cur.execute("SELECT id FROM notes WHERE title = %s", (target_title,))
        row = cur.fetchone()
        if row:
            cur.execute(
                "INSERT INTO links (source_note_id, target_note_id) VALUES (%s, %s) ON CONFLICT DO NOTHING",
                (note_id, row["id"]),
            )
    conn.commit()
    cur.close()


@app.on_event("startup")
def startup():
    init_db()


@app.get("/api/notes")
def list_notes():
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT id, title, created_at, updated_at FROM notes ORDER BY updated_at DESC")
    notes = cur.fetchall()
    cur.close()
    conn.close()
    return notes


@app.post("/api/notes", status_code=201)
def create_note(note: NoteCreate):
    conn = get_conn()
    cur = conn.cursor()
    try:
        cur.execute(
            "INSERT INTO notes (title, content) VALUES (%s, %s) RETURNING id, title, content, created_at, updated_at",
            (note.title, note.content),
        )
        created = cur.fetchone()
        conn.commit()
        sync_links(conn, created["id"], note.content)
    except Exception as e:
        conn.rollback()
        if "unique" in str(e).lower():
            raise HTTPException(status_code=409, detail="A note with this title already exists")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        cur.close()
        conn.close()
    return created


@app.get("/api/notes/{note_id}")
def get_note(note_id: int):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT id, title, content, created_at, updated_at FROM notes WHERE id = %s", (note_id,))
    note = cur.fetchone()
    if not note:
        cur.close()
        conn.close()
        raise HTTPException(status_code=404, detail="Note not found")

    # Get outgoing links
    cur.execute("""
        SELECT n.id, n.title FROM links l
        JOIN notes n ON n.id = l.target_note_id
        WHERE l.source_note_id = %s
    """, (note_id,))
    note["links"] = cur.fetchall()

    # Get backlinks
    cur.execute("""
        SELECT n.id, n.title FROM links l
        JOIN notes n ON n.id = l.source_note_id
        WHERE l.target_note_id = %s
    """, (note_id,))
    note["backlinks"] = cur.fetchall()

    cur.close()
    conn.close()
    return note


@app.put("/api/notes/{note_id}")
def update_note(note_id: int, note: NoteUpdate):
    conn = get_conn()
    cur = conn.cursor()

    cur.execute("SELECT id FROM notes WHERE id = %s", (note_id,))
    if not cur.fetchone():
        cur.close()
        conn.close()
        raise HTTPException(status_code=404, detail="Note not found")

    updates = []
    values = []
    if note.title is not None:
        updates.append("title = %s")
        values.append(note.title)
    if note.content is not None:
        updates.append("content = %s")
        values.append(note.content)

    if not updates:
        raise HTTPException(status_code=400, detail="No fields to update")

    updates.append("updated_at = NOW()")
    values.append(note_id)

    try:
        cur.execute(
            f"UPDATE notes SET {', '.join(updates)} WHERE id = %s RETURNING id, title, content, created_at, updated_at",
            values,
        )
        updated = cur.fetchone()
        conn.commit()
        if note.content is not None:
            sync_links(conn, note_id, note.content)
    except Exception as e:
        conn.rollback()
        if "unique" in str(e).lower():
            raise HTTPException(status_code=409, detail="A note with this title already exists")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        cur.close()
        conn.close()
    return updated


@app.delete("/api/notes/{note_id}")
def delete_note(note_id: int):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("DELETE FROM notes WHERE id = %s RETURNING id", (note_id,))
    deleted = cur.fetchone()
    cur.close()
    conn.commit()
    conn.close()
    if not deleted:
        raise HTTPException(status_code=404, detail="Note not found")
    return {"message": "Note deleted"}


@app.get("/api/search")
def search(q: str, weight: float = 0.3, limit: int = 20):
    """Combined ranking: (1-weight)*ts_rank + weight*normalized_pagerank."""
    if not q.strip():
        return []
    weight = max(0.0, min(1.0, weight))
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(
        """
        WITH query AS (SELECT plainto_tsquery('english', %s) AS q)
        SELECT
            n.id,
            n.title,
            ts_rank(n.search_vector, query.q) AS text_score,
            COALESCE(pr.score, 0) AS graph_score,
            ((1 - %s) * ts_rank(n.search_vector, query.q)
             + %s * COALESCE(pr.score, 0)) AS combined_score,
            ts_headline(
                'english', n.content, query.q,
                'MaxWords=25, MinWords=10, ShortWord=3, HighlightAll=false'
            ) AS snippet
        FROM notes n
        LEFT JOIN page_rank pr ON pr.note_id = n.id
        CROSS JOIN query
        WHERE n.search_vector @@ query.q
        ORDER BY combined_score DESC
        LIMIT %s
        """,
        (q, weight, weight, limit),
    )
    results = cur.fetchall()
    cur.close()
    conn.close()
    return results


@app.get("/api/orphans")
def list_orphans():
    """Notes with no incoming and no outgoing links."""
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(
        """
        SELECT n.id, n.title
        FROM notes n
        WHERE NOT EXISTS (
            SELECT 1 FROM links
            WHERE source_note_id = n.id OR target_note_id = n.id
        )
        ORDER BY n.title
        """
    )
    orphans = cur.fetchall()
    cur.close()
    conn.close()
    return orphans


@app.get("/api/path")
def shortest_path(from_id: int, to_id: int, max_depth: int = 8):
    """BFS shortest directed path from from_id to to_id over the link graph."""
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(
        """
        WITH RECURSIVE bfs(node, depth, path) AS (
            SELECT %s::int, 0, ARRAY[%s::int]
            UNION ALL
            SELECT l.target_note_id, b.depth + 1, b.path || l.target_note_id
            FROM bfs b
            JOIN links l ON l.source_note_id = b.node
            WHERE b.depth < %s AND NOT (l.target_note_id = ANY(b.path))
        )
        SELECT depth, path FROM bfs WHERE node = %s ORDER BY depth LIMIT 1
        """,
        (from_id, from_id, max_depth, to_id),
    )
    row = cur.fetchone()
    if not row:
        cur.close()
        conn.close()
        return {"found": False, "path": []}

    path_ids = row["path"]
    cur.execute("SELECT id, title FROM notes WHERE id = ANY(%s)", (path_ids,))
    titles = {n["id"]: n["title"] for n in cur.fetchall()}
    cur.close()
    conn.close()
    return {
        "found": True,
        "depth": row["depth"],
        "path": [{"id": i, "title": titles.get(i, "?")} for i in path_ids],
    }


@app.post("/api/upload")
async def upload_file(request: Request, file: UploadFile = File(...)):
    """Accept an image or PDF, store under uploads/, return the served URL."""
    original = file.filename or "upload"
    ext = os.path.splitext(original)[1].lower()
    if ext not in ALLOWED_EXTS:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type '{ext}'. Allowed: {sorted(ALLOWED_EXTS)}",
        )

    contents = await file.read()
    if len(contents) > MAX_UPLOAD_BYTES:
        raise HTTPException(status_code=413, detail="File too large (max 20 MB)")

    new_name = f"{uuid.uuid4().hex}{ext}"
    with open(os.path.join(UPLOADS_DIR, new_name), "wb") as f:
        f.write(contents)

    base = str(request.base_url).rstrip("/")
    return {
        "url": f"{base}/uploads/{new_name}",
        "filename": original,
        "kind": "pdf" if ext == ".pdf" else "image",
        "size": len(contents),
    }


@app.get("/api/graph")
def get_graph():
    """Full link graph: nodes (with PageRank score) + directed edges."""
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(
        """
        SELECT n.id, n.title, COALESCE(pr.score, 0) AS score
        FROM notes n
        LEFT JOIN page_rank pr ON pr.note_id = n.id
        ORDER BY n.id
        """
    )
    nodes = cur.fetchall()
    cur.execute("SELECT source_note_id, target_note_id FROM links")
    links = [
        {"source": r["source_note_id"], "target": r["target_note_id"]}
        for r in cur.fetchall()
    ]
    cur.close()
    conn.close()
    return {"nodes": nodes, "links": links}


@app.post("/api/admin/refresh-rankings")
def refresh_rankings_endpoint():
    """Recompute PageRank by refreshing the materialized view."""
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("REFRESH MATERIALIZED VIEW page_rank;")
    conn.commit()
    cur.execute("SELECT COUNT(*) AS n FROM page_rank;")
    n = cur.fetchone()["n"]
    cur.close()
    conn.close()
    return {"refreshed": True, "rows": n}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", reload=True)
