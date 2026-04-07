# LinkNotes - Prompt Log

This document logs all the prompts used during development of LinkNotes, along with what was generated and any manual changes made.

---

## Prompt 1: Initial Database Schema

**Prompt:**
> I want to build a notes app with PostgreSQL. I need two tables — one for notes (with id, title, content, and timestamps) and one for links between notes (source and target). Titles should be unique. Can you write the SQL CREATE TABLE statements?

**What I got:**
- SQL for `notes` and `links` tables with proper foreign keys and `ON DELETE CASCADE`

**Changes I made:**
- None, used it as-is

---

## Prompt 2: Python Database Connection

**Prompt:**
> Wrap that schema into a Python file using psycopg2. I need a `get_conn()` function that returns a connection and an `init_db()` function that creates the tables if they don't exist. Use environment variables for the connection string.

**What I got:**
- `db.py` with `get_conn()` and `init_db()`
- Used `RealDictCursor` so rows come back as dicts

**Changes I made:**
- The generated code used `localhost` in the connection string but my PostgreSQL uses Unix socket peer auth, so I changed it to `postgresql:///linknotes`
- Added `python-dotenv` and a `.env` file to load the database URL

---

## Prompt 3: Link Parsing Logic

**Prompt:**
> I need a function that takes a note's text content and extracts all the [[double bracket]] link targets. For example, from "Check out [[Operating Systems]] and [[B-Trees]]" it should return ["Operating Systems", "B-Trees"]. Write it in Python.

**What I got:**
- A simple regex-based `parse_links()` using `re.compile(r"\[\[(.+?)\]\]")`

**Changes I made:**
- None

---

## Prompt 4: Syncing Links to Database

**Prompt:**
> Now I need a function `sync_links(conn, note_id, content)` that: (1) deletes all existing links from that note, (2) parses [[links]] from the content, (3) for each link target, checks if a note with that title exists, and if so inserts a row into the links table. Use the parse_links function from before.

**What I got:**
- `sync_links()` that does DELETE then INSERT in a loop
- Checks target note existence before inserting

**Changes I made:**
- Added `ON CONFLICT DO NOTHING` to the INSERT because a note could link to the same target twice (e.g. mentioning [[B-Trees]] in two paragraphs) and that would violate the UNIQUE constraint

---

## Prompt 5: FastAPI CRUD Endpoints

**Prompt:**
> Write a FastAPI app with these endpoints:
> - GET /api/notes — list all notes (just id, title, timestamps)
> - POST /api/notes — create a note (title + content in body)
> - GET /api/notes/{note_id} — get full note
> - PUT /api/notes/{note_id} — update note
> - DELETE /api/notes/{note_id} — delete note
>
> Use the db.py file I already have. Call sync_links() after create and update.

**What I got:**
- Full `main.py` with all five endpoints
- Pydantic models for request bodies
- CORS middleware

**Changes I made:**
- It didn't handle the duplicate title case well — just returned a 500. I added a check for "unique" in the error message to return 409 instead.
- The create endpoint wasn't calling `conn.commit()` before `sync_links()`, so the note didn't exist yet when links were being resolved. Moved the commit.

---

## Prompt 6: Backlinks in GET Endpoint

**Prompt:**
> In the GET /api/notes/{note_id} endpoint, I also want to return backlinks — notes that link TO this note, not just notes this note links to. Can you add a second query that joins links and notes where target_note_id matches?

**What I got:**
- A second SQL query joining `links` and `notes` on `source_note_id` where `target_note_id = %s`
- Added as `note["backlinks"]` in the response

**Changes I made:**
- None, worked on first try

---

## Prompt 7: Seed Data Script

**Prompt:**
> Write a Python script that seeds the database with about 10 sample notes about CS topics like operating systems, data structures, databases, etc. Each note should have 2-4 [[links]] to other notes. Insert all notes first, then do a second pass to parse and create links.

