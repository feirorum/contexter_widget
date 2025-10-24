# Quick Start: Markdown Mode

## TL;DR

```bash
./venv/bin/python3 main.py --mode widget --markdown --no-semantic
```

That's it! The app will automatically:
- ✅ Use `config-markdown.yaml`
- ✅ Load data from `data-md/`
- ✅ Save to `data-md/saves.log`

## What You'll See

```
📄 Auto-selected markdown config: config-markdown.yaml

Starting Context Tool in widget mode...
📁 Data directory: data-md
📁 Data format: Markdown
💾 Database: :memory:
🔍 Semantic search: disabled

📊 Markdown Data Loaded:
  - 2 people
  - 4 abbreviations
  - Sample abbreviations: API, ASAP, JWT
  - Sample people: Magnus Sjostrand, Sarah Mitchell

💾 Saves will be logged to: /path/to/data-md/saves.log
```

## Test It

Copy any of these:
- **`llm`** → Should show "LLM = Large Language Model"
- **`Magnus`** → Should show contact details
- **`API`** → Should show "API = Application Programming Interface"

## Verify Setup

```bash
# Run all tests
./venv/bin/python3 tests/test_config_markdown.py
./venv/bin/python3 tests/test_markdown_mode.py

# Debug if needed
./venv/bin/python3 debug_markdown.py
```

## File Structure

```
context-tool/
├── config.yaml              # YAML mode config (uses data/)
├── config-markdown.yaml     # Markdown mode config (uses data-md/)
├── data/                    # YAML data files
│   ├── contacts.yaml
│   ├── abbreviations.yaml
│   └── ...
└── data-md/                 # Markdown data files
    ├── people/
    │   ├── magnus-sjostrand.md
    │   └── sarah-mitchell.md
    ├── abbreviations/
    │   └── ai-ml/
    │       └── llm.md
    └── saves.log           # ← Saves logged here
```

## Troubleshooting

### Not finding matches?

Check the startup output:
- ❌ `Data format: YAML` → You forgot `--markdown` flag
- ❌ `Data directory: data` → Should be `data-md`
- ✅ `Data format: Markdown` → Correct!
- ✅ `Sample abbreviations: API, ASAP, JWT` → Data loaded!

### Still stuck?

```bash
# See exactly what's loaded
./venv/bin/python3 debug_markdown.py
```
