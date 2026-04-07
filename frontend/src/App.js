import React, { useState, useEffect, useCallback } from "react";
import "./App.css";

const API = "http://localhost:8000/api";

function App() {
  const [notes, setNotes] = useState([]);
  const [selectedNote, setSelectedNote] = useState(null);
  const [editing, setEditing] = useState(false);
  const [title, setTitle] = useState("");
  const [content, setContent] = useState("");
  const [creating, setCreating] = useState(false);

  const fetchNotes = useCallback(async () => {
    const res = await fetch(`${API}/notes`);
    const data = await res.json();
    setNotes(data);
  }, []);

  useEffect(() => {
    fetchNotes();
  }, [fetchNotes]);

  const openNote = async (id) => {
    const res = await fetch(`${API}/notes/${id}`);
    const data = await res.json();
    setSelectedNote(data);
    setEditing(false);
    setCreating(false);
  };

  const startCreate = () => {
    setSelectedNote(null);
    setCreating(true);
    setEditing(false);
    setTitle("");
    setContent("");
  };

  const saveNewNote = async () => {
    if (!title.trim()) return;
    const res = await fetch(`${API}/notes`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ title, content }),
    });
    if (res.ok) {
      const created = await res.json();
      setCreating(false);
      fetchNotes();
      openNote(created.id);
    } else {
      const err = await res.json();
      alert(err.detail || "Error creating note");
    }
  };

  const startEdit = () => {
    setTitle(selectedNote.title);
    setContent(selectedNote.content);
    setEditing(true);
  };

  const saveEdit = async () => {
    const res = await fetch(`${API}/notes/${selectedNote.id}`, {
      method: "PUT",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ title, content }),
    });
    if (res.ok) {
      setEditing(false);
      fetchNotes();
      openNote(selectedNote.id);
    } else {
      const err = await res.json();
      alert(err.detail || "Error updating note");
    }
  };

  const deleteNote = async () => {
    if (!window.confirm("Delete this note?")) return;
    await fetch(`${API}/notes/${selectedNote.id}`, { method: "DELETE" });
    setSelectedNote(null);
    fetchNotes();
  };

  // Render note content with clickable [[links]]
  const renderContent = (text) => {
    const parts = text.split(/(\[\[.+?\]\])/g);
    return parts.map((part, i) => {
      const match = part.match(/^\[\[(.+?)\]\]$/);
      if (match) {
        const linkTitle = match[1];
        const linked = notes.find((n) => n.title === linkTitle);
        if (linked) {
          return (
            <span
              key={i}
              className="wiki-link"
              onClick={() => openNote(linked.id)}
            >
              {linkTitle}
            </span>
          );
        }
        return (
          <span key={i} className="wiki-link broken">
            {linkTitle}
          </span>
        );
      }
      return <span key={i}>{part}</span>;
    });
  };

  return (
    <div className="app">
      <aside className="sidebar">
        <h2>LinkNotes</h2>
        <button className="btn btn-primary" onClick={startCreate}>
          + New Note
        </button>
        <ul className="note-list">
          {notes.map((n) => (
            <li
              key={n.id}
              className={selectedNote?.id === n.id ? "active" : ""}
              onClick={() => openNote(n.id)}
            >
              {n.title}
            </li>
          ))}
        </ul>
      </aside>

      <main className="main-content">
        {creating && (
          <div className="note-view">
            <input
              className="note-title-input"
              placeholder="Note title..."
              value={title}
              onChange={(e) => setTitle(e.target.value)}
            />
            <textarea
              className="note-content-input"
              placeholder="Write your note... Use [[Note Title]] to link to other notes."
              value={content}
              onChange={(e) => setContent(e.target.value)}
            />
            <div className="actions">
              <button className="btn btn-primary" onClick={saveNewNote}>
                Save
              </button>
              <button className="btn" onClick={() => setCreating(false)}>
                Cancel
              </button>
            </div>
          </div>
        )}

        {selectedNote && !editing && (
          <div className="note-view">
            <h1>{selectedNote.title}</h1>
            <div className="note-content">{renderContent(selectedNote.content)}</div>

            {selectedNote.links?.length > 0 && (
              <div className="note-links">
                <h3>Links to:</h3>
                {selectedNote.links.map((l) => (
                  <span key={l.id} className="tag" onClick={() => openNote(l.id)}>
                    {l.title}
                  </span>
                ))}
              </div>
            )}

            {selectedNote.backlinks?.length > 0 && (
              <div className="note-links">
                <h3>Linked from:</h3>
                {selectedNote.backlinks.map((l) => (
                  <span key={l.id} className="tag" onClick={() => openNote(l.id)}>
                    {l.title}
                  </span>
                ))}
              </div>
            )}

            <div className="actions">
              <button className="btn btn-primary" onClick={startEdit}>
                Edit
              </button>
              <button className="btn btn-danger" onClick={deleteNote}>
                Delete
              </button>
            </div>
          </div>
        )}

        {selectedNote && editing && (
          <div className="note-view">
            <input
              className="note-title-input"
              value={title}
              onChange={(e) => setTitle(e.target.value)}
            />
            <textarea
              className="note-content-input"
              value={content}
              onChange={(e) => setContent(e.target.value)}
            />
            <div className="actions">
              <button className="btn btn-primary" onClick={saveEdit}>
                Save
              </button>
              <button className="btn" onClick={() => setEditing(false)}>
                Cancel
              </button>
            </div>
          </div>
        )}

        {!selectedNote && !creating && (
          <div className="empty-state">
            <h2>Welcome to LinkNotes</h2>
            <p>Select a note from the sidebar or create a new one.</p>
            <p>
              Link notes together using <code>[[Note Title]]</code> syntax.
            </p>
          </div>
        )}
      </main>
    </div>
  );
}

export default App;
