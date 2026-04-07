import re
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from db import get_conn, init_db

app = FastAPI(title="LinkNotes API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

LINK_PATTERN = re.compile(r"\[\[(.+?)\]\]")


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
