# Person Name Matching Fix

## Problem

Person names weren't matching when the name in the markdown header differed from the filename.

**Example:**
- File: `data-md/people/magnus-sjostrand.md`
- Header: `# Stefan Krona`
- No `name` field in frontmatter

Searching for "Stefan Krona" resulted in no matches because the loader was only checking:
1. Frontmatter `name` field (not present)
2. Filename fallback (would be "Magnus Sjostrand")

## Root Cause

The `MarkdownDataLoader._load_people()` method wasn't extracting names from markdown headers.

### Original Code Flow (src/data_loaders/markdown_data_loader.py):

```python
# OLD (before fix):
name = frontmatter.get('name')
if not name:
    # Fallback to filename
    name = md_file.stem.replace('-', ' ').title()
```

This meant:
- ✅ If `name` in frontmatter → use it
- ❌ If no `name` in frontmatter → use filename (WRONG!)
- ❌ Never checked markdown header

## The Solution

Modified `_load_people()` to extract name from first markdown header (`# Name`).

### File: `src/data_loaders/markdown_data_loader.py` (lines 171-183)

```python
# Extract name: Priority order:
# 1. frontmatter 'name' field
# 2. First markdown header (# Name)
# 3. Filename as fallback
name = frontmatter.get('name')
if not name:
    # Try to extract from first header in markdown
    header_match = re.search(r'^#\s+(.+)$', body, re.MULTILINE)
    if header_match:
        name = header_match.group(1).strip()
    else:
        # Fallback to filename
        name = md_file.stem.replace('-', ' ').title()
```

## Priority Order (After Fix)

1. **Frontmatter `name` field** (explicit)
2. **First markdown header** (`# Name`)
3. **Filename** (fallback only)

This matches Obsidian-style workflow where:
- Header contains the canonical name
- Filename is just for file organization
- Frontmatter is optional metadata

## Example

### File: `data-md/people/magnus-sjostrand.md`

```markdown
---
type: person
tags:
  - contact
  - developer
interests:
  - LLM
  - Linux
---

# Stefan Krona

Developer working on TerminAI...
```

### What Gets Loaded:

- ✅ Name: "Stefan Krona" (from `# Stefan Krona` header)
- ✅ Tags: `["contact", "developer"]`
- ✅ Interests: `["LLM", "Linux"]`

### What Matches:

- ✅ "Stefan" → Stefan Krona
- ✅ "Krona" → Stefan Krona
- ✅ "Stefan Krona" → Stefan Krona
- ✅ "stefan" (case-insensitive) → Stefan Krona
- ❌ "magnus" → No match (correct! name is Stefan, not Magnus)

## Why This Structure Works

### Obsidian Compatibility

Obsidian users often have:
- **Filenames** for organization (e.g., `magnus-sjostrand.md`)
- **Headers** for display name (e.g., `# Stefan Krona`)
- **Frontmatter** for metadata only

This is common when:
- Renaming people (old filename, new header)
- Organizing by ID/slug (filename) but displaying real name (header)
- Migrating from other systems

### No Data Duplication

You don't need to duplicate the name in frontmatter:

```markdown
---
name: Stefan Krona  # ← Not needed!
---

# Stefan Krona  # ← This is enough
```

The loader reads from the header, which is:
- ✅ More visible (first thing you see)
- ✅ Matches Obsidian display
- ✅ Reduces duplication
- ✅ Single source of truth

## Demo vs Widget Mode

Both modes use identical matching logic:

1. **Both use** `MarkdownDataLoader` for loading
2. **Both use** `ContextAnalyzer` for matching
3. **Same database** connection and queries

Therefore:
- ✅ Demo mode: Stefan Krona matches
- ✅ Widget mode: Stefan Krona matches
- ✅ Web mode: Stefan Krona matches (if implemented)

All modes share the same code path → consistent behavior.

## Testing

Created comprehensive test: `tests/test_person_name_matching.py`

```bash
./venv/bin/python3 tests/test_person_name_matching.py
```

Tests verify:
- ✅ Names extracted from headers (not filenames)
- ✅ Partial name matching works
- ✅ Full name matching works
- ✅ Case-insensitive matching works
- ✅ Demo and widget modes use same logic

All tests pass ✓

## Files Changed

1. **src/data_loaders/markdown_data_loader.py** (lines 171-183)
   - Added regex to extract from first `# Header`
   - Updated priority order

2. **tests/test_person_name_matching.py** (NEW)
   - Comprehensive tests for name extraction and matching

3. **PERSON_NAME_MATCHING_FIX.md** (this file)
   - Documentation of the fix

## Summary

| Before | After |
|--------|-------|
| ❌ Stefan Krona doesn't match | ✅ Stefan Krona matches |
| ❌ Only checks frontmatter + filename | ✅ Checks frontmatter → header → filename |
| ❌ Requires name in frontmatter | ✅ Header is enough (Obsidian-style) |
| ❌ Data duplication needed | ✅ Single source of truth (header) |

**Bottom line:**
- Names extracted from markdown headers (primary method)
- Frontmatter `name` field optional (override only)
- Filename used as last resort fallback
- Obsidian-compatible workflow ✅
- All modes (demo, widget) work identically ✅
