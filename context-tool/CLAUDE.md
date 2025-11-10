# Claude Code Development Notes

## Running the Application

### Quick Start (Semantic Search Disabled by Default)

```bash
# Install minimal dependencies
./venv/bin/pip install -r requirements-minimal.txt

# Run the application (must use venv python)
./venv/bin/python3 main.py

# Need embeddings? Add --local-semantic to enable them.
```

### With Semantic Search (Requires ~3GB download)

```bash
# Install all dependencies (includes PyTorch and sentence-transformers)
./venv/bin/pip install -r requirements.txt

# Run the application with semantic search enabled
./venv/bin/python3 main.py --local-semantic
```

## Access the Application

Once running, open your browser to: **http://localhost:8000**

## Command Line Options

```bash
./venv/bin/python3 main.py --help
./venv/bin/python3 main.py --local-semantic       # Enable semantic search (slower startup, downloads models)
./venv/bin/python3 main.py --system-mode          # Enable system-wide clipboard monitoring
./venv/bin/python3 main.py --mode widget          # Desktop widget mode (NEW!)
./venv/bin/python3 main.py --port 8080            # Use different port
./venv/bin/python3 main.py --data-dir ./my-data   # Use custom data directory

# Combine flags
./venv/bin/python3 main.py --local-semantic --system-mode
./venv/bin/python3 main.py --local-semantic --mode widget
```

## System-Wide Monitoring Mode

When you enable `--system-mode`, the Context Tool will monitor your system clipboard:

1. Start the server with system mode:
   ```bash
   ./venv/bin/python3 main.py --system-mode
   # Add --local-semantic if you need embeddings.
   ```

2. Open the web UI at http://localhost:8000

3. **Copy any text anywhere on your Windows system** (Ctrl+C or right-click copy)

4. The web UI will **automatically update** with analysis results in real-time!

### How it works:
- Monitors clipboard every 0.5 seconds
- Detects new copied text (minimum 3 characters)
- Analyzes it automatically using the Context Tool
- Broadcasts results to all connected browser tabs via WebSocket
- Works across Windows and WSL seamlessly

### Features:
- ✅ Real-time clipboard monitoring
- ✅ Automatic analysis of copied text
- ✅ WebSocket broadcasting to all clients
- ✅ Visual indicator showing "System Mode Active"
- ✅ Green "System Selection" badge for clipboard text
- ✅ Works with any Windows application (browser, notepad, VS Code, etc.)

## Testing

```bash
# Run verification tests
./venv/bin/python3 tests/test_basic_functionality.py

# Run semantic search tests (requires sentence-transformers)
./venv/bin/python3 tests/test_semantic_search.py

# Run all tests
for test in tests/test_basic_functionality.py tests/test_markdown_mode.py tests/test_config_markdown.py tests/test_data_loaders.py tests/test_person_name_matching.py tests/test_feature_parity.py tests/test_semantic_search.py
do
  echo "Testing: $test"
  ./venv/bin/python3 "$test" || exit 1
done
```

### Semantic Search Testing

The semantic search functionality has comprehensive test coverage:

- **Embedding Generation**: Tests 384-dimensional vector creation for contacts, snippets, and projects
- **Similarity Search**: Tests cosine similarity calculations and ranking
- **Threshold Filtering**: Tests configurable similarity thresholds (0.0-1.0)
- **Integration**: Tests semantic search integrated with context analyzer
- **Clipboard Scenarios**: Tests real-world use cases (authentication questions, performance issues, UI work)
- **Quality Checks**: Tests conceptual understanding (synonyms, related concepts)

**Example test results:**
- "user authentication" → Found JWT notes, Sarah (Auth Lead), OAuth project (score: 0.438)
- "database performance" → Found optimization notes, threading fixes
- "visual design" → Found React/UI content, Emma (Frontend Lead)

See `SEMANTIC_SEARCH_TESTING.md` for detailed results and `SEMANTIC_SEARCH.md` for full documentation.

## Smart Saver with Auto-Detection (NEW!)

The Context Tool now includes an intelligent saver that detects what you're copying and suggests appropriate save options!

### How It Works

When you click "💾 Save Snippet" (or press Ctrl+S), the smart saver:

