# Text Selection Context Tool - Technical System Design

## Overview
A Python-based desktop application that monitors text selection (from demo text or system-wide) and displays contextual information using a hybrid deterministic + LLM-enhanced approach.

---

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    User Interface Layer                      │
│  ┌─────────────────┐           ┌──────────────────────┐    │
│  │  Demo Text UI   │           │  Context Display UI  │    │
│  │  (Selectable)   │──────────▶│  (Results Panel)     │    │
│  └─────────────────┘           └──────────────────────┘    │
│           │                              ▲                   │
│           │                              │                   │
└───────────┼──────────────────────────────┼───────────────────┘
            │                              │
            ▼                              │
┌─────────────────────────────────────────────────────────────┐
│                   Selection Monitor Layer                    │
│  ┌──────────────────┐      ┌──────────────────────────┐    │
│  │  Demo Selection  │      │  System-wide Selection   │    │
│  │  Handler         │      │  (pyperclip/pynput)      │    │
│  └──────────────────┘      └──────────────────────────┘    │
└───────────────────────────────────────┬─────────────────────┘
                                        │
                                        ▼
┌─────────────────────────────────────────────────────────────┐
│                    Context Engine Layer                      │
│  ┌──────────────────────────────────────────────────────┐   │
│  │              Context Analyzer                        │   │
│  │  • Pattern Detection (Jira, emails, contacts)        │   │
│  │  • Semantic Search (embeddings for "related")        │   │
│  │  • Action Suggestion Rules                           │   │
│  └──────────────────────────────────────────────────────┘   │
│                           │                                  │
│         ┌─────────────────┼─────────────────┐               │
│         ▼                 ▼                 ▼               │
│  ┌──────────┐      ┌──────────┐     ┌──────────┐          │
│  │Pattern   │      │Semantic  │     │Action    │          │
│  │Matcher   │      │Searcher  │     │Suggester │          │
│  └──────────┘      └──────────┘     └──────────┘          │
└───────────────────────────────┬─────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────┐
│                      Data Layer                              │
│  ┌──────────────────────────────────────────────────────┐   │
│  │              SQLite In-Memory Database                │   │
│  │  • contacts                                           │   │
│  │  • snippets                                           │   │
│  │  • projects                                           │   │
│  │  • relationships                                      │   │
│  └──────────────────────────────────────────────────────┘   │
│                           ▲                                  │
│                           │                                  │
│  ┌──────────────────────────────────────────────────────┐   │
│  │         YAML Data Loader (on startup)                 │   │
│  │  • contacts.yaml                                      │   │
│  │  • snippets.yaml                                      │   │
│  │  • projects.yaml                                      │   │
│  └──────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
```

---

## Technology Stack

### Core Framework
- **Python 3.10+**
- **FastAPI** - Backend API for context queries
- **SQLite** - In-memory database
- **PyYAML** - Configuration and data loading

### UI Options (Choose One)
1. **Web UI (Recommended for Demo)**
   - FastAPI serving HTML/JS interface
   - WebSocket for real-time updates
   - Similar to current demo webpage

2. **Native Desktop UI**
   - **PyQt6** or **Tkinter** for cross-platform GUI
   - System tray integration

### Text Selection Monitoring
- **Demo Mode**: Click-based selection in UI
- **System Mode**: 
  - **pyperclip** - Clipboard monitoring
  - **pynput** - Keyboard/mouse event capture
  - **python-xlib** (Linux) / **pywin32** (Windows) / **pyobjc** (macOS) for window focus

### Semantic Search (Optional LLM Enhancement)
- **sentence-transformers** - Local embeddings for similarity
- **FAISS** or **ChromaDB** - Vector storage and search
- **Ollama Python client** - For local LLM queries

---

## Data Model

### Database Schema (SQLite)

```sql
-- Contacts
CREATE TABLE contacts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    email TEXT,
    role TEXT,
    context TEXT,
    last_contact TEXT,
    next_event TEXT,
    tags TEXT, -- JSON array
    metadata TEXT -- JSON object
);

-- Snippets
CREATE TABLE snippets (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    text TEXT NOT NULL,
    saved_date TEXT,
    tags TEXT, -- JSON array
    source TEXT, -- where it came from
    metadata TEXT -- JSON object
);

-- Projects
CREATE TABLE projects (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    status TEXT,
    description TEXT,
    tags TEXT, -- JSON array
    metadata TEXT -- JSON object
);

-- Relationships (knowledge graph edges)
CREATE TABLE relationships (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    from_type TEXT, -- contact, snippet, project
    from_id INTEGER,
    to_type TEXT,
    to_id INTEGER,
    relationship_type TEXT, -- worked_on, mentioned_in, related_to
    strength REAL DEFAULT 1.0, -- relationship weight
    metadata TEXT
);