**What I got:**
- `seed.py` with 10 notes on topics like Operating Systems, Process Management, Memory Management, CPU Scheduling, File Systems, Concurrency, Virtual Memory, Data Structures, B-Trees, Databases
- Two-pass approach: insert all, then link

**Changes I made:**
- Some of the generated notes used a `[[Operating Systems|OS]]` display-text syntax (like Wikipedia). My `parse_links` regex didn't handle this, so I updated the seed script to use a different regex that strips the `|display` part: `r"\[\[(.+?)(?:\|.+?)?\]\]"`
- Added `ON CONFLICT (title) DO UPDATE` so I can rerun the seed script without dropping tables
- Added `DELETE FROM links; DELETE FROM notes;` at the start so rerunning gives clean data

---

## Prompt 8: React App — Sidebar + Note List

**Prompt:**
> I'm building a React frontend for my notes API (at http://localhost:8000/api). Start with a sidebar that lists all notes and a main area. When I click a note in the sidebar it should fetch and display that note. Use functional components and hooks, no React Router.

**What I got:**
- Basic `App.js` with a sidebar and main content area
- `fetchNotes()` on mount, `openNote(id)` on click
- Sidebar highlights the active note

**Changes I made:**
- Wrapped `fetchNotes` in `useCallback` to fix a React warning about the useEffect dependency array
- The CSS was very plain, so I rewrote it with a dark sidebar (#1a1a2e) and accent color (#e94560)

---

## Prompt 9: React — Create, Edit, Delete

**Prompt:**
> Add create, edit, and delete functionality to the React app. I need:
> - A "+ New Note" button that shows a form with title input and content textarea
> - An "Edit" button on the note view that switches to edit mode
> - A "Delete" button with a confirmation dialog
> After any action, refresh the note list.

**What I got:**
- `creating` and `editing` state flags to toggle between view/edit/create modes
- Form with title input and textarea
- Delete with `window.confirm()`

**Changes I made:**
- The save function wasn't handling API errors — added `.json()` parsing of error responses and `alert(err.detail)` so I can see what went wrong
- Styled the buttons (primary = red accent, danger = lighter red, default = gray)

---

## Prompt 10: Rendering [[Wiki Links]] as Clickable

**Prompt:**
> In the note view, I want [[links]] in the content to be rendered as clickable text. Split the content string on the [[...]] pattern, and for each match, render a colored span that calls openNote() when clicked. If the linked note doesn't exist, show it in gray with strikethrough.

**What I got:**
- `renderContent()` function that uses `split(/(\[\[.+?\]\])/g)` to break text into parts
- Each `[[Link]]` part gets matched against the notes list and rendered as a clickable `<span>`

**Changes I made:**
- Added a `.broken` CSS class for links pointing to non-existent notes (gray + line-through + no pointer cursor)
- The function was using `notes.find(n => n.title === linkTitle)` but the note list from GET /api/notes doesn't include content, just id + title — that's fine, it works since we only need the id to navigate

---

## Prompt 11: CSS Styling

**Prompt:**
> The app looks too plain. Write CSS for a wiki-style notes app with: dark sidebar, clean main content area, nice typography, styled buttons, and pill-shaped tags for the links/backlinks sections.

**What I got:**
- Full `App.css` with flexbox layout, dark sidebar theme, form styling, tag/pill components

**Changes I made:**
- Tweaked spacing values (padding, margins)
- Changed the empty state to be vertically centered
- Added hover transitions on buttons and list items

---

## How to Run

### Backend
```bash
# Create the database
psql -c "CREATE DATABASE linknotes;"

# Install dependencies
pip install fastapi uvicorn psycopg2-binary pydantic python-dotenv

# Seed the database
python3 backend/seed.py

# Start the server
uvicorn main:app --app-dir backend --reload --port 8000
```

### Frontend
```bash
cd frontend
npm install
npm start
```

The app runs at `http://localhost:3000` with the API at `http://localhost:8000`.
