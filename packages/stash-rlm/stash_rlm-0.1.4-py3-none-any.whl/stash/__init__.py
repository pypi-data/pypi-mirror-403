"""
stash - External memory for AI agents

A lightweight context and memory management tool for AI agents.
Like a mini-RLM (Recursive Language Model) that any Clawdbot can use.

Usage:
    stash set <key> <value>      Store a value
    stash get <key>              Retrieve a value
    stash load <file> --as <id>  Load file into context
    stash search <pattern>       Search across contexts
    stash peek <id> [range]      View slice of content
    stash list                   List all entries
    stash forget <key>           Delete an entry
"""

__version__ = "0.1.4"
__author__ = "Klod <klod@shannonlabs.dev>"

from .store import StashStore
from .context import ContextManager

__all__ = ["StashStore", "ContextManager", "__version__"]
