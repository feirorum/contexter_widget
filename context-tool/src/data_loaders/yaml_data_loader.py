"""YAML data loader for the Context Tool"""

import yaml
import sqlite3
import json
from pathlib import Path
from typing import Optional, Dict, List, Any


class YAMLDataLoader:
    """Load YAML data files into SQLite database"""

    def __init__(self, db_connection: sqlite3.Connection):
        """
        Initialize data loader

        Args:
            db_connection: Active SQLite database connection
        """
        self.db = db_connection

    def load_from_yaml(self, data_dir: Path):
        """
        Load all YAML files into SQLite database

        Args:
            data_dir: Directory containing YAML data files
        """
        data_dir = Path(data_dir)

        # Load data files
        self._load_contacts(data_dir / "contacts.yaml")
        self._load_snippets(data_dir / "snippets.yaml")
        self._load_projects(data_dir / "projects.yaml")
        self._load_abbreviations(data_dir / "abbreviations.yaml")

        # Build relationships based on linked data
        self._build_relationships()

        self.db.commit()

    def _load_contacts(self, filepath: Path):
        """Load contacts from YAML file"""
        if not filepath.exists():
            print(f"Warning: {filepath} not found, skipping")
            return

        with open(filepath) as f:
            data = yaml.safe_load(f)

            if not data or 'contacts' not in data:
                print(f"Warning: No contacts found in {filepath}")
                return

            for contact in data['contacts']:
                # Extract standard fields
                name = contact.get('name')
                email = contact.get('email')
                role = contact.get('role')
                context = contact.get('context')
                last_contact = contact.get('last_contact')
                next_event = contact.get('next_event')
                tags = contact.get('tags', [])

                # Everything else goes into metadata
                metadata_fields = {
                    k: v for k, v in contact.items()
                    if k not in ['name', 'email', 'role', 'context',
                                 'last_contact', 'next_event', 'tags']
                }

                self.db.execute("""
                    INSERT INTO contacts (name, email, role, context,
                                         last_contact, next_event, tags, metadata)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    name,
                    email,
                    role,
                    context,
                    last_contact,
                    next_event,
                    json.dumps(tags),
                    json.dumps(metadata_fields)
                ))

        print(f"Loaded {len(data['contacts'])} contacts")

    def _load_snippets(self, filepath: Path):
        """Load snippets from YAML file"""
        if not filepath.exists():
            print(f"Warning: {filepath} not found, skipping")
            return

        with open(filepath) as f:
            data = yaml.safe_load(f)

            if not data or 'snippets' not in data:
                print(f"Warning: No snippets found in {filepath}")
                return

            for snippet in data['snippets']:
                # Extract standard fields
                text = snippet.get('text')
                saved_date = snippet.get('saved_date')
                tags = snippet.get('tags', [])
                source = snippet.get('source')

                # Everything else goes into metadata
                metadata_fields = {
                    k: v for k, v in snippet.items()
                    if k not in ['text', 'saved_date', 'tags', 'source']
                }

                self.db.execute("""
                    INSERT INTO snippets (text, saved_date, tags, source, metadata)
                    VALUES (?, ?, ?, ?, ?)
                """, (
                    text,
                    saved_date,
                    json.dumps(tags),
                    source,
                    json.dumps(metadata_fields)
                ))

        print(f"Loaded {len(data['snippets'])} snippets")

    def _load_projects(self, filepath: Path):
        """Load projects from YAML file"""
        if not filepath.exists():
            print(f"Warning: {filepath} not found, skipping")
            return

        with open(filepath) as f:
            data = yaml.safe_load(f)

            if not data or 'projects' not in data:
                print(f"Warning: No projects found in {filepath}")
                return

            for project in data['projects']:
                # Extract standard fields
                name = project.get('name')
                status = project.get('status')
                description = project.get('description')
                tags = project.get('tags', [])

                # Everything else goes into metadata
                metadata_fields = {
                    k: v for k, v in project.items()
                    if k not in ['name', 'status', 'description', 'tags']
                }

                self.db.execute("""
                    INSERT INTO projects (name, status, description, tags, metadata)
                    VALUES (?, ?, ?, ?, ?)
                """, (
                    name,
                    status,
                    description,
                    json.dumps(tags),
                    json.dumps(metadata_fields)
                ))

        print(f"Loaded {len(data['projects'])} projects")

    def _load_abbreviations(self, filepath: Path):
        """Load abbreviations from YAML file"""
        if not filepath.exists():
            print(f"Warning: {filepath} not found, skipping")
            return

        with open(filepath) as f:
            data = yaml.safe_load(f)

            if not data or 'abbreviations' not in data:
                print(f"Warning: No abbreviations found in {filepath}")
                return

            for abbr_entry in data['abbreviations']:
                # Extract standard fields
                abbr = abbr_entry.get('abbr')
                full = abbr_entry.get('full')
                definition = abbr_entry.get('definition')
                category = abbr_entry.get('category')
                examples = abbr_entry.get('examples', [])
                related = abbr_entry.get('related', [])
                links = abbr_entry.get('links', [])

                # Everything else goes into metadata
                metadata_fields = {
                    k: v for k, v in abbr_entry.items()
                    if k not in ['abbr', 'full', 'definition', 'category', 'examples', 'related', 'links']
                }

                self.db.execute("""
                    INSERT INTO abbreviations (abbr, full, definition, category, examples, related, links, metadata)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    abbr,
                    full,
                    definition,
                    category,
                    json.dumps(examples),
                    json.dumps(related),
                    json.dumps(links),
                    json.dumps(metadata_fields)
                ))

        print(f"Loaded {len(data['abbreviations'])} abbreviations")

    def _build_relationships(self):
        """
        Build relationships based on linked data in metadata

        This creates edges in the knowledge graph by examining:
        - Snippets linked to contacts
        - Snippets linked to projects
        - Projects linked to contacts (team_lead)
        """
        # Link snippets to contacts
        cursor = self.db.execute("SELECT id, metadata FROM snippets")
        for row in cursor.fetchall():
            snippet_id = row['id']
            metadata = json.loads(row['metadata']) if row['metadata'] else {}

            # Check for linked_contacts
            linked_contacts = metadata.get('linked_contacts', [])
            for contact_name in linked_contacts:
                # Find contact ID by name
                contact_row = self.db.execute(
                    "SELECT id FROM contacts WHERE name = ?",
                    (contact_name,)
                ).fetchone()

                if contact_row:
                    self.db.execute("""
                        INSERT INTO relationships
                        (from_type, from_id, to_type, to_id, relationship_type, strength)
                        VALUES (?, ?, ?, ?, ?, ?)
                    """, ('snippet', snippet_id, 'contact', contact_row['id'], 'mentions', 1.0))

            # Check for linked_projects
            linked_projects = metadata.get('linked_projects', [])
            for project_name in linked_projects:
                # Find project ID by name
                project_row = self.db.execute(
                    "SELECT id FROM projects WHERE name = ?",
                    (project_name,)
                ).fetchone()

                if project_row:
                    self.db.execute("""
                        INSERT INTO relationships
                        (from_type, from_id, to_type, to_id, relationship_type, strength)
                        VALUES (?, ?, ?, ?, ?, ?)
                    """, ('snippet', snippet_id, 'project', project_row['id'], 'related_to', 1.0))

        # Link projects to contacts (team_lead)
        cursor = self.db.execute("SELECT id, metadata FROM projects")
        for row in cursor.fetchall():
            project_id = row['id']
            metadata = json.loads(row['metadata']) if row['metadata'] else {}

            team_lead = metadata.get('team_lead')
            if team_lead:
                contact_row = self.db.execute(
                    "SELECT id FROM contacts WHERE name = ?",
                    (team_lead,)
                ).fetchone()

                if contact_row:
                    self.db.execute("""
                        INSERT INTO relationships
                        (from_type, from_id, to_type, to_id, relationship_type, strength)
                        VALUES (?, ?, ?, ?, ?, ?)
                    """, ('project', project_id, 'contact', contact_row['id'], 'led_by', 1.0))

        # Count relationships created
        count = self.db.execute("SELECT COUNT(*) as count FROM relationships").fetchone()['count']
        print(f"Built {count} relationships")


def load_yaml_data(db_connection: sqlite3.Connection, data_dir: Path):
    """
    Convenience function to load all YAML data

    Args:
        db_connection: Active SQLite database connection
        data_dir: Directory containing YAML data files
    """
    loader = YAMLDataLoader(db_connection)
    loader.load_from_yaml(data_dir)
