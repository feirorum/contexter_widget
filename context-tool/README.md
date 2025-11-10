# Context Tool

A Python-based desktop application that monitors text selection and displays contextual information using a hybrid deterministic + LLM-enhanced approach.

## Features

- **Pattern Detection**: Automatically detects Jira tickets, emails, URLs, phone numbers, and dates
- **Knowledge Graph**: Links contacts, snippets, and projects together
- **Semantic Search**: Find semantically similar content using embeddings
- **Smart Context**: Generates human-readable context summaries
- **Action Suggestions**: Suggests relevant actions based on selected text
- **Web UI**: Interactive demo with real-time analysis

## Quick Start

### 1. Installation

```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment
# On Linux/Mac:
source venv/bin/activate
# On Windows:
venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Run the Application

```bash
# Start the web server
python main.py

# Or specify options
python main.py --port 8000 --host localhost
```

The application will:
1. Load data from YAML files in `data/`
2. Initialize the SQLite database
3. Generate embeddings for semantic search
4. Start the web server

### 3. Access the UI

Open your browser to: **http://localhost:8000**

## Usage

### Web Demo

1. Open the web interface at http://localhost:8000
2. Select any text in the left panel
3. See contextual information appear in the right panel

**Try selecting:**
- A person's name (e.g., "Sarah Mitchell")
- A Jira ticket (e.g., "JT-344")
- A project name (e.g., "TerminAI")
- An email address
- A URL

### API Endpoints

The application exposes a REST API:

- `GET /` - Web UI
- `POST /api/analyze` - Analyze text
- `POST /api/save-snippet` - Save a snippet
- `GET /api/contacts` - List all contacts
- `GET /api/snippets` - List all snippets
- `GET /api/projects` - List all projects
- `GET /api/stats` - Get database statistics
- `WS /ws` - WebSocket for real-time analysis

**API Documentation:** http://localhost:8000/docs

## Project Structure

```
context-tool/
├── main.py                 # Application entry point
├── config.yaml            # Configuration
├── requirements.txt       # Dependencies
│
├── data/                  # Data files
│   ├── contacts.yaml
│   ├── snippets.yaml
│   └── projects.yaml
│
├── src/
│   ├── __init__.py
│   ├── api.py                  # FastAPI endpoints
│   ├── database.py             # SQLite setup
│   ├── data_loader.py          # YAML loader
│   ├── pattern_matcher.py      # Pattern detection
│   ├── semantic_searcher.py    # Semantic search
│   ├── context_analyzer.py     # Main analysis engine
│   └── action_suggester.py     # Action generation
│
├── ui/                    # User interface
│   └── web/              # Web UI
│       ├── index.html
│       └── app.js
│
└── tests/                # Tests
```

## Configuration

Edit `config.yaml` to customize:

```yaml
app:
  mode: demo  # demo or system

database:
  path: ":memory:"  # or "context_tool.db" for persistent

semantic_search:
  enabled: true
  model: all-MiniLM-L6-v2
  similarity_threshold: 0.5

ui:
  port: 8000
  host: localhost
```

## Data Format

### contacts.yaml

```yaml
contacts:
  - name: Sarah Mitchell
    email: sarah.m@company.com
    role: Auth Team Lead
    last_contact: 3 days ago via Slack about JT-344
    next_event: Meeting tomorrow 2pm
    tags: [teammate, auth, technical-lead]
```

### snippets.yaml

```yaml
snippets:
  - text: "JT-344: Login timeout issues"
    tags: [JT-344, auth, timeout]
    saved_date: 3 days ago
    linked_contacts: [Sarah Mitchell]
```

### projects.yaml

```yaml
projects:
  - name: Authentication System Redesign
    status: In Progress
    tickets: [JT-344, JT-346, JT-348]
    team_lead: Sarah Mitchell
```

## Development

### Command Line Options

```bash
python main.py --help

Options:
  --config CONFIG        Path to config file (default: config.yaml)
  --mode {demo,system}   Operating mode
  --port PORT           Web server port (default: 8000)
  --host HOST           Web server host (default: localhost)
  --data-dir DIR        Data directory (default: ./data)
  --local-semantic      Enable semantic search (disabled by default to avoid long model downloads)
```

### Running Tests

```bash
pytest tests/
```

## How It Works

1. **Text Selection**: User selects text in the UI
2. **Pattern Detection**: System detects patterns (Jira tickets, emails, etc.)
3. **Database Search**: Finds exact matches in contacts, snippets, projects
4. **Semantic Search**: Finds semantically similar items using embeddings
5. **Knowledge Graph**: Traverses relationships to find related items
6. **Context Generation**: Builds human-readable context summary
7. **Action Suggestions**: Suggests relevant actions (open URL, email, etc.)
8. **Display**: Shows all results in the UI

## Technologies

- **Python 3.10+**
- **FastAPI** - Web framework
- **SQLite** - In-memory database
- **PyYAML** - Data loading
- **sentence-transformers** - Semantic embeddings
- **uvicorn** - ASGI server

## Phases Completed

✅ **Phase 1: Core Data Layer**
- SQLite database with schema
- YAML data loader
- Sample data files

✅ **Phase 2: Pattern Matching**
- Deterministic pattern detection
- Action suggestion rules

✅ **Phase 3: Context Analysis Engine**
- Main analyzer that ties everything together
- Knowledge graph traversal
- Smart context generation

✅ **Phase 4: Semantic Search**
- Embeddings generation
- Similarity search

✅ **Phase 5: API Layer**
- FastAPI endpoints
- WebSocket support

✅ **Phase 6: Web UI**
- Interactive demo interface
- Real-time analysis display

## Future Enhancements

- System-wide text selection monitoring (beyond demo)
- Desktop UI (PyQt/Tkinter)
- LLM integration for enhanced insights
- Chrome extension
- More pattern types (file paths, code snippets)
- Relationship strength learning
- Export/import functionality

## License

MIT License

## Contributing

Contributions welcome! Please open an issue or PR.
