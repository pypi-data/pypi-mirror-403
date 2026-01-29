# Review: stash

## Summary
The project is compact and readable, with a clear separation between storage, context handling, and the CLI. The main risks are around input validation (regex/FTS parsing, range parsing), edge cases in chunking and memory tagging, and the lack of safeguards if this CLI is embedded in a service that accepts untrusted inputs. The biggest correctness issue is the `chunk()` step calculation, which can raise errors when overlap is too large.

## Findings

### High
- `stash/context.py:166-205` — `chunk()` computes `step = chunk_size - overlap` without validation. If `overlap >= chunk_size`, `range(0, total, step)` raises `ValueError` (step 0) or produces empty output (negative step). Add guardrails for `chunk_size > 0`, `overlap >= 0`, and `overlap < chunk_size`.
- `stash/context.py:114-162` and `stash/store.py:193-232` — `re.compile()` is called on user input without handling `re.error`. Invalid patterns crash the CLI. Wrap regex compilation in `try/except` and return a friendly error message (or surface the exception in a controlled way).
- `stash/store.py:178-191` — FTS5 `MATCH` uses raw user input. Certain patterns raise `sqlite3.OperationalError` and can be used to craft expensive or overly broad queries. Consider escaping to a literal search mode or catching errors and reporting invalid FTS syntax.

### Medium
- `stash/cli.py:206-209` — `cmd_remember` uses `len(store.list(entry_type='memory')) + 1`, but `list()` defaults to 100 entries. After 100 memories or when entries are deleted, tags can collide and overwrite data. Use a dedicated counter (SQL `COUNT(*)`), UUID, or timestamp to generate keys.
- `stash/context.py:135-136` — `ContextManager.search()` only fetches 100 contexts, so searches silently ignore older contexts. Consider scanning all contexts or adding pagination.
- `stash/context.py:99-136` — `ContextManager.search()` calls `store.get()` for each context, which increments access counts and writes to the DB during search. This can skew metrics and slow down searches. Consider a read-only fetch for search/list operations.
- `stash/cli.py:72-81` — `cmd_peek` range parsing uses `int()` without error handling. Non-integer input crashes the command. Validate and return a friendly error.

### Low / Security Hardening
- `stash/context.py:20-47` — `load_file()` reads any local path without restriction. That’s fine for a user-run CLI, but if reused in a service, it becomes a path traversal vector. Consider an allowlist of directories or a “safe mode” flag for embedded use.
- `stash/store.py:41-81` — Data is stored in plaintext without any permission checks. If the tool is used for API keys, recommend documenting file permissions and optionally offering encryption-at-rest.

## Suggested Fixes (Shortlist)
- Add input validation for `chunk_size`/`overlap` in `ContextManager.chunk()`.
- Wrap regex compilation and FTS search in `try/except` blocks; surface user-friendly errors.
- Replace memory key generation with a stable unique scheme (UUID, timestamp, or SQL `COUNT(*)`).
- Remove the hard-coded `limit=100` when scanning contexts, or make it configurable.
- Add a read-only fetch method in `StashStore` (no access count updates) for search/list operations.
- Validate `peek` range arguments to avoid `ValueError` on bad input.

## Notes
- If the CLI is only ever used locally, the “path traversal” and plaintext storage notes are less critical. They become important if `stash` is embedded in services or invoked with untrusted inputs.
