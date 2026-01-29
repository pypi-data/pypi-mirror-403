#!/usr/bin/env python3
"""
stash - External memory for AI agents

A lightweight context and memory management CLI.
"""

import argparse
import sys
import json
from pathlib import Path
from typing import Optional

from .store import StashStore
from .context import ContextManager


def format_size(size_bytes: int) -> str:
    """Format bytes as human-readable size."""
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size_bytes < 1024:
            return f"{size_bytes:.1f}{unit}"
        size_bytes /= 1024
    return f"{size_bytes:.1f}TB"


def cmd_set(args, store: StashStore) -> int:
    """Store a key-value pair."""
    # If value is "-", read from stdin
    if args.value == "-":
        value = sys.stdin.read()
    else:
        value = args.value
    
    store.set(args.key, value, entry_type="kv")
    print(f"✓ Stored '{args.key}' ({format_size(len(value))})")
    return 0


def cmd_get(args, store: StashStore) -> int:
    """Retrieve a value by key."""
    value = store.get(args.key)
    if value is None:
        print(f"✗ Key not found: {args.key}", file=sys.stderr)
        return 1
    
    if args.json:
        print(json.dumps({"key": args.key, "value": value}))
    else:
        print(value)
    return 0


def cmd_load(args, store: StashStore) -> int:
    """Load a file into context."""
    ctx = ContextManager(store)
    
    try:
        result = ctx.load_file(args.file, args.context_id or Path(args.file).stem)
        print(f"✓ Loaded '{result['source_name']}' as '{result['context_id']}'")
        print(f"  {result['line_count']} lines, {format_size(result['size_bytes'])}")
        return 0
    except FileNotFoundError as e:
        print(f"✗ {e}", file=sys.stderr)
        return 1


def cmd_peek(args, store: StashStore) -> int:
    """View a slice of a context."""
    ctx = ContextManager(store)
    
    # Parse range (e.g., "10:20" or "10")
    start, end = 0, None
    if args.range:
        if ':' in args.range:
            parts = args.range.split(':')
            start = int(parts[0]) if parts[0] else 0
            end = int(parts[1]) if parts[1] else None
        else:
            start = int(args.range)
            end = start + 20  # Default to 20 lines
    
    content = ctx.peek(args.context_id, start, end, unit=args.unit)
    if content is None:
        print(f"✗ Context not found: {args.context_id}", file=sys.stderr)
        return 1
    
    if args.numbered:
        lines = content.split('\n')
        for i, line in enumerate(lines, start=start + 1):
            print(f"{i:4}: {line}")
    else:
        print(content)
    return 0


def cmd_search(args, store: StashStore) -> int:
    """Search across entries."""
    if args.context:
        # Search within a specific context
        ctx = ContextManager(store)
        results = ctx.search(args.pattern, args.context, limit=args.limit)
        
        if not results:
            print("No matches found.")
            return 0
        
        for r in results:
            print(f"\n[{r['context_id']}:{r['line_number']}]")
            print(r['context'])
    else:
        # Search all entries with FTS
        if args.regex:
            results = store.search_regex(args.pattern, limit=args.limit)
            if not results:
                print("No matches found.")
                return 0
            
            for r in results:
                print(f"\n[{r['key']}] ({r['match_count']} matches)")
                print(f"  {r['snippet']}")
        else:
            results = store.search(args.pattern, limit=args.limit)
            if not results:
                print("No matches found.")
                return 0
            
            for key, snippet in results:
                print(f"\n[{key}]")
                print(f"  {snippet}")
    
    print(f"\n({len(results)} result{'s' if len(results) != 1 else ''})")
    return 0


def cmd_list(args, store: StashStore) -> int:
    """List all entries."""
    entries = store.list(entry_type=args.type, limit=args.limit)
    
    if not entries:
        print("No entries found.")
        return 0
    
    if args.json:
        print(json.dumps(entries, indent=2))
        return 0
    
    # Group by type for display
    by_type = {}
    for e in entries:
        t = e["type"]
        if t not in by_type:
            by_type[t] = []
        by_type[t].append(e)
    
    for entry_type, items in by_type.items():
        print(f"\n[{entry_type}]")
        for e in items:
            size = format_size(e["size"])
            key = e["key"]
            if entry_type == "context":
                key = key.replace("ctx:", "")
            print(f"  {key:<30} {size:>8}  (accessed {e['access_count']}x)")
    
    print(f"\n({len(entries)} entries)")
    return 0


def cmd_forget(args, store: StashStore) -> int:
    """Delete an entry."""
    # Try as regular key first
    if store.delete(args.key):
        print(f"✓ Forgot '{args.key}'")
        return 0
    
    # Try as context
    if store.delete(f"ctx:{args.key}"):
        print(f"✓ Forgot context '{args.key}'")
        return 0
    
    print(f"✗ Not found: {args.key}", file=sys.stderr)
    return 1


def cmd_stats(args, store: StashStore) -> int:
    """Show storage statistics."""
    stats = store.stats()
    
    if args.json:
        print(json.dumps(stats, indent=2))
        return 0
    
    print(f"Stash Statistics")
    print(f"─────────────────")
    print(f"Database: {stats['db_path']}")
    print(f"Total entries: {stats['total_entries']}")
    print(f"Total size: {format_size(stats['total_size_bytes'])}")
    print()
    print("By type:")
    for t, count in stats['by_type'].items():
        print(f"  {t}: {count}")
    
    return 0


