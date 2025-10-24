"""FastAPI endpoints for the Context Tool"""

from fastapi import FastAPI, WebSocket, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
import sqlite3
from pathlib import Path

from .database import get_database
from .data_loader import load_data
from .pattern_matcher import PatternMatcher
from .action_suggester import ActionSuggester
from .context_analyzer import ContextAnalyzer

# Optional import for semantic search
try:
    from .semantic_searcher import SemanticSearcher
    SEMANTIC_AVAILABLE = True
except ImportError:
    SEMANTIC_AVAILABLE = False
    SemanticSearcher = None


# Pydantic models for request/response
class SelectionRequest(BaseModel):
    text: str
    context: Dict[str, Any] = {}


class SnippetRequest(BaseModel):
    text: str
    tags: List[str] = []
    source: Optional[str] = None


class AnalysisResponse(BaseModel):
    selected_text: str
    detected_type: Optional[str]
    patterns: Dict[str, List[str]]
    exact_matches: List[Dict]
    semantic_matches: List[Dict]
    related_items: List[Dict]
    smart_context: str
    actions: List[Dict]
    insights: List[str]


# Global state
app = FastAPI(title="Context Tool API", version="1.0.0")
db: Optional[sqlite3.Connection] = None
analyzer: Optional[ContextAnalyzer] = None
system_monitor: Optional[Any] = None


# WebSocket connection manager
class ConnectionManager:
    """Manage WebSocket connections for broadcasting"""

    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        """Accept and store a new connection"""
        await websocket.accept()
        self.active_connections.append(websocket)
        print(f"Client connected. Total connections: {len(self.active_connections)}")

    def disconnect(self, websocket: WebSocket):
        """Remove a connection"""
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
        print(f"Client disconnected. Total connections: {len(self.active_connections)}")

    async def broadcast(self, message: dict):
        """Send message to all connected clients"""
        disconnected = []
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except Exception as e:
                print(f"Error broadcasting to client: {e}")
                disconnected.append(connection)

        # Clean up disconnected clients
        for conn in disconnected:
            self.disconnect(conn)


# Global connection manager
manager = ConnectionManager()


def initialize_app(
    data_dir: Path,
    db_path: str = ":memory:",
    enable_semantic: bool = True,
    use_markdown: bool = False
):
    """
    Initialize the application with database and components

    Args:
        data_dir: Path to data directory with YAML or markdown files
        db_path: Database path or ":memory:"
        enable_semantic: Whether to enable semantic search
        use_markdown: Whether to load markdown files instead of YAML
    """
    global db, analyzer

    # Initialize database
    database = get_database(db_path)
    db = database.connection

    # Load data from YAML or Markdown
    if use_markdown:
        from .markdown_loader import load_markdown_data
        load_markdown_data(db, data_dir)
    else:
        load_data(db, data_dir)

    # Initialize components
    pattern_matcher = PatternMatcher()
    action_suggester = ActionSuggester()

    # Initialize semantic searcher if enabled and available
    semantic_searcher = None
    if enable_semantic and SEMANTIC_AVAILABLE:
        semantic_searcher = SemanticSearcher(db)
        semantic_searcher.initialize()
        semantic_searcher.generate_embeddings_for_all()
    elif enable_semantic and not SEMANTIC_AVAILABLE:
        print("Warning: Semantic search requested but dependencies not installed. Running without it.")

    # Create analyzer
    analyzer = ContextAnalyzer(
        db=db,
        pattern_matcher=pattern_matcher,
        action_suggester=action_suggester,
        semantic_searcher=semantic_searcher
    )

    print("Application initialized successfully")

    # Mount static files for UI
    ui_dir = Path(__file__).parent.parent / "ui" / "web"
    if ui_dir.exists():
        app.mount("/static", StaticFiles(directory=str(ui_dir)), name="static")


@app.get("/app.js")
async def serve_app_js():
    """Serve the app.js file"""
    ui_dir = Path(__file__).parent.parent / "ui" / "web"
    app_js = ui_dir / "app.js"

    if app_js.exists():
        with open(app_js) as f:
            return HTMLResponse(content=f.read(), media_type="application/javascript")

    return HTMLResponse(content="// App.js not found", media_type="application/javascript")


@app.get("/", response_class=HTMLResponse)
async def root():
    """Serve the main web UI"""
    ui_dir = Path(__file__).parent.parent / "ui" / "web"
    index_file = ui_dir / "index.html"

    if index_file.exists():
        with open(index_file) as f:
            return f.read()

    return """
    <html>
        <body>
            <h1>Context Tool API</h1>
            <p>UI not found. API is running.</p>
            <p><a href="/docs">API Documentation</a></p>
        </body>
    </html>
    """


@app.post("/api/analyze", response_model=AnalysisResponse)
async def analyze_selection(request: SelectionRequest):
    """
    Analyze selected text and return context

    Args:
        request: Selection request with text

    Returns:
        Complete analysis result
    """
    if analyzer is None:
        raise HTTPException(status_code=500, detail="Application not initialized")

    try:
        result = analyzer.analyze(request.text)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/save-snippet")
