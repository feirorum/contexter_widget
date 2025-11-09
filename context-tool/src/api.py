"""FastAPI endpoints for the Context Tool"""

from fastapi import FastAPI, WebSocket, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
import sqlite3
from pathlib import Path

from .database import get_database
from .data_loaders import load_data
from .pattern_matcher import PatternMatcher
from .action_suggester import ActionSuggester
from .context_analyzer import ContextAnalyzer
from .saver import SmartSaver

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
    # Smart save options
    link_to_existing: List[Dict[str, Any]] = []
    create_new_contacts: List[Dict[str, str]] = []


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
    detected_people: List[Dict] = []  # People detected in text for smart save


# Global state
app = FastAPI(title="Context Tool API", version="1.0.0")
db: Optional[sqlite3.Connection] = None
analyzer: Optional[ContextAnalyzer] = None
saver: Optional[SmartSaver] = None
system_monitor: Optional[Any] = None
app_data_dir: Optional[Path] = None
app_use_markdown: bool = False


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
    global db, analyzer, saver, app_data_dir, app_use_markdown

    # Store global config
    app_data_dir = Path(data_dir)
    app_use_markdown = use_markdown

    # Initialize database
    database = get_database(db_path)
    db = database.connection

    # Load data from YAML or Markdown
    print(f"📁 Data format: {'Markdown' if use_markdown else 'YAML'}")
    print(f"📁 Data directory: {Path(data_dir).absolute()}")

    # Load data using unified interface
    if use_markdown:
        load_data(db, data_dir, format='markdown')
    else:
        load_data(db, data_dir, format='yaml')

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

    # Initialize saver (only for markdown mode)
    if use_markdown:
        def reload_callback(save_type: str):
            """Callback to reload data after save"""
            load_data(db, data_dir, format='markdown')
            print(f"   📚 Reloaded data after {save_type} save")

        saver = SmartSaver(
            data_dir=app_data_dir,
            log_file=app_data_dir / "saves.log",
            on_save_callback=reload_callback
        )
        print(f"💾 Saver initialized for {app_data_dir}")
    else:
        print("⚠️  Saver not initialized (YAML mode doesn't support markdown saving)")

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
    Save a new snippet with smart linking

    Args:
        request: Snippet data with optional smart linking options

    Returns:
        Status and snippet ID with details about created/linked contacts
    """
    if db is None:
        raise HTTPException(status_code=500, detail="Database not initialized")

    try:
        created_contacts = []

        # Use EntitySaver for markdown mode (saves to files and links to persons)
        if app_use_markdown and saver:
            # 1. Create new contacts if requested
            for new_person in request.create_new_contacts:
                person_name = new_person.get('name', '')
                if person_name:
                    try:
                        person_file = saver.save(
                            text=person_name,
                            save_type='person',
                            metadata={'source': 'smart_save'}
                        )
                        created_contacts.append(person_name)
                    except Exception as e:
                        print(f"Warning: Failed to create contact for {person_name}: {e}")

            # 2. Build list of explicit person names to link to (respects user selections)
            explicit_person_names = []

            # Add existing contacts the user selected
            for existing_contact in request.link_to_existing:
                contact_name = existing_contact.get('contact_name', '')
                if contact_name:
                    explicit_person_names.append(contact_name)

            # Add newly created contacts
            for new_person in request.create_new_contacts:
                person_name = new_person.get('name', '')
                if person_name:
                    explicit_person_names.append(person_name)

            # 3. Save the snippet with explicit person linking (only link to user-selected contacts)
            # If user made selections, use explicit linking; otherwise auto-detect
            use_explicit = len(request.link_to_existing) > 0 or len(request.create_new_contacts) > 0

            filepath = saver.save(
                text=request.text,
                save_type='snippet',
                metadata={
                    'tags': request.tags,
                    'source': request.source or 'web',
                    'explicit_person_names': explicit_person_names if use_explicit else None,
                    'auto_link_persons': not use_explicit  # Auto-link only if no explicit selections
                }
            )

            # 4. Prepare result message
            msg_parts = [f"Snippet saved to {filepath.name}"]
            if created_contacts:
                msg_parts.append(f"Created {len(created_contacts)} new contact(s): {', '.join(created_contacts)}")
            if request.link_to_existing:
                msg_parts.append(f"Linked to {len(request.link_to_existing)} existing contact(s)")

            return {
                "status": "saved",
                "file": str(filepath.name) if filepath else None,
                "message": ". ".join(msg_parts),
                "created_contacts": created_contacts,
                "linked_contacts": [p.get('contact_name', '') for p in request.link_to_existing]
            }
        else:
            # Fallback to database save for YAML mode
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
                "message": "Snippet saved successfully (YAML mode - smart linking not available)"
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


# Smart Saver endpoints
smart_saver_instance = None  # Global instance


def _reload_data_after_save(save_type: str):
    """
    Reload data from files after saving

    Args:
        save_type: Type of entity that was saved
    """
    global db, app_data_dir, app_use_markdown

    if db is None or app_data_dir is None:
        print("Warning: Cannot reload data - app not initialized")
        return

    print(f"🔄 Reloading {save_type} data...")

    # Reload all data from files
    if app_use_markdown:
        load_data(db, app_data_dir, format='markdown')
    else:
        load_data(db, app_data_dir, format='yaml')

    print(f"✓ Data reloaded! New {save_type} is now searchable.")


def get_smart_saver():
    """Get or create Smart Saver instance"""
    global smart_saver_instance, app_data_dir, app_use_markdown

    if smart_saver_instance is None:
        from .saver import SmartSaver

        # Use configured data directory, or fallback to auto-detection
        if app_data_dir:
            data_dir = app_data_dir
        else:
            data_dir = Path("./data-md") if Path("./data-md").exists() else Path("./data")

        smart_saver_instance = SmartSaver(
            data_dir=data_dir,
            on_save_callback=_reload_data_after_save
        )

    return smart_saver_instance


class SaveSmartRequest(BaseModel):
    text: str


class SaveSmartPerformRequest(BaseModel):
    text: str
    save_type: str
    metadata: Optional[Dict[str, Any]] = None


@app.post("/api/save-smart/detect")
async def detect_save_type(request: SaveSmartRequest):
    """
    Detect save type for text using Smart Saver

    Returns save type choices with confidence and reasoning
    """
    try:
        saver = get_smart_saver()
        choices = saver.get_save_choices(request.text)

        return {
            "choices": choices,
            "text_preview": request.text[:100]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/save-smart/save")
async def save_smart(request: SaveSmartPerformRequest):
    """
    Perform smart save with chosen type

    Saves to appropriate markdown directory and logs action
    """
    try:
        saver = get_smart_saver()
        result = saver.save(request.text, request.save_type, request.metadata)

        if result:
            return {
                "status": "success",
                "message": f"Saved as {request.save_type}",
                "file": result
            }
        else:
            return {
                "status": "error",
                "message": "Failed to save"
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
