"""This module provides a database interface for storing and retrieving."""
import os  # noqa: F401
import sqlite3
import uuid
from datetime import datetime

import chromadb
from chromadb.utils import embedding_functions

# Configuration
SQLITE_DB_PATH = "eternity.db"
CHROMA_DB_PATH = "chroma_db"

# Initialize ChromaDB
chroma_client = chromadb.PersistentClient(path=CHROMA_DB_PATH)
# Use default Sentence Transformer embedding
sentence_transformer_ef = embedding_functions.\
    SentenceTransformerEmbeddingFunction(model_name="all-MiniLM-L6-v2")
collection = chroma_client.\
    get_or_create_collection(name="memories",
    embedding_function=sentence_transformer_ef)

def init_db():
    """Initialize SQLite database."""
    conn = sqlite3.connect(SQLITE_DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS memories (
            id TEXT PRIMARY KEY,
            content TEXT,
            tags TEXT,
            file_path TEXT,
            file_type TEXT,
            created_at TEXT
        )
    ''')
    conn.commit()
    conn.close()

def add_memory(content: str, tags: list[str],
               file_path: str = None, file_type: str = None) -> str:
    """Add a memory to both SQLite and ChromaDB."""
    memory_id = str(uuid.uuid4())
    timestamp = datetime.now().isoformat()
    tags_str = ",".join(tags)

    # Add to SQLite
    conn = sqlite3.connect(SQLITE_DB_PATH)
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO memories (id, content, tags, "
        "file_path, file_type, created_at) VALUES (?, ?, ?, ?, ?, ?)",
        (memory_id, content, tags_str, file_path, file_type, timestamp)
    )
    conn.commit()
    conn.close()

    # Add to ChromaDB
    collection.add(
        documents=[content],
        metadatas=[{"tags": tags_str, "created_at": timestamp}],
        ids=[memory_id]
    )

    return memory_id

def search_memories(query_text: str, n_results: int = 5):
    """Search memories using Vector Search."""
    results = collection.query(
        query_texts=[query_text],
        n_results=n_results
    )

    # Process results
    # Chroma returns lists of lists (one list per query)
    processed_results = []
    if results["ids"]:
        ids = results["ids"][0]
        distances = results["distances"][0]\
            if results["distances"] else [0.0] * len(ids)
        metadatas = results["metadatas"][0]
        documents = results["documents"][0]

        for i, memory_id in enumerate(ids):
            processed_results.append({
                "id": memory_id,
                "content": documents[i],
                "tags": metadatas[i].get("tags", "").\
                    split(",") if metadatas[i].get("tags") else [],
                "created_at": metadatas[i].get("created_at", ""),
                "distance": distances[i]
            })

    return processed_results

def get_all_memories(limit: int = 100):
    """Retrieve recent memories from SQLite."""
    conn = sqlite3.connect(SQLITE_DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM memories "
        "ORDER BY created_at DESC LIMIT ?", (limit,))
    rows = cursor.fetchall()
    conn.close()
    memories = []
    for row in rows:
        memories.append({
            "id": row["id"],
            "content": row["content"],
            "tags": row["tags"].split(",") if row["tags"] else [],
            "file_path": row["file_path"],
            "file_type": row["file_type"],
            "created_at": row["created_at"]
        })
    return memories
