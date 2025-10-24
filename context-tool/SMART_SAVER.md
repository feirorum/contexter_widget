# Smart Saver - Auto-Detection & Intelligent Saving

The Smart Saver automatically detects what type of entity you're copying and suggests the most appropriate save format.

## Overview

```
┌─────────────────┐
│  Copy Text      │
│  "John Doe"     │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Entity Detector │ ◄─── Regex patterns
│                 │      - Person names
│  - Person: 90%  │      - Email addresses
│  - Snippet: 50% │      - Abbreviations
└────────┬────────┘      - Projects
         │
         ▼
┌─────────────────┐
│ Choice Dialog   │
│                 │
│ ○ 👤 Person 90% │ ◄─── User selects
│ ○ 📝 Snippet 50%│
│                 │
│ [Save] [Cancel] │
└────────┬────────┘
         │
         ▼
┌──────────────────┐
│ Markdown Writer  │
│                  │
│ Saves to:        │
│ people/          │ ◄─── With frontmatter
│ john-doe.md      │      and body content
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│ Save Log         │
│                  │
│ JSON line added  │ ◄─── Tracks decision
│ with reasoning   │      and metadata
└──────────────────┘
```

## Detection Rules

### Person Detection (Confidence: 60-95%)

**Pattern 1: Name Pattern** (90% if full match, 60% if partial)
- Regex: `\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)+\b`
- Matches: "John Doe", "Sarah Mitchell", "Dr. Jane Smith"
- Requires: 2+ capitalized words

**Pattern 2: Email Address** (95%)
- Regex: `\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b`
- Matches: "john@example.com", "sarah.m@company.com"

### Abbreviation Detection (Confidence: 80%)

**Pattern 1: Uppercase Acronym**
- Regex: `^[A-Z]{2,6}[0-9]*$`
- Matches: "API", "JWT", "HTTP", "K8s"
- Length: 2-6 uppercase letters

**Pattern 2: Dotted Acronym**
- Regex: `^([A-Z]\.){2,}$`
- Matches: "U.S.A.", "Ph.D."

### Snippet (Default - Confidence: 50-100%)

**Always available** as fallback option
- Used when no specific pattern detected
- Confidence 100% if nothing else matches
- Confidence 50% when other patterns detected

## Save Locations

```
data-md/
├── people/
│   ├── john-doe.md
│   ├── sarah-mitchell.md
│   └── magnus-sjostrand.md
│
├── snippets/
│   ├── 2024-01-15-discussed-auth.md
│   ├── 2024-01-15-meeting-notes.md
│   └── 2024-01-16-idea-for-feature.md
│
├── abbreviations/
│   └── custom/
│       ├── api.md
│       ├── jwt.md
│       └── llm.md
│
├── projects/
│   ├── context-tool.md
│   └── new-project.md
│
└── saves.log  ← Tracks all save actions
```

## File Naming Convention

### People
- Format: `firstname-lastname.md`
- Example: `john-doe.md`
- Extracted from: First capitalized words in text
- Duplicates: Appends `-1`, `-2`, etc.

### Snippets
- Format: `YYYY-MM-DD-first-few-words.md`
- Example: `2024-01-15-discussed-auth.md`
- Extracted from: Date + first 3 words of text
- Duplicates: Appends `-HHMMSS` timestamp

### Abbreviations
- Format: `lowercase-abbr.md`
- Example: `api.md`, `jwt.md`
- Saved in: `abbreviations/custom/`
- Duplicates: Appends `-1`, `-2`, etc.

### Projects
- Format: `project-name.md`
- Example: `context-tool.md`
- Extracted from: First line or provided name
- Duplicates: Appends `-1`, `-2`, etc.

## Markdown Format

All files follow the same structure:

```markdown
---
[YAML Frontmatter]
type: person|snippet|abbreviation|project
[Type-specific fields]
created: YYYY-MM-DD HH:MM:SS
source: saved_from_clipboard
---

# [Title]

[Body content with sections]

## Related

- Add related items here
```

### Person File

```markdown
---
type: person
email: john@example.com
created: 2024-01-15 14:30:00
source: saved_from_clipboard
---

# John Doe

## Notes

[Original copied text goes here]

## Expertise

- Add skills and expertise

## Related

- [[Project Name]]
- [[Technology]]
```

### Snippet File

