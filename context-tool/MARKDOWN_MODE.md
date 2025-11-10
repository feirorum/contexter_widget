# Using Markdown Mode

## Quick Start

To use markdown data instead of YAML, add the `--markdown` flag:

```bash
# Web mode
./venv/bin/python3 main.py --markdown

# Widget mode (recommended for testing)
./venv/bin/python3 main.py --mode widget --markdown

# Enable embeddings (optional, slower startup)
# ./venv/bin/python3 main.py --markdown --local-semantic
```

When you use `--markdown`, the app automatically:
1. **Selects** `config-markdown.yaml` (if it exists)
2. **Uses** `data-md/` directory
3. **Saves** to `data-md/saves.log`

## What You Should See

When starting correctly in markdown mode, you'll see:

```
📄 Auto-selected markdown config: config-markdown.yaml

Starting Context Tool in widget mode...
📁 Data directory: data-md
📁 Data format: Markdown
💾 Database: :memory:
🔍 Semantic search: disabled
Initializing widget mode...
📁 Data format: Markdown
📁 Data directory: /path/to/context-tool/data-md
📁 Loading markdown files from: /path/to/context-tool/data-md

📊 Markdown Data Loaded:
  - 2 people
  - 1 snippets
  - 1 projects
  - 4 abbreviations
  - 14 relationships
  - Sample abbreviations: API, ASAP, JWT
  - Sample people: Magnus Sjostrand, Sarah Mitchell

💾 Saves will be logged to: /path/to/context-tool/data-md/saves.log
```

## Test Data Available

The `data-md/` directory includes:

### Abbreviations
- **LLM** - Large Language Model (ai-ml/llm.md)
- **API** - Application Programming Interface
- **JWT** - JSON Web Token
- **ASAP** - As Soon As Possible

### People
- **Magnus Sjöstrand** - Developer working on TerminAI
- **Sarah Mitchell** - Auth Team Lead

### Projects
- **Context Tool** - This project

## Testing

Copy any of these to test:
- `llm` → Should show "LLM = Large Language Model"
- `Magnus` → Should show contact details
- `API` → Should show "API = Application Programming Interface"

## Troubleshooting

### ❌ If you see YAML mode instead:

```
📁 Data format: YAML          ← Wrong!
📁 Data directory: .../data   ← Should be data-md
Loaded 133 abbreviations      ← Too many (YAML data)
```

**Solution**: Add the `--markdown` flag when starting

### ❌ If you see 0 items loaded:

```
📁 Data format: Markdown
📁 Data directory: .../data-md
⚠️  WARNING: Directory .../data-md does not exist!
```

**Solution**: The `data-md/` directory is missing. Check your working directory.

### ✅ Correct output:

```
📁 Data format: Markdown       ← Correct!
📁 Data directory: .../data-md ← Correct!
📊 Markdown Data Loaded:
  - 2 people                   ← Small numbers = markdown
  - 4 abbreviations
  - Sample abbreviations: API, ASAP, JWT  ← Shows what was loaded
  - Sample people: Magnus Sjostrand, ...  ← Shows Magnus
```

## Debug Script

If still having issues, run the debug script:

```bash
./venv/bin/python3 debug_markdown.py
```

This will show exactly what data is in the database and test matching.

## Run Tests

```bash
# Test markdown loading
./venv/bin/python3 tests/test_markdown_mode.py

# Test all functionality
./venv/bin/python3 tests/test_basic_functionality.py
```
