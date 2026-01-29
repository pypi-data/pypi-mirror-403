"""
SQLite-based storage backend for stash.
Zero external dependencies - uses Python's built-in sqlite3.
"""

import sqlite3
import json
import os
from pathlib import Path
from datetime import datetime
from typing import Optional, List, Dict, Any, Tuple


def get_default_db_path() -> Path:
    """Get the default database path, respecting XDG conventions."""
    if xdg_data := os.environ.get("XDG_DATA_HOME"):
        base = Path(xdg_data)
    elif stash_home := os.environ.get("STASH_HOME"):
        return Path(stash_home) / "stash.db"
    else:
        base = Path.home() / ".local" / "share"
    
    stash_dir = base / "stash"
    stash_dir.mkdir(parents=True, exist_ok=True)
    return stash_dir / "stash.db"


class StashStore:
    """
    SQLite-backed key-value store with metadata and search.
    
    Stores both simple key-value pairs and large text contexts
    that can be searched and chunked.
    """
    
    def __init__(self, db_path: Optional[Path] = None):
        self.db_path = db_path or get_default_db_path()
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()
    
    def _init_db(self) -> None:
        """Initialize the database schema."""
        with sqlite3.connect(self.db_path) as conn:
            conn.executescript("""
                CREATE TABLE IF NOT EXISTS entries (
                    key TEXT PRIMARY KEY,
                    value TEXT NOT NULL,
                    entry_type TEXT DEFAULT 'kv',
                    metadata TEXT DEFAULT '{}',
                    created_at TEXT DEFAULT (datetime('now')),
                    updated_at TEXT DEFAULT (datetime('now')),
                    access_count INTEGER DEFAULT 0,
                    last_accessed_at TEXT
                );
                
                CREATE INDEX IF NOT EXISTS idx_entries_type ON entries(entry_type);
                CREATE INDEX IF NOT EXISTS idx_entries_created ON entries(created_at);
                
                -- Full-text search virtual table
                CREATE VIRTUAL TABLE IF NOT EXISTS entries_fts USING fts5(
                    key, value, content='entries', content_rowid='rowid'
                );
                
                -- Triggers to keep FTS in sync
                CREATE TRIGGER IF NOT EXISTS entries_ai AFTER INSERT ON entries BEGIN
                    INSERT INTO entries_fts(rowid, key, value) 
                    VALUES (new.rowid, new.key, new.value);
                END;
                
                CREATE TRIGGER IF NOT EXISTS entries_ad AFTER DELETE ON entries BEGIN
                    INSERT INTO entries_fts(entries_fts, rowid, key, value) 
                    VALUES('delete', old.rowid, old.key, old.value);
                END;
                
                CREATE TRIGGER IF NOT EXISTS entries_au AFTER UPDATE ON entries BEGIN
                    INSERT INTO entries_fts(entries_fts, rowid, key, value) 
                    VALUES('delete', old.rowid, old.key, old.value);
                    INSERT INTO entries_fts(rowid, key, value) 
                    VALUES (new.rowid, new.key, new.value);
                END;
            """)
    
    def set(self, key: str, value: str, entry_type: str = "kv", 
            metadata: Optional[Dict[str, Any]] = None) -> None:
        """Store a value with optional metadata."""
        meta_json = json.dumps(metadata or {})
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                INSERT INTO entries (key, value, entry_type, metadata, updated_at)
                VALUES (?, ?, ?, ?, datetime('now'))
                ON CONFLICT(key) DO UPDATE SET
                    value = excluded.value,
                    entry_type = excluded.entry_type,
                    metadata = excluded.metadata,
                    updated_at = datetime('now')
            """, (key, value, entry_type, meta_json))
    
    def get(self, key: str) -> Optional[str]:
        """Retrieve a value by key, updating access stats."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                UPDATE entries 
                SET access_count = access_count + 1,
                    last_accessed_at = datetime('now')
                WHERE key = ?
            """, (key,))
            
            cursor = conn.execute(
                "SELECT value FROM entries WHERE key = ?", (key,)
            )
            row = cursor.fetchone()
            return row[0] if row else None
    
    def get_with_metadata(self, key: str) -> Optional[Dict[str, Any]]:
        """Retrieve a value with all its metadata."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("""
                SELECT key, value, entry_type, metadata, 
                       created_at, updated_at, access_count
                FROM entries WHERE key = ?
            """, (key,))
            row = cursor.fetchone()
            if not row:
                return None
            
            return {
                "key": row[0],
                "value": row[1],
                "type": row[2],
                "metadata": json.loads(row[3]),
                "created_at": row[4],
                "updated_at": row[5],
                "access_count": row[6],
            }
    
    def delete(self, key: str) -> bool:
        """Delete an entry by key."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("DELETE FROM entries WHERE key = ?", (key,))
            return cursor.rowcount > 0
    
    def list(self, entry_type: Optional[str] = None, 
             limit: int = 100) -> List[Dict[str, Any]]:
        """List entries, optionally filtered by type."""
        with sqlite3.connect(self.db_path) as conn:
            if entry_type:
                cursor = conn.execute("""
                    SELECT key, entry_type, 
                           LENGTH(value) as size,
                           created_at, updated_at, access_count
                    FROM entries 
                    WHERE entry_type = ?
                    ORDER BY updated_at DESC
                    LIMIT ?
                """, (entry_type, limit))
            else:
                cursor = conn.execute("""
                    SELECT key, entry_type,
                           LENGTH(value) as size,
                           created_at, updated_at, access_count
                    FROM entries
                    ORDER BY updated_at DESC
                    LIMIT ?
                """, (limit,))
            
            return [
                {
                    "key": row[0],
                    "type": row[1],
                    "size": row[2],
                    "created_at": row[3],
                    "updated_at": row[4],
                    "access_count": row[5],
                }
                for row in cursor.fetchall()
            ]
    
    def search(self, pattern: str, limit: int = 50) -> List[Tuple[str, str]]:
        """
        Full-text search across all entries.
        Returns list of (key, snippet) tuples.
        """
        with sqlite3.connect(self.db_path) as conn:
            # Use FTS5 for fast full-text search
            cursor = conn.execute("""
                SELECT key, snippet(entries_fts, 1, '>>>', '<<<', '...', 32)
                FROM entries_fts
                WHERE entries_fts MATCH ?
                LIMIT ?
            """, (pattern, limit))
            return cursor.fetchall()
    
    def search_regex(self, pattern: str, key_filter: Optional[str] = None,
                     limit: int = 50) -> List[Dict[str, Any]]:
        """
        Search using regex pattern (slower but more flexible).
        """
        import re
        regex = re.compile(pattern, re.IGNORECASE)
        results = []
        
        with sqlite3.connect(self.db_path) as conn:
            if key_filter:
                cursor = conn.execute(
                    "SELECT key, value FROM entries WHERE key LIKE ?",
                    (f"%{key_filter}%",)
                )
            else:
                cursor = conn.execute("SELECT key, value FROM entries")
            
            for key, value in cursor:
                matches = list(regex.finditer(value))
                if matches:
                    # Get context around first match
                    match = matches[0]
                    start = max(0, match.start() - 50)
                    end = min(len(value), match.end() + 50)
                    snippet = value[start:end]
                    if start > 0:
                        snippet = "..." + snippet
                    if end < len(value):
                        snippet = snippet + "..."
                    
                    results.append({
                        "key": key,
                        "snippet": snippet,
                        "match_count": len(matches),
                        "first_match": match.group(),
                    })
                    
                    if len(results) >= limit:
                        break
        
        return results
    
    def stats(self) -> Dict[str, Any]:
        """Get storage statistics."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("""
                SELECT 
                    COUNT(*) as total_entries,
                    SUM(LENGTH(value)) as total_size,
                    COUNT(DISTINCT entry_type) as type_count
                FROM entries
            """)
            row = cursor.fetchone()
            
            cursor = conn.execute("""
                SELECT entry_type, COUNT(*) as count
                FROM entries
                GROUP BY entry_type
            """)
            by_type = {r[0]: r[1] for r in cursor.fetchall()}
            
            return {
                "total_entries": row[0] or 0,
                "total_size_bytes": row[1] or 0,
                "type_count": row[2] or 0,
                "by_type": by_type,
                "db_path": str(self.db_path),
            }