def cmd_remember(args, store: StashStore) -> int:
    """Quick way to store a memory/note."""
    key = f"mem:{args.tag}" if args.tag else f"mem:{len(store.list(entry_type='memory')) + 1}"
    store.set(key, args.note, entry_type="memory")
    print(f"✓ Remembered: {args.note[:50]}{'...' if len(args.note) > 50 else ''}")
    return 0


def cmd_recall(args, store: StashStore) -> int:
    """Recall memories by tag or list all."""
    if args.tag:
        value = store.get(f"mem:{args.tag}")
        if value:
            print(value)
        else:
            # Try searching
            results = store.search_regex(args.tag, key_filter="mem:")
            if results:
                for r in results:
                    print(f"[{r['key']}] {r['snippet']}")
            else:
                print(f"No memories matching '{args.tag}'")
    else:
        entries = store.list(entry_type="memory")
        if not entries:
            print("No memories stored.")
            return 0
        
        for e in entries:
            value = store.get(e["key"])
            tag = e["key"].replace("mem:", "")
            preview = value[:60] + "..." if len(value) > 60 else value
            print(f"[{tag}] {preview}")
    
    return 0


def main():
    parser = argparse.ArgumentParser(
        prog="stash",
        description="External memory for AI agents - a mini RLM",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  stash set api:key "sk-12345"       Store a value
  stash get api:key                  Retrieve it
  stash load log.txt --as logs       Load file into context
  stash peek logs 0:50               View lines 0-50
  stash search "error" --in logs     Search in context
  stash remember "User likes JSON"   Store a quick memory
  stash recall                       List memories
  stash list                         List all entries
  stash forget logs                  Delete an entry
        """
    )
    parser.add_argument("--db", type=Path, help="Database path (default: ~/.local/share/stash/stash.db)")
    parser.add_argument("--json", action="store_true", help="Output as JSON where applicable")
    
    subparsers = parser.add_subparsers(dest="command", required=True)
    
    # set
    p_set = subparsers.add_parser("set", help="Store a key-value pair")
    p_set.add_argument("key", help="Key to store under")
    p_set.add_argument("value", help="Value to store (use '-' for stdin)")
    
    # get
    p_get = subparsers.add_parser("get", help="Retrieve a value")
    p_get.add_argument("key", help="Key to retrieve")
    p_get.add_argument("--json", action="store_true", help="Output as JSON")
    
    # load
    p_load = subparsers.add_parser("load", help="Load a file into context")
    p_load.add_argument("file", help="File to load")
    p_load.add_argument("--as", dest="context_id", help="Context ID (default: filename)")
    
    # peek
    p_peek = subparsers.add_parser("peek", help="View slice of a context")
    p_peek.add_argument("context_id", help="Context to peek into")
    p_peek.add_argument("range", nargs="?", help="Range (e.g., '10:20' or '10')")
    p_peek.add_argument("--unit", choices=["lines", "chars"], default="lines")
    p_peek.add_argument("-n", "--numbered", action="store_true", help="Show line numbers")
    
    # search
    p_search = subparsers.add_parser("search", help="Search entries")
    p_search.add_argument("pattern", help="Search pattern")
    p_search.add_argument("--in", dest="context", help="Search in specific context")
    p_search.add_argument("--regex", "-r", action="store_true", help="Use regex search")
    p_search.add_argument("--limit", "-l", type=int, default=20, help="Max results")
    
    # list
    p_list = subparsers.add_parser("list", aliases=["ls"], help="List entries")
    p_list.add_argument("--type", "-t", help="Filter by type")
    p_list.add_argument("--limit", "-l", type=int, default=50, help="Max entries")
    p_list.add_argument("--json", action="store_true", help="Output as JSON")
    
    # forget
    p_forget = subparsers.add_parser("forget", aliases=["rm"], help="Delete an entry")
    p_forget.add_argument("key", help="Key or context ID to delete")
    
    # stats
    p_stats = subparsers.add_parser("stats", help="Show storage statistics")
    p_stats.add_argument("--json", action="store_true", help="Output as JSON")
    
    # remember
    p_remember = subparsers.add_parser("remember", help="Store a quick memory")
    p_remember.add_argument("note", help="Note to remember")
    p_remember.add_argument("--tag", "-t", help="Tag for the memory")
    
    # recall
    p_recall = subparsers.add_parser("recall", help="Recall memories")
    p_recall.add_argument("tag", nargs="?", help="Tag or search term")
    
    args = parser.parse_args()
    
    # Initialize store
    store = StashStore(args.db)
    
    # Dispatch to command handler
    commands = {
        "set": cmd_set,
        "get": cmd_get,
        "load": cmd_load,
        "peek": cmd_peek,
        "search": cmd_search,
        "list": cmd_list,
        "ls": cmd_list,
        "forget": cmd_forget,
        "rm": cmd_forget,
        "stats": cmd_stats,
        "remember": cmd_remember,
        "recall": cmd_recall,
    }
    
    handler = commands.get(args.command)
    if handler:
        return handler(args, store)
    else:
        parser.print_help()
        return 1


if __name__ == "__main__":
    sys.exit(main())
