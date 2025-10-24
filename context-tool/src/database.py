"""Database setup and utilities for the Context Tool"""

import sqlite3
from pathlib import Path
from typing import Optional


class Database:
    """SQLite database manager for context tool"""

    def __init__(self, db_path: str = ":memory:"):
        """
        Initialize database connection

        Args:
            db_path: Path to SQLite database file, or ":memory:" for in-memory database
        """
        self.db_path = db_path
        self.connection = None

    def connect(self) -> sqlite3.Connection:
        """Connect to database and enable row factory"""
        self.connection = sqlite3.connect(self.db_path)
        self.connection.row_factory = sqlite3.Row
        return self.connection

    def initialize_schema(self):
        """Create all database tables"""
        if not self.connection:
            raise RuntimeError("Database not connected. Call connect() first.")

        cursor = self.connection.cursor()

        # Contacts table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS contacts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                email TEXT,
                role TEXT,
                context TEXT,
                last_contact TEXT,
                next_event TEXT,
                tags TEXT,
                metadata TEXT
            )
        """)

        # Snippets table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS snippets (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                text TEXT NOT NULL,
                saved_date TEXT,
                tags TEXT,
                source TEXT,
                metadata TEXT
            )
        """)

        # Projects table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS projects (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                status TEXT,
                description TEXT,
                tags TEXT,
                metadata TEXT
            )
        """)

        # Abbreviations table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS abbreviations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                abbr TEXT NOT NULL,
                full TEXT NOT NULL,
                definition TEXT,
                category TEXT,
                examples TEXT,
                related TEXT,
                links TEXT,
                metadata TEXT
            )
        """)

        # Relationships table (knowledge graph edges)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS relationships (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                from_type TEXT,
                from_id INTEGER,
                to_type TEXT,
                to_id INTEGER,
                relationship_type TEXT,
                strength REAL DEFAULT 1.0,
                metadata TEXT
            )
        """)

        # Embeddings table (for semantic search)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS embeddings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                entity_type TEXT,
                entity_id INTEGER,
                embedding BLOB,
                text TEXT
            )
        """)

        # Create indexes for better performance
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_contacts_name
            ON contacts(name)
        """)

        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_contacts_email
            ON contacts(email)
        """)

        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_snippets_text
            ON snippets(text)
        """)

        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_relationships_from
            ON relationships(from_type, from_id)
        """)

        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_relationships_to
            ON relationships(to_type, to_id)
        """)

        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_embeddings_entity
            ON embeddings(entity_type, entity_id)
        """)

        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_abbreviations_abbr
            ON abbreviations(abbr)
        """)

        self.connection.commit()

    def close(self):
        """Close database connection"""
        if self.connection:
            self.connection.close()
            self.connection = None

    def __enter__(self):
        """Context manager entry"""
        self.connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        self.close()


def get_database(db_path: str = ":memory:") -> Database:
    """
    Factory function to create and initialize database

    Args:
        db_path: Path to database file or ":memory:"

    Returns:
        Initialized Database instance
    """
    db = Database(db_path)
    db.connect()
    db.initialize_schema()
    return db
