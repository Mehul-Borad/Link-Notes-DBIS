"""Seed the database with sample interconnected notes."""
from db import get_conn, init_db, refresh_rankings

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
    # --- Algorithms cluster (extended seed for richer testing) ---
    {
        "title": "Algorithms",
        "content": """An algorithm is a finite sequence of well-defined instructions that solves a problem in a finite number of steps.

Common algorithm classes:
- [[Sorting]] - arranging items in order
- Search - linear, binary, hash-based
- [[Dynamic Programming]] - solving problems by combining sub-solutions
- Greedy methods, divide-and-conquer

Algorithms are designed on top of particular [[Data Structures|data structures]] and analyzed for correctness and time/space complexity. See also: [[Hash Tables]] and [[B-Trees]].""",
    },
    {
        "title": "Sorting",
        "content": """Sorting arranges elements of a list in a specific order (typically ascending).

Comparison-based [[Algorithms]]:
- Quicksort, Mergesort, Heapsort - O(n log n)
- Insertion sort, Bubble sort - O(n^2)

Non-comparison sorts (Counting, Radix, Bucket) can do better than O(n log n) under restrictions on input.

Stable sorts preserve the relative order of equal keys, which matters when sorting [[Data Structures|data structures]] like records by multiple fields.""",
    },
    {
        "title": "Dynamic Programming",
        "content": """Dynamic Programming (DP) solves problems by breaking them into overlapping sub-problems and reusing answers.

Two ingredients:
- Optimal substructure
- Overlapping sub-problems

Classic examples include shortest paths, edit distance, knapsack, and matrix chain multiplication.

Closely related to [[Algorithms|algorithm]] design and often implemented with arrays or [[Hash Tables]] as memoization tables.""",
    },
    {
        "title": "Hash Tables",
        "content": """A hash table is a [[Data Structures|data structure]] mapping keys to values via a hash function, giving O(1) expected lookup.

Collisions are handled by:
- Separate chaining (linked lists per bucket)
- Open addressing (linear/quadratic probing)

Used heavily in [[Algorithms]], [[Databases]] (hash indexes), and language runtimes (dictionaries, sets). Worst-case behavior degrades when the hash function is poor or under adversarial input.""",
    },
    # --- Networks cluster ---
    {
        "title": "Computer Networks",
        "content": """Computer networks connect machines so they can exchange information.

Models and concepts:
- OSI 7-layer model
- TCP/IP 4-layer model (see [[TCP IP]])
- Routing, switching, addressing

Networking is implemented at the [[Operating Systems|OS]] level via the network stack and is the substrate for protocols like [[HTTP]].""",
    },
    {
        "title": "TCP IP",
        "content": """TCP/IP is the protocol suite that powers the modern internet.

Layers:
1. Link (Ethernet, Wi-Fi)
2. Internet (IP)
3. Transport (TCP, UDP)
4. Application ([[HTTP]], DNS, SMTP)

Closely tied to [[Computer Networks]] and to [[Operating Systems]] which implement the stack in kernel space.""",
    },
    {
        "title": "HTTP",
        "content": """HTTP (HyperText Transfer Protocol) is the application-layer protocol of the World Wide Web.

Key features:
- Stateless request/response
- Methods: GET, POST, PUT, DELETE, etc.
- Status codes (2xx, 3xx, 4xx, 5xx)
- Sits on top of [[TCP IP|TCP]]

Modern variants HTTP/2 and HTTP/3 multiplex requests and use binary framing. Crucial for understanding [[Computer Networks]].""",
    },
    # --- Compilers cluster (creates a longer path for /api/path testing) ---
    {
        "title": "Compilers",
        "content": """A compiler translates source code from a high-level language into a lower-level language (typically machine code).

Major phases:
- [[Lexical Analysis]] - tokenization
- [[Parsing]] - building a syntax tree
- Semantic analysis - type checking
- Optimization
- Code generation

Compilers depend heavily on [[Data Structures]] (trees, graphs, symbol tables) and rely on services from the [[Operating Systems]].""",
    },
    {
        "title": "Parsing",
        "content": """Parsing builds a structured representation (parse tree / AST) from a stream of tokens produced by [[Lexical Analysis]].

Two main families:
- Top-down: recursive descent, LL parsers
- Bottom-up: LR family, used in tools like yacc/bison

Output of the parser is consumed by later phases of [[Compilers]] for semantic analysis and code generation.""",
    },
    {
        "title": "Lexical Analysis",
        "content": """Lexical analysis (lexing or tokenization) breaks the source character stream into tokens.

Tools and techniques:
- Regular expressions, finite automata
- Hand-written or generated (lex, flex)

Output feeds into [[Parsing]] which is the next phase of [[Compilers]]. Reuses ideas from [[Algorithms]] (state-machine simulation) and [[Data Structures|data structures]].""",
    },
    # --- Demo notes that exercise the markdown rendering features ---
    {
        "title": "Markdown Syntax",
        "content": """LinkNotes supports several inline syntaxes inside note content.

Wiki-style note links:
- [[Operating Systems]] - direct link
- [[Operating Systems|the OS note]] - link with a display alias

Embedded media (URL-based; the editor's Attach button can also upload local files):
- ![Random demo image](https://picsum.photos/seed/linknotes/600/360)
- ![Sample PDF (PPO paper, arXiv)](https://arxiv.org/pdf/1707.06347)

External links:
- [PageRank on Wikipedia](https://en.wikipedia.org/wiki/PageRank)
- [PostgreSQL full-text search docs](https://www.postgresql.org/docs/current/textsearch.html)

Useful when documenting bigger topics like [[Algorithms]] or [[Databases]].""",
    },
    {
        "title": "Resources",
        "content": """A collection of useful external references.

Foundational:
- [Donald Knuth's home page](https://www-cs-faculty.stanford.edu/~knuth/)
- [Computer Science topics on Wikipedia](https://en.wikipedia.org/wiki/Outline_of_computer_science)

Database-specific:
- [PostgreSQL documentation](https://www.postgresql.org/docs/)
- [Use The Index, Luke!](https://use-the-index-luke.com/)

Related notes: [[Databases]], [[Algorithms]], [[Operating Systems]].""",
    },
    {
        "title": "PageRank Visualization",
        "content": """The PageRank algorithm assigns each node an importance score derived from the structure of incoming links.

![PageRank graph (placeholder)](https://placehold.co/600x360/1a1a2e/ffffff?text=PageRank+graph+demo)

A canonical illustration would show a node with many incoming arrows from other already-important pages getting the highest rank. The placeholder above is just to verify image rendering - see the [interactive Wikipedia diagram](https://en.wikipedia.org/wiki/PageRank#/media/File:PageRanks-Example.svg) for the real thing.

LinkNotes uses the same idea over the [[Databases|database]] of notes - see also [[Algorithms]] and the original [paper by Brin and Page](http://infolab.stanford.edu/~backrub/google.html).""",
    },
    # --- Intentional orphans (no incoming or outgoing links) for /api/orphans ---
    {
        "title": "Reading List",
        "content": """Books I want to read this semester. (This note is intentionally not connected to any other note - it should appear under Orphans.)

- "The Art of Computer Programming" - Knuth
- "Database System Concepts" - Silberschatz, Korth, Sudarshan
- "Designing Data-Intensive Applications" - Kleppmann

Find them at [Goodreads](https://www.goodreads.com/) or your local library.""",
    },
    {
        "title": "Scratch",
        "content": """Quick personal scratch space - todos, half-formed thoughts.

- Try the new pgvector extension
- Read up on DuckDB internals
- Refresh on relational algebra

(Orphan note - no wiki-links in or out.)""",
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
    refresh_rankings()
    print(f"Seeded {len(SAMPLE_NOTES)} notes with links. PageRank refreshed.")


if __name__ == "__main__":
    seed()
