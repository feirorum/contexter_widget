# Claude Code Development Notes

## Running the Application

### Quick Start (Without Semantic Search)

```bash
# Install minimal dependencies
./venv/bin/pip install -r requirements-minimal.txt

# Run the application (must use venv python)
./venv/bin/python3 main.py --no-semantic
```

### With Semantic Search (Requires ~3GB download)

```bash
# Install all dependencies (includes PyTorch and sentence-transformers)
./venv/bin/pip install -r requirements.txt

# Run the application
./venv/bin/python3 main.py
```

## Access the Application

Once running, open your browser to: **http://localhost:8000**

## Command Line Options

```bash
./venv/bin/python3 main.py --help
./venv/bin/python3 main.py --no-semantic          # Skip semantic search (faster)
./venv/bin/python3 main.py --system-mode          # Enable system-wide clipboard monitoring
./venv/bin/python3 main.py --mode widget          # Desktop widget mode (NEW!)
./venv/bin/python3 main.py --port 8080            # Use different port
./venv/bin/python3 main.py --data-dir ./my-data   # Use custom data directory

# Combine flags
./venv/bin/python3 main.py --no-semantic --system-mode
./venv/bin/python3 main.py --no-semantic --mode widget
```

## System-Wide Monitoring Mode

When you enable `--system-mode`, the Context Tool will monitor your system clipboard:

1. Start the server with system mode:
   ```bash
   ./venv/bin/python3 main.py --no-semantic --system-mode
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
```

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
./venv/bin/python3 main.py --mode widget --no-semantic
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
1. Start widget mode: `./venv/bin/python3 main.py --mode widget --no-semantic`
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
# Use markdown data format
./venv/bin/python3 main.py --mode widget --no-semantic --markdown

# The --markdown flag automatically uses data-md/ directory
```

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

## Development Notes

- Must use `./venv/bin/python3` to access installed packages
- Semantic search requires large dependencies (PyTorch ~900MB, CUDA libraries ~2GB)
- For quick testing, use `--no-semantic` flag
- The minimal requirements file skips heavy ML dependencies
- Widget mode requires `tkinter` (usually included with Python) and `pyperclip`
- Both YAML (`data/`) and Markdown (`data-md/`) formats are supported