1. **Analyzes the copied text** using regex patterns
2. **Detects entity type**:
   - **Person** (e.g., "John Doe", "sarah@example.com") - 2+ capitalized words or email
   - **Abbreviation** (e.g., "API", "JWT", "HTTP") - Uppercase acronym pattern
   - **Snippet** (default) - Any other text
3. **Shows a dialog** with save options ranked by confidence
4. **Saves as markdown** in the appropriate directory
5. **Logs the action** in `saves.log` with reasoning

### Detection Examples

```bash
# Copy "John Doe" → Suggests:
# [✓] 👤 Save as Person (90% - Found name pattern: 'John Doe')
# [ ] 📝 Save as Snippet

# Copy "sarah.m@company.com" → Suggests:
# [✓] 👤 Save as Person (95% - Email address detected)
# [ ] 📝 Save as Snippet

# Copy "API" → Suggests:
# [✓] 📖 Save as Abbreviation (80% - Uppercase acronym pattern)
# [ ] 📝 Save as Snippet

# Copy "Discussed auth with Sarah..." → Suggests:
# [✓] 📝 Save as Snippet (100% - No specific pattern detected)
```

### Save Dialog

Beautiful radio button dialog showing:
- Confidence percentage for each option
- Detection reason
- Save/Cancel buttons
- Keyboard shortcuts (Enter to save, Esc to cancel)

### Saved Files

All files saved in markdown format with frontmatter:

**Person** → `data-md/people/john-doe.md`:
```markdown
---
type: person
email: john@example.com
created: 2024-01-15 14:30:00
source: saved_from_clipboard
---

# John Doe

## Notes

[Original copied text]

## Related

- Add related items here
```

**Abbreviation** → `data-md/abbreviations/custom/api.md`:
```markdown
---
type: abbreviation
abbr: API
category: Custom
created: 2024-01-15 14:30:00
source: saved_from_clipboard
---

# API

## Definition

Add definition here.

## Usage

Add usage examples.
```

**Snippet** → `data-md/snippets/2024-01-15-discussed-auth.md`:
```markdown
---
type: snippet
date: 2024-01-15 14:30:00
source: clipboard
tags: []
---

# Saved Snippet - Discussed auth with Sarah

[Full text of your snippet]

## Related

- Add related items here
```

### Save Log

Every save is logged to `data-md/saves.log` (JSON lines format):

```json
{"timestamp": "2024-01-15 14:30:22", "type": "person", "file": "people/john-doe.md", "reason": "Email address detected: 'john@example.com'", "text_preview": "john@example.com John Doe..."}
{"timestamp": "2024-01-15 14:32:15", "type": "snippet", "file": "snippets/2024-01-15-discussed.md", "reason": "Default save as snippet", "text_preview": "Discussed auth implementation..."}
```

This log tracks:
- When you saved
- What type was chosen
- Where it was saved
- Why that type was detected
- Preview of the text

Perfect for:
- Reviewing your save history
- Understanding the detection logic
- Auditing what was saved
- Machine learning on your patterns

## Desktop Widget Mode (NEW!)

The widget mode provides a native desktop UI with clipboard monitoring:

```bash
./venv/bin/python3 main.py --mode widget
# Optional: add --local-semantic to enable embeddings.
```

### Features:
- 🖥️ **Native Desktop UI** - Tkinter-based window (cross-platform)
- ⌨️ **Keyboard Navigation** - Use ↑↓ arrows to navigate matches, Enter to select
- 📋 **Clipboard Monitoring** - Automatically analyzes copied text
- 🎨 **Two-Pane Layout**:
  - **Left pane**: Compact list of matches (abbreviations, contacts, snippets, projects)
  - **Right pane**: Detailed view of selected match
- 🔧 **Quick Actions**:
  - 🔍 Search Web (Ctrl+W) - Opens Google search with selected text
  - 💾 Save Snippet (Ctrl+S) - Saves current text as snippet
  - 📋 Copy (Ctrl+C) - Copies selected text to clipboard
- 🎯 **Smart Text Truncation** - Long text is truncated to 30-40 chars in list view
- 🔝 **Always on Top** - Widget stays on top of other windows

### How it works:
1. Start widget mode: `./venv/bin/python3 main.py --mode widget` (add `--local-semantic` if needed)
2. A desktop window appears (initially empty)
3. **Copy any text anywhere** on your system (Ctrl+C)
4. Widget instantly shows:
   - Truncated selected text in header
   - List of matches (abbreviations, contacts, etc.)
   - Detailed view on the right
