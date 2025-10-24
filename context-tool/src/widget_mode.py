"""Widget mode for Context Tool - Desktop UI with clipboard monitoring"""

import asyncio
import threading
import sqlite3
from pathlib import Path
from typing import Optional
import json
from datetime import datetime

from .database import get_database
from .data_loader import load_data
from .pattern_matcher import PatternMatcher
from .action_suggester import ActionSuggester
from .context_analyzer import ContextAnalyzer
from .widget_ui import ContextWidget
from .saver import SmartSaver

# Optional import for semantic search
try:
    from .semantic_searcher import SemanticSearcher
    SEMANTIC_AVAILABLE = True
except ImportError:
    SEMANTIC_AVAILABLE = False
    SemanticSearcher = None


class WidgetMode:
    """
    Desktop widget mode with clipboard monitoring

    This mode runs a tkinter desktop widget that shows context analysis
    results when text is copied to the clipboard.
    """

    def __init__(
        self,
        data_dir: Path,
        db_path: str = ":memory:",
        enable_semantic: bool = False,
        poll_interval: float = 0.5,
        min_length: int = 3,
        use_markdown: bool = False
    ):
        """
        Initialize widget mode

        Args:
            data_dir: Directory containing YAML or markdown data files
            db_path: Path to SQLite database
            enable_semantic: Enable semantic search
            poll_interval: Clipboard polling interval in seconds
            min_length: Minimum text length to trigger analysis
            use_markdown: Use markdown files instead of YAML
        """
        self.data_dir = Path(data_dir)
        self.db_path = db_path
        self.enable_semantic = enable_semantic
        self.poll_interval = poll_interval
        self.min_length = min_length
        self.use_markdown = use_markdown

        # Components
        self.db = None
        self.analyzer = None
        self.widget = None
        self.saver = None
        self.monitor_thread = None
        self.running = False

        # Clipboard tracking
        self.last_clipboard = ""

    def initialize(self):
        """Initialize database and components"""
        print("Initializing widget mode...")

        # Setup database
        db_instance = get_database(self.db_path)
        self.db = db_instance.connection

        # Load data
        print(f"Loading data from {self.data_dir}...")
        if self.use_markdown:
            from .markdown_loader import load_markdown_data
            load_markdown_data(self.db, self.data_dir)
        else:
            load_data(self.db, self.data_dir)

        # Initialize components
        pattern_matcher = PatternMatcher()
        action_suggester = ActionSuggester()

        # Semantic searcher (optional)
        semantic_searcher = None
        if self.enable_semantic and SEMANTIC_AVAILABLE:
            print("Initializing semantic search...")
            semantic_searcher = SemanticSearcher(self.db)
            semantic_searcher.build_index()

        # Create analyzer
        self.analyzer = ContextAnalyzer(
            db=self.db,
            pattern_matcher=pattern_matcher,
            action_suggester=action_suggester,
            semantic_searcher=semantic_searcher
        )

        # Create smart saver
        self.saver = SmartSaver(data_dir=self.data_dir)

        # Create widget UI (show on start for widget mode)
        self.widget = ContextWidget(on_save_snippet=self.saver, start_hidden=False)

        print("Initialization complete!")

    def check_clipboard(self):
        """Check clipboard for changes and analyze"""
        try:
            import pyperclip
            import sqlite3
            
            # Create thread-local database connection
            thread_db = get_database(self.db_path).connection
            thread_analyzer = ContextAnalyzer(
                db=thread_db,
                pattern_matcher=self.analyzer.pattern_matcher,
                action_suggester=self.analyzer.action_suggester,
                semantic_searcher=None  # Semantic search disabled in monitoring thread
            )

            current_clipboard = pyperclip.paste()

            # Check if clipboard changed and meets minimum length
            if (current_clipboard != self.last_clipboard and
                len(current_clipboard.strip()) >= self.min_length):

                self.last_clipboard = current_clipboard

                print(f"\n📋 Clipboard changed: {current_clipboard[:50]}...")

                # Analyze the text using thread-local analyzer
                result = thread_analyzer.analyze(current_clipboard.strip())

                # Show in widget (must be done in main thread)
                self.widget.root.after(0, lambda: self.widget.show(result))

        except ImportError:
            print("Error: pyperclip not installed. Install with: pip install pyperclip")
            self.running = False
        except Exception as e:
            print(f"Error checking clipboard: {e}")
            import traceback
            traceback.print_exc()

    def monitor_clipboard_loop(self):
        """Background thread to monitor clipboard"""
        import time

        while self.running:
            self.check_clipboard()
            time.sleep(self.poll_interval)

    def start_clipboard_monitoring(self):
        """Start clipboard monitoring in background thread"""
        self.running = True

        # Start monitoring thread
        self.monitor_thread = threading.Thread(
            target=self.monitor_clipboard_loop,
            daemon=True
        )
        self.monitor_thread.start()

        print(f"\n🔍 Clipboard monitoring started!")
        print(f"   Polling interval: {self.poll_interval}s")
        print(f"   Minimum text length: {self.min_length} characters")
        print(f"\n   Copy any text to see context analysis in the widget!")

    def stop_clipboard_monitoring(self):
        """Stop clipboard monitoring"""
        self.running = False
        if self.monitor_thread:
            self.monitor_thread.join(timeout=2.0)

    def run(self):
        """
        Run the widget mode

        This starts clipboard monitoring and runs the tkinter main loop.
        """
        # Initialize components
        self.initialize()

        # Start clipboard monitoring
        self.start_clipboard_monitoring()

        # Run the widget UI (blocking)
        try:
            print("\n" + "="*60)
            print("Widget Mode Running!")
            print("="*60)
            print("\nCopy text anywhere on your system to see context analysis.")
            print("Press Ctrl+C or close the widget window to exit.\n")

            self.widget.run()
        except KeyboardInterrupt:
            print("\nShutting down...")
        finally:
            self.stop_clipboard_monitoring()


def run_widget_mode(
    data_dir: Path,
    db_path: str = ":memory:",
    enable_semantic: bool = False,
    poll_interval: float = 0.5,
    min_length: int = 3,
    use_markdown: bool = False
):
    """
    Convenience function to run widget mode

    Args:
        data_dir: Directory containing YAML or markdown data files
        db_path: Path to SQLite database
        enable_semantic: Enable semantic search
        poll_interval: Clipboard polling interval in seconds
        min_length: Minimum text length to trigger analysis
        use_markdown: Use markdown files instead of YAML
    """
    mode = WidgetMode(
        data_dir=data_dir,
        db_path=db_path,
        enable_semantic=enable_semantic,
        poll_interval=poll_interval,
        min_length=min_length,
        use_markdown=use_markdown
    )
    mode.run()
