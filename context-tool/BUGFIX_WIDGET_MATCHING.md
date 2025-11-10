# Bug Fix: Widget Mode Not Finding Matches

## Problem

Widget mode wasn't finding any matches for abbreviations (like "llm", "api") or contacts (like "Magnus"), even though the web mode worked perfectly.

## Root Cause

The clipboard monitoring thread in widget mode was creating a **new database connection** on each check:

```python
# OLD CODE (BROKEN)
thread_db = get_database(self.db_path).connection  # Creates NEW connection!
thread_analyzer = ContextAnalyzer(db=thread_db, ...)
```

When using `:memory:` database (the default), each new connection creates a **completely separate, empty database** with no data loaded!

### Why Web Mode Worked

Web mode uses a **global `analyzer`** variable that's initialized once and reused for all requests. All requests share the same database connection with all the loaded data.

### Why Widget Mode Didn't Work

Widget mode created a new analyzer with a new database connection in the monitoring thread:
- Main thread: Load data → Database has 4 abbreviations, 2 people
- Monitoring thread: New connection → **Empty database** → No matches found!

## Solution

**Reuse the same analyzer** (and thus same database connection) in the monitoring thread:

```python
# NEW CODE (FIXED)
# Use self.analyzer from main thread - shares same database connection!
result = self.analyzer.analyze(current_clipboard.strip())
```

This is safe because:
- SQLite connections are thread-safe for concurrent reads
- The monitoring thread only reads (analyzing), never writes
- Same pattern as web mode (shared analyzer)

## Changed File

`src/widget_mode.py` - Method `check_clipboard()` (lines 118-138)

**Before:**
```python
def check_clipboard(self):
    import pyperclip
    import sqlite3

    # Create thread-local database connection
    thread_db = get_database(self.db_path).connection  # NEW EMPTY DB!
    thread_analyzer = ContextAnalyzer(
        db=thread_db,
        pattern_matcher=self.analyzer.pattern_matcher,
        action_suggester=self.analyzer.action_suggester,
        semantic_searcher=None
    )

    # ... clipboard check ...
    result = thread_analyzer.analyze(text)  # NO DATA!
```

**After:**
```python
def check_clipboard(self):
    import pyperclip

    # ... clipboard check ...

    # Use SHARED analyzer (same database connection!)
    result = self.analyzer.analyze(text)  # HAS DATA!
```

## Test Results

Created `test_widget_analyzer.py` to verify the fix:

```
Testing 'llm':
   ✓ FOUND: LLM = Large Language Model

Testing 'api':
   ✓ FOUND: API = Application Programming Interface

Testing 'Magnus':
   ✓ FOUND: Magnus Sjostrand

OLD WAY: Thread DB has 0 abbreviations (EMPTY!)
NEW WAY: ✓ FOUND: LLM (Fixed!)
```

## Verification

To test widget mode now works:

```bash
./venv/bin/python3 main.py --mode widget --markdown
# Optional: add --local-semantic to enable embeddings.
```

Then copy:
- `llm` → Should show "LLM = Large Language Model"
- `api` → Should show "API = Application Programming Interface"
- `Magnus` → Should show contact details

## Related Issues

This bug only affected:
- `:memory:` database mode (default)
- Widget mode with clipboard monitoring
- Any threaded access that created new connections

This bug did NOT affect:
- Web mode (uses global analyzer)
- File-based database (same file = shared data across connections)
- Direct analyzer.analyze() calls in main thread

## Prevention

For future multi-threaded database access:
1. ✅ **Reuse connections** - Share analyzer/connection across threads
2. ✅ **Use file-based DB** - If you must create multiple connections
3. ❌ **Don't create new `:memory:` connections** - Each one is empty!

## Lesson Learned

**SQLite `:memory:` databases are per-connection, not per-process!**

Each connection to `:memory:` creates a completely independent database. To share data:
- Either use the same connection
- Or use a file-based database (even `file::memory:?cache=shared`)
