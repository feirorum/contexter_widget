---
type: project
status: active
team_lead: "[[Sarah Mitchell]]"
tags:
  - python
  - ai
  - productivity
  - desktop-app
start_date: 2024-01-01
tech_stack:
  - Python
  - FastAPI
  - SQLite
  - Tkinter
---

# Context Tool

A smart context analyzer that provides relevant information based on selected or copied text. Monitors system clipboard and provides instant lookups for abbreviations, contacts, and related information through multiple interfaces.

## Features

### Core Capabilities
- Text selection analysis with pattern matching
- Abbreviation lookup (100+ tech/business terms)
- Contact management and relationship tracking
- Knowledge graph for connected information
- Semantic search (optional)

### Interfaces
- **Web UI** - Browser-based interface with real-time WebSocket updates
- **Widget Mode** - Native desktop window with two-pane layout
- **System Mode** - Background clipboard monitoring

## Architecture

```
┌─────────────────┐
│ Clipboard       │
│ Monitor         │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Context         │
│ Analyzer        │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ UI Layer        │
│ (Web/Widget)    │
└─────────────────┘
```

## Team

- **Lead**: [[Sarah Mitchell]]
- **Contributors**: Development team

## Status

**Active Development** - Widget mode recently implemented with full keyboard navigation and action buttons. Abbreviations feature complete with 100+ entries.

## Related

- [[JWT]] - Used for authentication
- [[OAuth]] - Authentication protocol
- [[Python]] - Primary language
