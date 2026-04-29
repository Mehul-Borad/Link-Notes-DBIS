# LinkNotes - Prompt Log

Prompts used while building this project. Used Claude (Sonnet) for most of the code generation, copy-pasted and modified as needed.

---

## Prompt 1

> i need a postgres schema for a notes app. theres two tables - notes and links. notes has id title content and timestamps, links stores which note links to which note. titles should be unique. give me the CREATE TABLE sql

---

## Prompt 2

> can you put this in a python file? i want a function that connects to postgres using psycopg2 and another function that runs the CREATE TABLE statements. use env variables for the db url

---

## Prompt 3

> write a python function that takes a string and returns all the text inside double square brackets. like if i give it "check [[Operating Systems]] and [[B-Trees]]" it should return ["Operating Systems", "B-Trees"]

---

## Prompt 4

> ok now i need a function that takes a db connection, a note id, and the note content. it should delete all existing links from that note in the links table, then use the regex function to find all [[links]], and for each one check if a note with that title exists, and if yes insert a row into links table

---

## Prompt 5

> write me a fastapi app with these routes:
> GET /api/notes - returns all notes
> POST /api/notes - creates a note
> GET /api/notes/{note_id} - returns one note
> PUT /api/notes/{note_id} - updates a note  
> DELETE /api/notes/{note_id} - deletes a note
> use my db.py for connections. after creating or updating a note call sync_links

---

## Prompt 6

> in the get single note endpoint can you also return which notes link TO this note? like backlinks. so query the links table where target_note_id = the current note and join to get the source note titles

---

## Prompt 7

> i need a seed script to fill the database with sample data for testing. make like 10 notes about CS topics (operating systems, memory management, databases, data structures etc). each one should have [[links]] to a few other notes. remember you need to insert ALL notes first before parsing links because a link target might not exist yet

---

## Prompt 8

> now i need a react frontend. start simple - sidebar on the left that shows all note titles, clicking one fetches it and shows it in the main area. api is at http://localhost:8000/api. use useState and useEffect, no react router

---

## Prompt 9

> add create edit and delete to the react app. new note button at top of sidebar that shows a form. edit button on the note view that lets you change title and content. delete button with confirmation. refresh the list after each action

---

## Prompt 10

> in the note content display, i want [[links]] to show up as clickable red text. when you click one it should open that note. if the target note doesnt exist show it in gray with strikethrough. split the content on the [[ ]] pattern and render each piece

---

## Prompt 11

> the app still looks pretty ugly. write me better css. i want a clean wiki-style look - dark sidebar, light main area, nice font, the links/backlinks should show as little pill shaped tags, good spacing overall

---

## Prompt 12

> found a bug. when i write [[Operating Systems|OS]] the link doesnt actually get inserted in the links table because the regex captures "Operating Systems|OS" as the title and theres no note with that exact name. fix the regex in main.py so it only captures the part before the |. also fix the same thing in the frontend renderer — the alias should be what gets shown but clicking should still open the original note

---

## Prompt 13

> add full text search. add a tsvector column to the notes table that's auto generated from title and content. use setweight so title hits matter more than content hits. put a GIN index on it. then make a /api/search?q=... endpoint that returns the matching notes with ts_rank scores and a ts_headline snippet. dont use LIKE

---

## Prompt 14

> now write a plpgsql function compute_pagerank that does the standard pagerank iteration over the links table. damping 0.85, max 30 iterations, stop early if delta < 0.0001. wrap it in a materialized view called page_rank that also stores a normalized score in [0,1]. add a POST /api/admin/refresh-rankings endpoint to refresh the view. also call refresh_rankings() at the end of seed.py so the seed populates it

---

## Prompt 15

> in the search endpoint combine ts_rank with the pagerank score. (1-w)*text_score + w*graph_score, default w=0.3. left join page_rank on note_id. so notes that are linked to a lot will rank higher even if the text match is weaker. return text_score, graph_score, and combined_score so i can see the breakdown

---

## Prompt 16

