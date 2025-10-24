# Threading Fix: SQLite Cross-Thread Access

## Problem

Widget mode crashed with:
```
sqlite3.ProgrammingError: SQLite objects created in a thread can only be used in that same thread.
The object was created in thread id 126475379241088 and this is thread id 126475328571072.
```

This happened when the clipboard monitoring thread tried to use the analyzer (which contains a database connection) created in the main thread.

## Root Cause

SQLite has a safety feature called `check_same_thread` that **by default** prevents connections from being used across threads. This is to prevent accidental misuse that could cause corruption.

```python
# Default behavior
connection = sqlite3.connect(':memory:')  # check_same_thread=True (default)

# Main thread: OK
connection.execute("SELECT * FROM table")

# Different thread: ERROR!
connection.execute("SELECT * FROM table")  # ProgrammingError!
```

## The Solution

Added `check_same_thread=False` to the database connection:

### File: `src/database.py`

```python
def connect(self) -> sqlite3.Connection:
    """
    Connect to database and enable row factory

    Uses check_same_thread=False to allow connection sharing across threads.
    This is safe for read-only operations (like analysis in monitoring threads).
    """
    self.connection = sqlite3.connect(
        self.db_path,
        check_same_thread=False  # ← THE FIX!
    )
    self.connection.row_factory = sqlite3.Row
    return self.connection
```

## Why This Is Safe

✅ **Our use case is READ-ONLY in background threads:**

1. **Main thread** - Creates database and loads data
2. **Monitoring thread** - Only READS via `analyzer.analyze()`
   - No INSERT, UPDATE, or DELETE operations
   - SQLite handles concurrent reads perfectly

3. **Writes only in main thread** - Saves happen via GUI callbacks in main thread

## The Pattern

```python
# Main thread: Initialize once
self.db = get_database(db_path)  # Uses check_same_thread=False
self.analyzer = ContextAnalyzer(self.db.connection, ...)

# Monitoring thread (background): Read-only
def check_clipboard(self):
    # Safe: Only reading via analyze()
    result = self.analyzer.analyze(text)

    # UI update back in main thread
    self.widget.root.after(0, lambda: self.widget.show(result))
```

## When NOT to Use check_same_thread=False

❌ **Don't use it if you write from multiple threads:**

```python
# BAD: Writing from background thread (RACE CONDITIONS!)
def background_thread():
    db.execute("INSERT INTO ...")  # NOT SAFE!
```

Instead, use:
1. **Queue pattern** - Send writes to main thread via queue
2. **Thread-local connections** - Each thread gets own connection (file-based DB)

## Testing

Created `tests/test_threading.py` to verify:

```bash
./venv/bin/python3 tests/test_threading.py
```

Tests:
- ✅ Cross-thread reads work
- ✅ Concurrent reads from multiple threads work
- ✅ No ProgrammingError exceptions
- ✅ Correct results returned

## Files Changed

1. **src/database.py** - Added `check_same_thread=False`
2. **src/widget_mode.py** - Added explanatory comments
3. **CLAUDE.md** - Comprehensive threading documentation
4. **tests/test_threading.py** - Threading tests

## Documentation

See `CLAUDE.md` → "SQLite Threading Best Practices" section for:
- Detailed explanation
- When it's safe vs unsafe
- Alternative patterns for writes
- What NOT to do

## Summary

| Before | After |
|--------|-------|
| ❌ ProgrammingError in monitoring thread | ✅ Reads work from any thread |
| ❌ Widget mode crashed on clipboard change | ✅ Widget mode works perfectly |
| ❌ Unclear threading rules | ✅ Documented best practices |

**Bottom line:**
- `check_same_thread=False` allows cross-thread **reads** (safe)
- Monitoring thread only reads (analyze), never writes
- All tests pass ✅
