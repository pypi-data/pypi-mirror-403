"""
Context manager for handling large files and documents.
Provides chunking, peeking, and search within loaded contexts.
"""

import re
from pathlib import Path
from typing import Optional, List, Dict, Any, Tuple, Union


class ContextManager:
    """
    Manages large text contexts loaded from files.
    Provides efficient access without loading everything into memory.
    """
    
    def __init__(self, store: "StashStore"):
        self.store = store
    
    def load_file(self, path: Union[str, Path], context_id: str,
                  encoding: str = "utf-8") -> Dict[str, Any]:
        """
        Load a file into the stash as a context.
        
        Args:
            path: Path to the file
            context_id: ID to reference this context
            encoding: File encoding (default utf-8)
            
        Returns:
            Metadata about the loaded context
        """
        path = Path(path)
        if not path.exists():
            raise FileNotFoundError(f"File not found: {path}")
        
        content = path.read_text(encoding=encoding)
        lines = content.count('\n') + 1
        
        metadata = {
            "source_path": str(path.absolute()),
            "source_name": path.name,
            "size_bytes": len(content.encode(encoding)),
            "line_count": lines,
            "encoding": encoding,
        }
        
        self.store.set(
            key=f"ctx:{context_id}",
            value=content,
            entry_type="context",
            metadata=metadata
        )
        
        return {
            "context_id": context_id,
            "key": f"ctx:{context_id}",
            **metadata
        }
    
    def load_text(self, content: str, context_id: str,
                  source: str = "inline") -> Dict[str, Any]:
        """Load text directly into a context."""
        lines = content.count('\n') + 1
        
        metadata = {
            "source": source,
            "size_bytes": len(content.encode()),
            "line_count": lines,
        }
        
        self.store.set(
            key=f"ctx:{context_id}",
            value=content,
            entry_type="context",
            metadata=metadata
        )
        
        return {
            "context_id": context_id,
            "key": f"ctx:{context_id}",
            **metadata
        }
    
    def peek(self, context_id: str, start: int = 0, end: Optional[int] = None,
             unit: str = "lines") -> Optional[str]:
        """
        View a slice of a context.
        
        Args:
            context_id: Context to peek into
            start: Start position (0-indexed)
            end: End position (exclusive), None for rest
            unit: "lines" or "chars"
            
        Returns:
            The requested slice or None if context not found
        """
        content = self.store.get_raw(f"ctx:{context_id}")
        if content is None:
            return None
        
        if unit == "lines":
            lines = content.split('\n')
            if end is None:
                end = len(lines)
            selected = lines[start:end]
            return '\n'.join(selected)
        else:  # chars
            if end is None:
                end = len(content)
            return content[start:end]
    
    def search(self, pattern: str, context_id: Optional[str] = None,
               limit: int = 20, context_lines: int = 2) -> List[Dict[str, Any]]:
        """
        Search for a pattern within context(s).
        
        Args:
            pattern: Regex pattern to search for
            context_id: Specific context to search, or None for all
            limit: Max results to return
            context_lines: Lines of context around each match
            
        Returns:
            List of matches with context
        """
        results = []
        try:
            regex = re.compile(pattern, re.IGNORECASE)
        except re.error as exc:
            raise ValueError(f"Invalid regex pattern: {exc}") from exc
        
        # Get contexts to search
        if context_id:
            contexts = [(f"ctx:{context_id}", self.store.get_raw(f"ctx:{context_id}"))]
        else:
            entries = self.store.list(entry_type="context", limit=None)
            contexts = [(e["key"], self.store.get_raw(e["key"])) for e in entries]
        
        for key, content in contexts:
            if content is None:
                continue
            
            lines = content.split('\n')
            for i, line in enumerate(lines):
                if regex.search(line):
                    # Get context around match
                    start = max(0, i - context_lines)
                    end = min(len(lines), i + context_lines + 1)
                    
                    context_snippet = '\n'.join(
                        f"{'>' if j == i else ' '} {j+1}: {lines[j]}"
                        for j in range(start, end)
                    )
                    
                    results.append({
                        "context_id": key.replace("ctx:", ""),
                        "line_number": i + 1,
                        "line": line.strip(),
                        "context": context_snippet,
                    })
                    
                    if len(results) >= limit:
                        return results
        
        return results
    
    def chunk(self, context_id: str, chunk_size: int = 100,
              unit: str = "lines", overlap: int = 10) -> List[Dict[str, Any]]:
        """
        Split a context into overlapping chunks.
        
        Args:
            context_id: Context to chunk
            chunk_size: Size of each chunk
            unit: "lines" or "chars"
            overlap: Overlap between chunks
            
        Returns:
            List of chunks with metadata
        """
        content = self.store.get_raw(f"ctx:{context_id}")
        if content is None:
            return []
        
        if chunk_size <= 0:
            raise ValueError("chunk_size must be > 0")
        if overlap < 0:
            raise ValueError("overlap must be >= 0")
        if overlap >= chunk_size:
            raise ValueError("overlap must be smaller than chunk_size")

        chunks = []
        
        if unit == "lines":
            lines = content.split('\n')
            total = len(lines)
            step = chunk_size - overlap
            
            for i in range(0, total, step):
                chunk_lines = lines[i:i + chunk_size]
                chunks.append({
                    "chunk_index": len(chunks),
                    "start_line": i + 1,
                    "end_line": min(i + chunk_size, total),
                    "content": '\n'.join(chunk_lines),
                    "size": len(chunk_lines),
                })
        else:
            total = len(content)
            step = chunk_size - overlap
            
            for i in range(0, total, step):
                chunk_content = content[i:i + chunk_size]
                chunks.append({
                    "chunk_index": len(chunks),
                    "start_char": i,
                    "end_char": min(i + chunk_size, total),
                    "content": chunk_content,
                    "size": len(chunk_content),
                })
        
        return chunks
    
    def info(self, context_id: str) -> Optional[Dict[str, Any]]:
        """Get information about a context."""
        data = self.store.get_with_metadata(f"ctx:{context_id}")
        if data is None:
            return None
        
        return {
            "context_id": context_id,
            "type": data["type"],
            "metadata": data["metadata"],
            "created_at": data["created_at"],
            "updated_at": data["updated_at"],
            "access_count": data["access_count"],
        }
    
    def list_contexts(self) -> List[Dict[str, Any]]:
        """List all loaded contexts."""
        entries = self.store.list(entry_type="context", limit=None)
        return [
            {
                "context_id": e["key"].replace("ctx:", ""),
                "size": e["size"],
                "created_at": e["created_at"],
                "access_count": e["access_count"],
            }
            for e in entries
        ]
    
    def forget(self, context_id: str) -> bool:
        """Remove a context from the stash."""
        return self.store.delete(f"ctx:{context_id}")