> two more endpoints
> GET /api/orphans - notes that have no links in or out, use NOT EXISTS
> GET /api/path?from_id=X&to_id=Y - shortest directed path between two notes. use a recursive CTE doing BFS over the links table. carry the path as an int[] and check NOT (target = ANY(path)) to avoid cycles. cap depth at 8. return depth and the list of notes in the path

---

## Prompt 17

> wire all these up in the react app
> - search bar at the top of the sidebar. when you type and hit enter the note list gets replaced with results showing title and the score breakdown
> - a small "Orphans" button that loads the orphans into the sidebar
> - a "Refresh ranks" button that calls the admin endpoint
> - on each note view a "Find path to:" form with a datalist of titles. show the result as a chain of pill tags A → B → C, each clickable to open that note

---

## Prompt 18

> getting this when seed.py runs:
> psycopg2.errors.InsufficientPrivilege: cannot create temporary table within security-restricted operation
> CONTEXT: SQL statement "CREATE TEMP TABLE _pr_curr ..."
> the pagerank function uses temp tables but REFRESH MATERIALIZED VIEW runs in a security restricted context that doesnt allow temp table creation. switch to a persistent unlogged table called pr_state created in the schema, and have the function only DELETE/INSERT/UPDATE that table

---

## Prompt 19

> when we search and click a result, highlight the matching keywords in the displayed note (title and content). dont break the [[wiki link]] rendering. for normal text use a yellow mark, for matches inside wiki links use a wavy underline so the link styling stays. clear highlights when search is cleared

---

## Prompt 20

> when im typing [[ in the note editor, show a dropdown of matching note titles below where im typing. arrow up/down to navigate, enter or tab to insert (auto adds the closing ]] and moves cursor after), escape to close. case insensitive substring match. should work in both the create and edit textareas, factor it into a NoteEditor component so theres no duplication

---

## Prompt 21

> add support for embedding images and pdfs and external website links inside notes. use markdown syntax:
> ![alt](url) - embed (image if extension is png/jpg/gif/webp, pdf iframe if .pdf)
> [text](url) - external link, opens in new tab
> rewrite renderContent to be a single tokenizer pass that handles [[wiki]], embeds, and external links together. dont break search highlighting

---

## Prompt 22

> add a graph view page. new file Graph.js. backend endpoint GET /api/graph that returns nodes (with pagerank score) and links (source, target). use react-force-graph-2d (npm install it). zoomable, pannable, hoverable nodes with tooltip showing pagerank, click a node to open the note. add a toggle button in the sidebar to switch between the notes view and the graph view

---

## Prompt 23

> i want to upload actual files (png/jpg/pdf), not just paste URLs. add a POST /api/upload endpoint in fastapi that accepts a multipart file, validates the extension, caps at 20MB, saves it under backend/uploads/ with a uuid filename, and returns the served URL. mount /uploads as static files. add an "Attach image / PDF" button in NoteEditor that opens a file picker and inserts ![filename](url) at the cursor on success. python-multipart needs to be added to requirements.txt. also add a .gitignore so uploads/ doesnt get committed

---

## Prompt 24

> redo the graph
> - nodes should be rounded rectangles, not circles
> - each node shows the title (bold), then "→ N links" and "← N backlinks" using the link counts (compute them from the links array client-side after fetching)
> - selected note should be highlighted (red border, light yellow tint)
> - arrows should end at the rectangle edge, not at the center. write a custom linkCanvasObject that computes where the line crosses the target's rect edge
> - right now when i drag a node the whole layout wobbles because of physics. i want only the node im dragging to move. after the initial layout settles, pin every node by setting fx/fy = x/y. on drag end, update the dragged node's fx/fy so it stays put at the new spot
> - also bump link distance and charge so the nodes start spread out

---

## Prompt 25

> persist the node positions across reloads. on every drag-end save {id: {x, y}} into localStorage under "linknotes-graph-layout-v1". on graph mount, restore them by setting fx/fy on each node before passing the data to ForceGraph2D. nodes that dont have a saved position get force-laid-out around the pinned ones. also add a "Reset layout" button in the corner of the graph view that wipes the saved positions and re-runs the simulation
