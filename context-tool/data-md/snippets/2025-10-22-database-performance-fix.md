---
type: snippet
date: 2025-10-22 16:45:00
source: debugging
tags: [bug, database, sqlite, threading, performance]
---

# Fixed SQLite Threading Issues

## Problem

Widget mode was experiencing empty database results when clipboard monitoring ran in a background thread. Each thread was creating new `:memory:` connections, resulting in isolated empty databases.

## Root Cause

SQLite's default `check_same_thread=True` prevents sharing connections across threads. Our monitoring thread couldn't access the main thread's database.

## Solution

Added `check_same_thread=False` to database connection:

```python
self.connection = sqlite3.connect(
    self.db_path,
    check_same_thread=False  # Allow cross-thread access
)
```

This is **safe** because:
- Background thread only performs READ operations (analyze)
- No writes happen in monitoring thread
- SQLite handles concurrent reads safely
- UI updates still happen in main thread via `root.after()`

## Performance Impact

- Fixed: 0% match rate → 95%+ match rate
- No performance degradation
- Thread-safe for our use case

## Related

- [[John Chen]] - Helped debug the issue
- [[Context Tool]] - Project affected
- See: `BUGFIX_WIDGET_MATCHING.md` for full writeup
