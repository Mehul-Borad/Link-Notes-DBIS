# LinkNotes

A personal knowledge-base / wiki built for **CS349 (DBIS Lab)**. Notes link to one another via `[[Note Title]]` syntax, and the search engine ranks results by a combination of PostgreSQL full-text relevance and **PageRank-style graph centrality**, so the more-referenced concepts in your notebook surface first.

The project is deliberately database-heavy: full-text search via `tsvector` + GIN, PageRank computed inside PostgreSQL with a PL/pgSQL function and a materialized view, and shortest-path queries written as recursive CTEs.

> Full project report: [`report.pdf`](report.pdf) (LaTeX source in [`report.tex`](report.tex)).
> Prompt log used during development: [`PROMPT_LOG.md`](PROMPT_LOG.md).

---

## Features

**Notes & links**
- CRUD for notes (unique title, content, timestamps).
- Wiki-link syntax: `[[Operating Systems]]` and `[[Operating Systems|the OS note]]` (alias).
- Each note view shows outgoing links and **backlinks** (notes that point to it).

**Search & ranking**
- PostgreSQL full-text search (`tsvector` generated column + GIN index, weighted: title=A, content=B).
- PageRank computed in-database via PL/pgSQL (`compute_pagerank`), cached in a materialized view (`page_rank`).
- Combined ranking: `(1 − w) · ts_rank + w · normalized_pagerank` (default `w = 0.3`).
- Search highlights the matched terms in the open note (yellow `<mark>` in body/title; wavy underline inside `[[wiki-links]]`).

**Graph features**
- `GET /api/orphans` – notes with no incoming or outgoing edges.
- `GET /api/path?from_id=X&to_id=Y` – shortest directed path between two notes (recursive-CTE BFS, cycle-free via `INT[]` path tracking).
- Interactive **Graph view** (`react-force-graph-2d`) with rectangle nodes showing title + link/backlink counts, edge-routed arrows, freeze-on-drag (only the dragged node moves), and `localStorage`-backed layout persistence with a *Reset layout* button.

**Editor**
- `[[` autocomplete dropdown of matching note titles (↑/↓, Enter/Tab to insert with auto-`]]`, Esc to dismiss).
- Markdown-style media: `![alt](url.png|.jpg|.gif|.webp)` for images, `![alt](url.pdf)` for embedded PDFs, `[text](url)` for external links.
- File upload (`/api/upload`) for images and PDFs up to 20 MB; "Attach" button inserts the right markdown at the cursor.

**Seed**
- 25 interconnected notes covering operating systems, algorithms, networks, and compilers, plus dedicated demo notes for embeds/aliases/externals and two intentional orphans, so every feature has data to exercise it.

---

## Tech stack

| Layer | Tools |
|---|---|
| Backend | Python 3, FastAPI, psycopg2, python-multipart |
| Database | PostgreSQL 12+ (uses `tsvector`, GIN, PL/pgSQL, materialized views, recursive CTEs) |
| Frontend | React 19 (Create React App), `react-force-graph-2d` |

---

## Prerequisites

- PostgreSQL 12 or newer
- Python 3.10+
- Node.js 18+ and `npm`

## Setup

### 1. PostgreSQL

```bash
sudo -u postgres createuser -s $USER
sudo -u postgres createdb linknotes
```

(The default `DATABASE_URL` is `postgresql:///linknotes`; override via `backend/.env` if needed.)

### 2. Backend

```bash
cd backend
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
.venv/bin/python seed.py            # creates schema, seeds 25 notes, refreshes PageRank
.venv/bin/uvicorn main:app --port 8000
```

API will be live on `http://localhost:8000`.

### 3. Frontend

```bash
cd frontend
npm install
npm start                           # http://localhost:3000
```

---

## API endpoints

| Method | Path | Purpose |
|---|---|---|
| `GET` | `/api/notes` | List notes (id, title, timestamps) |
| `POST` | `/api/notes` | Create note |
| `GET` | `/api/notes/{id}` | Get note + outgoing links + backlinks |
| `PUT` | `/api/notes/{id}` | Update note (re-syncs links) |
| `DELETE` | `/api/notes/{id}` | Delete note |
| `GET` | `/api/search?q=&weight=&limit=` | FTS + PageRank-combined ranking |
| `GET` | `/api/orphans` | Notes with no incoming or outgoing edges |
| `GET` | `/api/path?from_id=&to_id=` | Shortest directed path (recursive CTE) |
| `GET` | `/api/graph` | All nodes + links (for the graph view) |
| `POST` | `/api/upload` | Upload an image or PDF |
| `POST` | `/api/admin/refresh-rankings` | Recompute PageRank materialized view |

---

## Project layout

```
backend/
  db.py            schema, init_db(), refresh_rankings(), PL/pgSQL PageRank, matview
  main.py          FastAPI app: notes CRUD, search, orphans, path, upload, graph
  seed.py          25-note seed, calls refresh_rankings() at the end
  requirements.txt
  uploads/         user-uploaded images and PDFs (gitignored)
frontend/
  src/App.js       sidebar, CRUD UI, search/orphans/path, NoteEditor with [[
                   autocomplete and file upload, view toggle, search highlighting
  src/Graph.js     react-force-graph-2d wrapper, rectangle nodes, edge-routed
                   arrows, layout persistence
  src/App.css      styling for everything above
diffs/             per-file diffs of every modified file vs the initial commit
                   (3fbcf9d), included for the assignment submission
report.tex/.pdf    project report
PROMPT_LOG.md      26 prompts used during development
```

---

## Notes & limitations

- The default `DATABASE_URL` (`postgresql:///linknotes`) relies on Unix-socket peer authentication. Set `DATABASE_URL` in `backend/.env` for any other setup.
- `REFRESH MATERIALIZED VIEW page_rank` is **not** auto-run on every save (it's not free). Hit *Refresh ranks* in the sidebar after a batch of edits, or `POST /api/admin/refresh-rankings`. The seed script refreshes it for you.
- Search is currently bounded to the GIN index and the matview; the proposal also called for a quantitative benchmark on a larger corpus (\~hundreds of notes), which is the natural next step.

---

## Authors

Mehul Borad (23B0930), Sahil (23B0943), Thanuj (23B1082), Raghav Goyal (23B0908) — CS349 Spring 2026.