```markdown
---
type: snippet
date: 2024-01-15 14:30:00
source: clipboard
tags: []
---

# Saved Snippet - First Line

[Full text of your snippet]

## Context

Add context about this snippet.

## Related

- [[Person Name]]
- [[Project]]
```

### Abbreviation File

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

Application Programming Interface - Add your definition here.

## Usage

Add usage examples and context.

## Related

- [[REST]]
- [[HTTP]]
```

## Save Log Format

Each save is logged as a JSON line in `saves.log`:

```json
{
  "timestamp": "2024-01-15 14:30:22",
  "type": "person",
  "file": "people/john-doe.md",
  "reason": "Email address detected: 'john@example.com'",
  "text_preview": "john@example.com John Doe is a software engineer..."
}
```

### Log Fields

- **timestamp**: When the save occurred (ISO format)
- **type**: Entity type chosen (person/snippet/abbreviation/project)
- **file**: Relative path to saved file (from data-md/)
- **reason**: Why this type was detected
- **text_preview**: First 80 characters of saved text

### Using the Log

```bash
# View recent saves
tail -20 data-md/saves.log | jq

# Count saves by type
cat data-md/saves.log | jq -r '.type' | sort | uniq -c

# Find all person saves
cat data-md/saves.log | jq 'select(.type == "person")'

# View saves from today
cat data-md/saves.log | jq 'select(.timestamp | startswith("2024-01-15"))'
```

## Widget Integration

The Smart Saver is integrated into the widget mode:

1. **Copy text** anywhere on your system
2. Widget shows the text with matches
3. **Click "💾 Save Snippet"** or press **Ctrl+S**
4. **Dialog appears** with detected options
5. **Select type** and click Save
6. File created in markdown format
7. Action logged to `saves.log`
8. Success message shown

## Extending Detection

To add new detection patterns, edit `src/saver.py`:

### Add Detection Method

```python
def _detect_project(self, text: str) -> Tuple[float, str]:
    """Detect if text looks like a project"""
    # Add your detection logic
    if condition:
        return (0.7, "Reason for detection")
    return (0.0, "No pattern detected")
```

### Update detect_entity_type

```python
def detect_entity_type(self, text: str) -> List[Tuple[str, float, str]]:
    # ... existing code ...

    # Add your detection
    project_confidence, project_reason = self._detect_project(text)
    if project_confidence > 0:
        detections.append(('project', project_confidence, project_reason))
```

### Add Save Method

```python
def save_as_project(self, text: str, **kwargs) -> Path:
    """Save text as a project markdown file"""
    # Implement save logic
    # Return path to created file
```

## API

### EntitySaver Class

```python
from src.saver import EntitySaver

saver = EntitySaver(data_dir=Path('./data-md'))

# Detect entity type
detections = saver.detect_entity_type("John Doe")
# Returns: [('person', 0.9, "Found name pattern: 'John Doe'")]

# Save as specific type
path = saver.save_as_person("John Doe", email="john@example.com")
path = saver.save_as_snippet("Some text to save")
path = saver.save_as_abbreviation("API", full_form="Application Programming Interface")
```

### SmartSaver Wrapper

```python
from src.saver import SmartSaver

saver = SmartSaver(data_dir=Path('./data-md'))

# Get save choices
choices = saver.get_save_choices("John Doe")
# Returns: [{'type': 'person', 'label': '👤 Save as Person', ...}]

# Save with type
path = saver.save("John Doe", save_type='person')

# Or call directly (defaults to snippet)
path = saver("Some text")
```

## Benefits

✅ **Intelligent** - Auto-detects entity types
✅ **User Choice** - Always shows options, never forces
✅ **Confidence Scores** - Shows detection reasoning
✅ **Markdown Format** - Human-readable and editable
✅ **Logged** - Every action tracked with reasoning
✅ **Extensible** - Easy to add new detection patterns
✅ **Obsidian Compatible** - Works with Obsidian vaults
✅ **Version Control** - Git-friendly text format

## Future Enhancements

Possible improvements:

- **Machine Learning** - Learn from user corrections
- **Context-aware** - Use surrounding matches to improve detection
- **Bulk Actions** - Save multiple items at once
- **Templates** - Custom markdown templates per type
- **Auto-tagging** - Suggest tags based on content
- **Deduplication** - Check if item already exists
- **Rich Previews** - Show preview of how file will look
- **Undo** - Ability to undo recent saves