async def save_snippet(request: SnippetRequest):
    """
    Save a new snippet

    Args:
        request: Snippet data

    Returns:
        Status and snippet ID
    """
    if db is None:
        raise HTTPException(status_code=500, detail="Database not initialized")

    try:
        import json
        from datetime import datetime

        cursor = db.execute("""
            INSERT INTO snippets (text, saved_date, tags, source, metadata)
            VALUES (?, ?, ?, ?, ?)
        """, (
            request.text,
            datetime.now().isoformat(),
            json.dumps(request.tags),
            request.source,
            json.dumps({})
        ))

        db.commit()
        snippet_id = cursor.lastrowid

        return {
            "status": "saved",
            "id": snippet_id,
            "message": "Snippet saved successfully"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/contacts")
async def list_contacts():
    """
    Get all contacts

    Returns:
        List of all contacts
    """
    if db is None:
        raise HTTPException(status_code=500, detail="Database not initialized")

    try:
        cursor = db.execute("SELECT * FROM contacts")
        contacts = []

        for row in cursor.fetchall():
            contact = {key: row[key] for key in row.keys()}
            contacts.append(contact)

        return contacts
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/snippets")
async def list_snippets():
    """
    Get all snippets

    Returns:
        List of all snippets
    """
    if db is None:
        raise HTTPException(status_code=500, detail="Database not initialized")

    try:
        cursor = db.execute("SELECT * FROM snippets ORDER BY id DESC")
        snippets = []

        for row in cursor.fetchall():
            snippet = {key: row[key] for key in row.keys()}
            snippets.append(snippet)

        return snippets
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/projects")
async def list_projects():
    """
    Get all projects

    Returns:
        List of all projects
    """
    if db is None:
        raise HTTPException(status_code=500, detail="Database not initialized")

    try:
        cursor = db.execute("SELECT * FROM projects")
        projects = []

        for row in cursor.fetchall():
            project = {key: row[key] for key in row.keys()}
            projects.append(project)

        return projects
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/stats")
async def get_stats():
    """
    Get database statistics

    Returns:
        Statistics about the database
    """
    if db is None:
        raise HTTPException(status_code=500, detail="Database not initialized")

    try:
        contacts_count = db.execute("SELECT COUNT(*) as count FROM contacts").fetchone()['count']
        snippets_count = db.execute("SELECT COUNT(*) as count FROM snippets").fetchone()['count']
        projects_count = db.execute("SELECT COUNT(*) as count FROM projects").fetchone()['count']
        abbreviations_count = db.execute("SELECT COUNT(*) as count FROM abbreviations").fetchone()['count']
        relationships_count = db.execute("SELECT COUNT(*) as count FROM relationships").fetchone()['count']
        embeddings_count = db.execute("SELECT COUNT(*) as count FROM embeddings").fetchone()['count']

        return {
            "contacts": contacts_count,
            "snippets": snippets_count,
            "projects": projects_count,
            "abbreviations": abbreviations_count,
            "relationships": relationships_count,
            "embeddings": embeddings_count
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """
    WebSocket for real-time selection monitoring

    This allows the UI to send text selections and receive
    analysis results in real-time. Also receives broadcasts
    when system-wide text selection is enabled.
    """
    await manager.connect(websocket)

    if analyzer is None:
        await websocket.send_json({"error": "Application not initialized"})
        manager.disconnect(websocket)
        return

    try:
        while True:
            # Receive text from client (for demo mode)
            data = await websocket.receive_text()

            # Analyze the text
            result = analyzer.analyze(data)

            # Send results back to this client
            await websocket.send_json(result)

    except Exception as e:
        print(f"WebSocket error: {e}")
    finally:
        manager.disconnect(websocket)


async def start_system_monitoring(poll_interval: float = 0.5, min_length: int = 3):
    """
    Start system-wide clipboard monitoring

    Args:
        poll_interval: How often to check clipboard (seconds)
        min_length: Minimum text length to trigger analysis
    """
    global system_monitor

    # Import here to avoid circular dependency
    from monitors.system_monitor import AsyncSystemMonitor

    async def on_clipboard_change(text: str):
        """Callback when clipboard changes"""
        if analyzer:
            result = analyzer.analyze(text)
            result['source'] = 'system'  # Mark as system selection
            await manager.broadcast(result)

    system_monitor = AsyncSystemMonitor(
        on_selection=on_clipboard_change,
        poll_interval=poll_interval,
        min_length=min_length
    )

    await system_monitor.start()


@app.on_event("startup")
async def startup_event():
    """Application startup"""
    print("Context Tool API started")


@app.on_event("shutdown")
async def shutdown_event():
    """Clean up on shutdown"""
    global db, system_monitor

    if system_monitor:
        await system_monitor.stop()

    if db:
        db.close()
