# Markdown Data Format

This directory contains Obsidian-compatible markdown files for the Context Tool.

## Directory Structure

```
data-md/
├── people/              # Person/contact files
├── snippets/            # Saved text snippets
├── projects/            # Project information
└── abbreviations/       # Abbreviation definitions
    ├── tech/            # Technical abbreviations
    ├── business/        # Business terms
    ├── ai-ml/           # AI/ML related
    ├── development/     # Development concepts
    ├── security/        # Security terms
    └── networking/      # Networking protocols
```

## File Format

Each markdown file consists of:
1. **YAML frontmatter** (between `---` markers) for structured metadata
2. **Markdown body** for human-readable content
3. **Wikilinks** `[[Name]]` to connect related items

## Examples

### Person (`people/firstname-lastname.md`)

```markdown
---
type: person
email: person@example.com
role: Software Engineer
tags:
  - teammate
  - developer
expertise:
  - Python
  - JavaScript
last_contact: 2024-01-15 via Slack
next_event: Meeting tomorrow 2pm
---

# Person Name

Brief description of the person.

## Current Work

What they're working on now.

## Expertise

- Area 1
- Area 2

## Notes

- Important notes
- Preferences
- Contact info

## Related

- [[Project Name]] - Projects they're involved in
- [[Skill]] - Areas of expertise
```

### Snippet (`snippets/YYYY-MM-DD-title.md`)

```markdown
---
type: snippet
date: 2024-01-15 14:30
source: Slack conversation
tags:
  - topic1
  - topic2
people:
  - "[[Person Name]]"
projects:
  - "[[Project Name]]"
---

# Snippet Title

Main content of the snippet.

## Key Points

- Point 1
- Point 2

## Action Items

- [ ] Todo 1
- [ ] Todo 2

## Related

- [[Related Topic]]
```

### Project (`projects/project-name.md`)

```markdown
---
type: project
status: active
team_lead: "[[Person Name]]"
tags:
  - python
  - web
start_date: 2024-01-01
tech_stack:
  - Python
  - React
---

# Project Name

Description of the project.

## Features

- Feature 1
- Feature 2

## Team

- **Lead**: [[Person Name]]
- **Contributors**: Team members

## Status

Current status and progress.

## Related

- [[Technology]]
- [[Team Member]]
```

### Abbreviation (`abbreviations/category/term.md`)

```markdown
---
type: abbreviation
abbr: API
category: Development
examples:
  - REST API
  - GraphQL API
related:
  - "[[REST]]"
  - "[[HTTP]]"
links:
  - https://example.com/api-docs
---

# API - Application Programming Interface

Full explanation of the abbreviation.

## Key Concepts

Detailed information about the concept.

## Use Cases

- Use case 1
- Use case 2

## Related

- [[Related Term]]
```

## Wikilinks

Use wikilinks `[[Name]]` to create relationships between items:

- `[[Person Name]]` - Links to a person
- `[[Project Name]]` - Links to a project
- `[[Abbreviation]]` - Links to an abbreviation
- `[[Term|Display Text]]` - Link with custom display text

The Context Tool automatically:
1. Parses all wikilinks in both frontmatter and body
2. Creates relationships in the knowledge graph
3. Shows related items when you search for something

## Adding New Items

### New Person

1. Create `people/firstname-lastname.md`
2. Add frontmatter with email, role, tags, etc.
3. Write description and notes in markdown
4. Link to related projects and skills with `[[Project Name]]`

### New Snippet

1. Create `snippets/YYYY-MM-DD-topic.md`
2. Add frontmatter with date, source, tags
3. Write content in markdown
4. Link to people and projects mentioned

### New Abbreviation

1. Create `abbreviations/category/term.md`
2. Add frontmatter with abbr, category, examples, links
3. Write full explanation in markdown
4. Link to related concepts

## Obsidian Compatibility

These files work perfectly with Obsidian:

1. Open this folder as an Obsidian vault
2. All wikilinks will be clickable
3. Edit files with Obsidian's rich markdown editor
4. View the graph view to see relationships
5. Use tags and backlinks

## Benefits

✅ **Human-readable** - Edit in any text editor or Obsidian
✅ **Version control friendly** - Great for git
✅ **Searchable** - Easy to grep and search
✅ **Portable** - Standard markdown format
✅ **Rich formatting** - Headers, lists, code blocks, etc.
✅ **Connected** - Wikilinks create knowledge graph
✅ **Compatible** - Works with Obsidian, Foam, Dendron, etc.

## Migration from YAML

The Context Tool supports both YAML and Markdown formats. Use the `--markdown` flag:

```bash
# Use markdown files
./venv/bin/python3 main.py --mode widget --markdown

# Use YAML files (default)
./venv/bin/python3 main.py --mode widget

# Enable semantic search with either format (optional)
# ./venv/bin/python3 main.py --mode widget --local-semantic [--markdown]
```

When you use `--markdown`, the tool automatically looks in `data-md/` instead of `data/`.