5. Use keyboard or mouse to navigate:
   - **↑↓** - Navigate through matches
   - **Enter** - Refresh details
   - **Esc** - Close widget
6. Click action buttons or use shortcuts

### Example Use Cases:
- Copy "API" → See full explanation: "Application Programming Interface"
- Copy "sarah.m@company.com" → See contact details, last meeting notes
- Copy a snippet you saved → See related projects and contacts
- Copy any abbreviation → Get instant definition with examples and links

## Markdown Data Format (NEW!)

The Context Tool now supports **Obsidian-compatible markdown files** as an alternative to YAML!

### Using Markdown Files

```bash
# Use markdown data format (automatically uses config-markdown.yaml)
./venv/bin/python3 main.py --mode widget --markdown

# Enable semantic search in markdown mode (optional, slower)
# ./venv/bin/python3 main.py --mode widget --markdown --local-semantic

# The --markdown flag automatically:
# 1. Selects config-markdown.yaml (if exists)
# 2. Uses data-md/ directory
# 3. Saves to data-md/saves.log
```

### Configuration Files

- **config.yaml** - Default config for YAML mode (uses `data/` directory)
- **config-markdown.yaml** - Config for Markdown mode (uses `data-md/` directory)

When you use `--markdown` flag, the app automatically selects `config-markdown.yaml`.

### Why Markdown?

- ✅ **Human-readable** - Edit in any text editor or Obsidian
- ✅ **Obsidian compatible** - Works with Obsidian vaults, wikilinks, graph view
- ✅ **Version control friendly** - Great for git
- ✅ **Searchable** - Easy to grep and find things
- ✅ **Rich formatting** - Headers, lists, code blocks, tables
- ✅ **Wikilinks** - `[[Name]]` creates relationships automatically

### Directory Structure

```
data-md/
├── people/              # firstname-lastname.md
├── snippets/            # YYYY-MM-DD-title.md
├── projects/            # project-name.md
└── abbreviations/       # Organized by category
    ├── tech/
    ├── business/
    ├── ai-ml/
    └── security/
```

### Example Person File

```markdown
---
type: person
email: sarah.m@company.com
role: Auth Team Lead
tags: [teammate, auth, technical-lead]
expertise: [OAuth, JWT, mobile auth]
last_contact: 3 days ago via Slack about JT-344
next_event: Meeting tomorrow 2pm
---

# Sarah Mitchell

Auth Team Lead responsible for authentication infrastructure.

## Current Work

Working on JT-344 authentication feature. Leading JWT migration.

## Related

- [[Context Tool]] - Current project
- [[OAuth]] - Primary expertise
```

### Example Abbreviation File

```markdown
---
type: abbreviation
abbr: JWT
category: Security
related: ["[[OAuth]]", "[[Auth]]", "[[API]]"]
links:
  - https://jwt.io
---

# JWT - JSON Web Token

A compact, URL-safe means of representing claims between parties.

## Structure

A JWT consists of three parts: header.payload.signature

## Security Best Practices

- Use short expiration times (15 min)
- Use RS256 for production
- Store in httpOnly cookies

## Related

- [[OAuth]] - Uses JWT tokens
- [[Sarah Mitchell]] - Working on JWT implementation
```

### Wikilinks Create Relationships

When you write `[[Sarah Mitchell]]` or `[[OAuth]]` in your markdown files:
1. Context Tool parses all wikilinks
2. Creates relationships in the knowledge graph
3. Shows related items when you search

### Edit with Obsidian

1. Open `data-md/` folder as an Obsidian vault
2. Edit files with rich markdown editor
3. Click wikilinks to navigate
4. View graph view to see connections
5. Changes are instantly available in Context Tool

See `data-md/README.md` for detailed format documentation and examples.

### Person Name Extraction (Important!)

The markdown loader extracts person names using this **priority order**:

1. **Frontmatter `name` field** (explicit override)
2. **First markdown header** (`# Name`) - PRIMARY METHOD
3. **Filename** (last resort fallback)

This is Obsidian-compatible! You don't need to duplicate the name in frontmatter:

```markdown
---
type: person
email: stefan@example.com
# NO 'name' field needed!
---

# Stefan Krona  ← This is enough!

Developer working on TerminAI...
```