-- Embeddings (for semantic search)
CREATE TABLE embeddings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    entity_type TEXT, -- contact, snippet, project
    entity_id INTEGER,
    embedding BLOB, -- numpy array as bytes
    text TEXT -- original text that was embedded
);
```

### YAML Data Format

**contacts.yaml**
```yaml
contacts:
  - name: Sarah Mitchell
    email: sarah.m@company.com
    role: Auth Team Lead
    last_contact: 3 days ago via Slack about JT-344
    next_event: Meeting tomorrow 2pm
    tags: [teammate, auth, technical-lead]
    expertise: [OAuth, JWT, mobile auth]
    
  - name: Magnus Sjöstrand
    context: Met today, discussed Europe trip
    tags: [new-contact, travel, europe]
    
  - name: Stefan K
    github: https://github.com/sefn/terminai
    interests: [LLM, Linux, OS, desktop-interfaces]
    project: TerminAI - Linux LLM interface
    tags: [developer, llm-interfaces, linux]
```

**snippets.yaml**
```yaml
snippets:
  - id: 1
    text: "JT-344: Login timeout issues"
    tags: [JT-344, auth, timeout]
    saved_date: 3 days ago
    linked_contacts: [Sarah Mitchell]
    
  - id: 2
    text: "JT-3xx series all related to auth system overhaul"
    tags: [auth, project-planning, jira]
    saved_date: last week
    
  - id: 3
    text: "I tried to fix JT-344 with a new cert but it didn't fix the problem"
    tags: [JT-344, troubleshooting, certificates, auth-issues]
    saved_date: just saved
    linked_contacts: [Sarah Mitchell]
    linked_projects: [Authentication System]
```

**projects.yaml**
```yaml
projects:
  - name: Authentication System Redesign
    status: In Progress
    tickets: [JT-344, JT-346, JT-348]
    team_lead: Sarah Mitchell
    issues: [Certificate problems, Login timeouts, Token refresh]
    
  - name: TerminAI
    type: Linux LLM interface
    creator: Stefan K
    repository: https://github.com/sefn/terminai
    keywords: [ollama, deno, glow, wofi, keyboard-driven]
```

---

## Core Components

### 1. Data Loader (`data_loader.py`)

```python
import yaml
import sqlite3
import json
from pathlib import Path

