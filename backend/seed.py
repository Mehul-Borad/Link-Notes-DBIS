"""Seed the database with sample interconnected notes."""
from db import get_conn, init_db

SAMPLE_NOTES = [
    {
        "title": "Operating Systems",
        "content": """An operating system (OS) is system software that manages computer hardware and software resources.

Key concepts:
- [[Process Management]] handles creation, scheduling, and termination of processes.
- [[Memory Management]] deals with allocation and deallocation of memory.
- [[File Systems]] provide a way to store and retrieve data.
- The [[CPU Scheduling]] algorithm determines which process runs next.

Popular operating systems include Linux, Windows, and macOS.""",
    },
    {
        "title": "Process Management",
        "content": """Process management involves handling the lifecycle of processes in an [[Operating Systems|OS]].

A process is a program in execution. Each process has:
- A process ID (PID)
- A program counter
- Registers and stack

Related topics:
- [[CPU Scheduling]] determines process execution order.
- [[Concurrency]] deals with multiple processes executing simultaneously.
- Inter-process communication (IPC) allows processes to exchange data.""",
    },
    {
        "title": "Memory Management",
        "content": """Memory management is the functionality of an [[Operating Systems|OS]] that handles primary memory.

Techniques include:
- Paging: divides memory into fixed-size pages.
- Segmentation: divides memory into variable-size segments.
- [[Virtual Memory]] allows execution of processes not completely in memory.

Memory management must handle allocation, deallocation, and protection of memory spaces.""",
    },
    {
        "title": "CPU Scheduling",
        "content": """CPU scheduling is the basis of multiprogrammed [[Operating Systems]].

Common algorithms:
- First-Come, First-Served (FCFS)
- Shortest Job First (SJF)
- Round Robin (RR)
- Priority Scheduling

The goal is to maximize CPU utilization and throughput while minimizing waiting time.
Related: [[Process Management]], [[Concurrency]].""",
    },
    {
        "title": "File Systems",
        "content": """A file system controls how data is stored and retrieved in an [[Operating Systems|OS]].

Common file systems:
- ext4 (Linux)
- NTFS (Windows)
- APFS (macOS)

Key concepts include inodes, directories, file permissions, and journaling.
See also: [[Data Structures]] used in file system implementation like [[B-Trees]].""",
    },
    {
        "title": "Concurrency",
        "content": """Concurrency is the ability of different parts of a program to be executed out of order.

Key challenges:
- Race conditions
- Deadlocks
- Starvation

Solutions involve locks, semaphores, and monitors.
Related to [[Process Management]] and [[CPU Scheduling]] in [[Operating Systems]].""",
    },
    {
        "title": "Virtual Memory",
        "content": """Virtual memory is a [[Memory Management]] technique that provides an idealized abstraction of the storage resources.

It uses both hardware and software to allow a computer to compensate for physical memory shortages by temporarily transferring data to disk.

Key concepts: page tables, TLB, page faults, and swapping.
See also: [[Operating Systems]], [[Data Structures]].""",
    },
    {
        "title": "Data Structures",
        "content": """Data structures are ways of organizing and storing data for efficient access and modification.

Common data structures:
- Arrays and Linked Lists
- Stacks and Queues
- [[B-Trees]] and Hash Tables
- Graphs

Used extensively in [[File Systems]], [[Databases]], and algorithm design.""",
    },
    {
        "title": "B-Trees",
        "content": """A B-Tree is a self-balancing tree [[Data Structures|data structure]] that maintains sorted data.

Properties:
- All leaves are at the same level
- A node can have multiple keys
- Commonly used in [[Databases]] and [[File Systems]]

B-Trees minimize disk I/O operations, making them ideal for storage systems.""",
    },
    {
        "title": "Databases",
        "content": """A database is an organized collection of structured information stored electronically.

Key concepts:
- Relational model and SQL
- [[B-Trees]] for indexing
- Transaction management (ACID properties)
- Normalization

Database management systems (DBMS) like PostgreSQL use [[Data Structures]] extensively.
See also: [[File Systems]] for underlying storage.""",
    },
]


def seed():
    init_db()
    conn = get_conn()
    cur = conn.cursor()

    # Clear existing data
    cur.execute("DELETE FROM links")
    cur.execute("DELETE FROM notes")
    conn.commit()

    # Insert notes
    for note in SAMPLE_NOTES:
        cur.execute(
            "INSERT INTO notes (title, content) VALUES (%s, %s) ON CONFLICT (title) DO UPDATE SET content = EXCLUDED.content",
            (note["title"], note["content"]),
        )
    conn.commit()

    # Now parse links (all notes exist)
    import re
    link_pattern = re.compile(r"\[\[(.+?)(?:\|.+?)?\]\]")

    for note in SAMPLE_NOTES:
        cur.execute("SELECT id FROM notes WHERE title = %s", (note["title"],))
        source = cur.fetchone()
        targets = link_pattern.findall(note["content"])
        for target_title in targets:
            cur.execute("SELECT id FROM notes WHERE title = %s", (target_title,))
            target = cur.fetchone()
            if target:
                cur.execute(
                    "INSERT INTO links (source_note_id, target_note_id) VALUES (%s, %s) ON CONFLICT DO NOTHING",
                    (source["id"], target["id"]),
                )
    conn.commit()
    cur.close()
    conn.close()
    print(f"Seeded {len(SAMPLE_NOTES)} notes with links.")


if __name__ == "__main__":
    seed()