**Why this works:**
- ✅ Filename can be for organization (e.g., `magnus-sjostrand.md`)
- ✅ Header shows the canonical name (e.g., `# Stefan Krona`)
- ✅ No data duplication required
- ✅ Single source of truth (the header)
- ✅ Obsidian displays the header as the note title

**Matching:**
- "Stefan" → Finds Stefan Krona ✓
- "Krona" → Finds Stefan Krona ✓
- "Stefan Krona" → Finds Stefan Krona ✓
- "magnus" → No match ✓ (name is Stefan, not Magnus)

See `PERSON_NAME_MATCHING_FIX.md` for details.

## Development Notes

- Must use `./venv/bin/python3` to access installed packages
- Semantic search requires large dependencies (PyTorch ~900MB, CUDA libraries ~2GB)
- For quick testing, just skip `--local-semantic` (semantic search stays disabled)
- The minimal requirements file skips heavy ML dependencies
- Widget mode requires `tkinter` (usually included with Python) and `pyperclip`
- Both YAML (`data/`) and Markdown (`data-md/`) formats are supported

## Code Organization

### Data Loaders (Refactored)

All data loaders are now in `src/data_loaders/`:

```python
from src.data_loaders import load_data

# Load YAML data
load_data(db, Path('./data'), format='yaml')

# Load Markdown data
load_data(db, Path('./data-md'), format='markdown')
```

Classes:
- `YAMLDataLoader` - Loads YAML files from `data/`
- `MarkdownDataLoader` - Loads Markdown files from `data-md/`

See `REFACTORING.md` for details on the refactoring.

### Bug Fixes

**Widget Mode Matching Issue (FIXED)** - Widget mode clipboard monitoring was creating new database connections, resulting in empty `:memory:` databases with no data. Now reuses the same analyzer for all threads. See `BUGFIX_WIDGET_MATCHING.md` for details.

### SQLite Threading Best Practices

**IMPORTANT:** SQLite has threading restrictions that must be handled properly.

#### The Problem

By default, SQLite doesn't allow using connections across threads:
```python
# Main thread
db = get_database(':memory:')
analyzer = ContextAnalyzer(db.connection, ...)

# Monitoring thread (WILL FAIL!)
result = analyzer.analyze(text)  # Error: SQLite objects created in a thread...
```

#### The Solution

We use `check_same_thread=False` in the database connection:

```python
# src/database.py
self.connection = sqlite3.connect(
    self.db_path,
    check_same_thread=False  # Allow cross-thread access
)
```

#### When This Is Safe

✅ **READ-ONLY operations from background threads**
- Widget mode monitoring thread only reads (analyze)
- No writes happen in background threads
- SQLite handles concurrent reads safely

❌ **NOT safe for writes from multiple threads**
- Don't write to database from background threads
- Use a queue or main thread for writes

#### Pattern Used in Widget Mode

```python
# Main thread: Initialize once
self.db = get_database(db_path)  # Uses check_same_thread=False
self.analyzer = ContextAnalyzer(self.db, ...)

# Monitoring thread: Read-only operations
def check_clipboard(self):
    # Safe: Only reading via analyze()
    result = self.analyzer.analyze(text)

    # Safe: UI update via main thread
    self.widget.root.after(0, lambda: self.widget.show(result))
```

#### Alternative Approaches

If you need writes from threads:

1. **Thread-local connections** (each thread gets own connection)
   - Use file-based DB: `context.db`
   - Each thread creates its own connection
   - Handles concurrent writes with locking

2. **Queue pattern** (recommended for writes)
   ```python
   # Background thread
   write_queue.put(('save_snippet', text))

   # Main thread
   while True:
       operation, data = write_queue.get()
       db.execute(...)  # Write in main thread
   ```

#### What NOT to Do

❌ **Don't create new `:memory:` connections in threads**
```python
# Each :memory: connection is a separate empty database!
thread_db = sqlite3.connect(':memory:')  # EMPTY DB!
```

❌ **Don't write from multiple threads without locking**
```python
# Background thread writing directly (NOT SAFE)
db.execute("INSERT INTO ...")  # Race conditions!
```

#### Summary

- ✅ `check_same_thread=False` for cross-thread reads
- ✅ Widget monitoring thread only reads (analyze)
- ✅ UI updates via `root.after()` in main thread
- ❌ No writes from background threads
- ❌ No new `:memory:` connections in threads