class DataLoader:
    def __init__(self, db_connection):
        self.db = db_connection
        
    def load_from_yaml(self, data_dir: Path):
        """Load all YAML files into SQLite database"""
        self._load_contacts(data_dir / "contacts.yaml")
        self._load_snippets(data_dir / "snippets.yaml")
        self._load_projects(data_dir / "projects.yaml")
        self._build_relationships()
        
    def _load_contacts(self, filepath: Path):
        with open(filepath) as f:
            data = yaml.safe_load(f)
            for contact in data['contacts']:
                self.db.execute("""
                    INSERT INTO contacts (name, email, role, context, 
                                         last_contact, next_event, tags, metadata)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    contact.get('name'),
                    contact.get('email'),
                    contact.get('role'),
                    contact.get('context'),
                    contact.get('last_contact'),
                    contact.get('next_event'),
                    json.dumps(contact.get('tags', [])),
                    json.dumps({k: v for k, v in contact.items() 
                              if k not in ['name', 'email', 'role', 'context', 
                                          'last_contact', 'next_event', 'tags']})
                ))
```

### 2. Pattern Matcher (`pattern_matcher.py`)

```python
import re
from typing import Dict, List, Optional

class PatternMatcher:
    """Deterministic pattern detection for known formats"""
    
    PATTERNS = {
        'jira_ticket': r'\b(JT-?\d+)\b',
        'email': r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',
        'url': r'https?://[^\s]+',
        'phone': r'\b\d{3}[-.]?\d{3}[-.]?\d{4}\b',
        'date': r'\b\d{4}-\d{2}-\d{2}\b'
    }
    
    def detect(self, text: str) -> Dict[str, List[str]]:
        """Detect all patterns in text"""
        results = {}
        for pattern_type, regex in self.PATTERNS.items():
            matches = re.findall(regex, text, re.IGNORECASE)
            if matches:
                results[pattern_type] = matches
        return results
    
    def get_type(self, text: str) -> Optional[str]:
        """Get primary type of the text"""
        detections = self.detect(text)
        if not detections:
            return None
        # Return most specific pattern found
        priority = ['jira_ticket', 'email', 'url', 'phone', 'date']
        for ptype in priority:
            if ptype in detections:
                return ptype
        return list(detections.keys())[0]
```

### 3. Context Analyzer (`context_analyzer.py`)

```python
from typing import Dict, List, Any
from pattern_matcher import PatternMatcher
from semantic_searcher import SemanticSearcher

class ContextAnalyzer:
    def __init__(self, db, pattern_matcher, semantic_searcher):
        self.db = db
        self.pattern_matcher = pattern_matcher
        self.semantic = semantic_searcher
        
    def analyze(self, selected_text: str) -> Dict[str, Any]:
        """Main analysis entry point"""
        # 1. Detect patterns (deterministic)
        patterns = self.pattern_matcher.detect(selected_text)
        text_type = self.pattern_matcher.get_type(selected_text)
        
        # 2. Find exact matches in database
        exact_matches = self._find_exact_matches(selected_text)
        
        # 3. Find semantic matches (LLM-enhanced)
        semantic_matches = self.semantic.find_similar(selected_text, limit=5)
        
        # 4. Build knowledge graph context
        related_items = self._get_related_items(exact_matches)
        
        # 5. Generate smart context
        smart_context = self._generate_smart_context(
            selected_text, text_type, exact_matches, related_items
        )
        
        # 6. Suggest actions
        actions = self._suggest_actions(text_type, exact_matches)
        
        return {
            'selected_text': selected_text,
            'detected_type': text_type,
            'patterns': patterns,
            'related': semantic_matches + exact_matches,
            'smart_context': smart_context,
            'actions': actions,
            'insights': self._generate_insights(exact_matches, related_items)
        }
    
    def _find_exact_matches(self, text: str) -> List[Dict]:
        """Find exact matches in contacts, snippets, projects"""
        results = []
        
        # Search contacts
        cursor = self.db.execute("""
            SELECT * FROM contacts 
            WHERE name LIKE ? OR email LIKE ?
        """, (f'%{text}%', f'%{text}%'))
        for row in cursor.fetchall():
            results.append({
                'type': 'contact',
                'data': dict(row)
            })
        
        # Search snippets
        cursor = self.db.execute("""
            SELECT * FROM snippets 
            WHERE text LIKE ?
        """, (f'%{text}%',))
        for row in cursor.fetchall():
            results.append({
                'type': 'snippet',
                'data': dict(row)
            })
            
        return results
```

### 4. Semantic Searcher (`semantic_searcher.py`)

```python
from sentence_transformers import SentenceTransformer
import numpy as np
from typing import List, Dict

class SemanticSearcher:
    """LLM-enhanced semantic similarity search"""
    
    def __init__(self, db, model_name='all-MiniLM-L6-v2'):
        self.db = db
        self.model = SentenceTransformer(model_name)
        self._load_embeddings()
        
    def _load_embeddings(self):
        """Load pre-computed embeddings from database"""
        cursor = self.db.execute("SELECT * FROM embeddings")
        self.embeddings = []
        for row in cursor.fetchall():
            self.embeddings.append({
                'entity_type': row['entity_type'],
                'entity_id': row['entity_id'],
                'text': row['text'],
                'embedding': np.frombuffer(row['embedding'], dtype=np.float32)
            })
    
    def find_similar(self, query: str, limit: int = 5) -> List[Dict]:
        """Find semantically similar items"""
        query_embedding = self.model.encode(query)
        
        similarities = []
        for item in self.embeddings:
            similarity = np.dot(query_embedding, item['embedding'])
            similarities.append((similarity, item))
        
        # Sort by similarity and return top results
        similarities.sort(reverse=True, key=lambda x: x[0])
        return [
            {
                'type': item['entity_type'],
                'id': item['entity_id'],
                'text': item['text'],
                'similarity': float(score)
            }
            for score, item in similarities[:limit]
            if score > 0.5  # threshold
        ]
```

---

## API Endpoints (FastAPI)

```python
from fastapi import FastAPI, WebSocket
from pydantic import BaseModel

app = FastAPI()

class SelectionRequest(BaseModel):
    text: str
    context: dict = {}

@app.post("/api/analyze")
async def analyze_selection(request: SelectionRequest):
    """Analyze selected text and return context"""
    analyzer = ContextAnalyzer(db, pattern_matcher, semantic_searcher)
    result = analyzer.analyze(request.text)
    return result

@app.post("/api/save-snippet")
async def save_snippet(text: str, tags: List[str] = None):
    """Save a new snippet"""
    # Insert into database
    # Generate embeddings
    # Update relationships
    return {"status": "saved", "id": snippet_id}

@app.get("/api/contacts")
async def list_contacts():
    """Get all contacts"""
    cursor = db.execute("SELECT * FROM contacts")
    return [dict(row) for row in cursor.fetchall()]

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket for real-time selection monitoring"""
    await websocket.accept()
    while True:
        data = await websocket.receive_text()
        result = analyzer.analyze(data)
        await websocket.send_json(result)
```

---

## Project Structure

```
context-tool/
├── main.py                 # Application entry point
├── requirements.txt        # Python dependencies
├── config.yaml            # Configuration
│
├── data/                  # Data files
│   ├── contacts.yaml
│   ├── snippets.yaml
│   └── projects.yaml
│
├── src/
│   ├── __init__.py
│   ├── data_loader.py          # YAML → SQLite loader
│   ├── database.py             # Database setup and utils
│   ├── pattern_matcher.py      # Deterministic patterns
│   ├── semantic_searcher.py    # Vector similarity search
│   ├── context_analyzer.py     # Main analysis engine
│   ├── action_suggester.py     # Action generation
│   └── api.py                  # FastAPI endpoints
│
├── ui/                    # User interface
│   ├── web/              # Web-based UI (HTML/JS)
│   │   ├── index.html
│   │   └── app.js
│   └── desktop/          # Native UI (PyQt/Tkinter)
│       └── main_window.py
│
├── monitors/             # Selection monitoring
│   ├── demo_monitor.py   # Demo text selection
│   └── system_monitor.py # System-wide clipboard/selection
│
└── tests/
    ├── test_data_loader.py
    ├── test_pattern_matcher.py
    └── test_context_analyzer.py
```

---

## Dependencies (requirements.txt)

```
# Core
fastapi>=0.104.0
uvicorn[standard]>=0.24.0
pydantic>=2.4.0
pyyaml>=6.0.1

# Database
sqlite3  # Built-in

# Semantic Search (Optional)
sentence-transformers>=2.2.2
numpy>=1.24.0
faiss-cpu>=1.7.4  # or chromadb

# Text Selection Monitoring
pyperclip>=1.8.2
pynput>=1.7.6

# UI (choose one)
# Web UI - included with FastAPI
# PyQt6>=6.6.0  # For native desktop UI
# tkinter  # Built-in

# Development
pytest>=7.4.0
black>=23.10.0
```

---

## Running the Application

### Setup
```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Initialize data
python -m src.data_loader
```

### Run Demo Mode (Web UI)
```bash
# Start the FastAPI server
uvicorn src.api:app --reload

# Open browser to http://localhost:8000
```

### Run System Mode (System-wide monitoring)
```bash
# Start with system-wide selection monitoring
python main.py --mode system
```

---

## Configuration (config.yaml)

```yaml
app:
  name: Context Tool
  mode: demo  # demo or system
  
database:
  type: sqlite
  path: ":memory:"  # or path to file
  
data:
  directory: ./data
  auto_load: true
  
semantic_search:
  enabled: true
  model: all-MiniLM-L6-v2
  similarity_threshold: 0.5
  
monitoring:
  demo:
    enabled: true
  system:
    enabled: false
    clipboard: true
    hotkey: "ctrl+shift+space"
    
ui:
  type: web  # web or desktop
  port: 8000
  host: localhost
```

---

## Next Steps for Implementation

1. **Phase 1: Core Data Layer**
   - Implement SQLite schema
   - Create YAML loader
   - Test with roleplay data

2. **Phase 2: Pattern Matching**
   - Implement deterministic patterns
   - Build action suggestion rules
   - Create test cases

3. **Phase 3: Basic UI**
   - Web interface with demo text
   - Click-based selection
   - Context display panel

4. **Phase 4: Semantic Search**
   - Add embeddings generation
   - Implement similarity search
   - Test with related content queries

5. **Phase 5: System Monitoring**
   - Add clipboard monitoring
   - Implement system-wide selection capture
   - Test cross-application functionality

---

## Testing Strategy

```python
# tests/test_context_analyzer.py
def test_jira_ticket_detection():
    analyzer = ContextAnalyzer(db, pattern_matcher, semantic_searcher)
    result = analyzer.analyze("JT-346")
    
    assert result['detected_type'] == 'jira_ticket'
    assert 'JT-344' in str(result['related'])
    assert 'Authentication System' in str(result['smart_context'])
    assert 'Open in Jira' in result['actions']
```

---

## Performance Considerations

- **Embeddings**: Pre-compute on data load, not on query
- **Database**: Index on frequently searched fields (name, tags)
- **Caching**: Cache recent context analysis results
- **Lazy Loading**: Load semantic search only if enabled
- **Async**: Use async/await for non-blocking operations