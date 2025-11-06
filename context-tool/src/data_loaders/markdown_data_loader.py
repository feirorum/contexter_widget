"""Markdown data loader for Obsidian-compatible notes"""

import re
import sqlite3
import json
from pathlib import Path
from typing import Dict, List, Any, Tuple, Optional
from datetime import date, datetime
import yaml


class MarkdownDataLoader:
    """
    Load markdown files with YAML frontmatter into SQLite database

    Supports:
    - YAML frontmatter for metadata
    - Markdown body for content
    - Wikilinks [[Name]] for relationships
    - Organized subdirectories (people/, snippets/, projects/, abbreviations/)
    """

    def __init__(self, db_connection: sqlite3.Connection):
        """
        Initialize markdown loader

        Args:
            db_connection: Active SQLite database connection
        """
        self.db = db_connection
        self.wikilinks_to_resolve = []  # (from_type, from_id, wikilink_text)

    def _serialize_value(self, value: Any) -> Any:
        """
        Convert values to JSON-serializable format

        Args:
            value: Value to convert

        Returns:
            JSON-serializable value
        """
        if isinstance(value, (date, datetime)):
            return value.isoformat()
        elif isinstance(value, dict):
            return {k: self._serialize_value(v) for k, v in value.items()}
        elif isinstance(value, list):
            return [self._serialize_value(v) for v in value]
        else:
            return value

    def load_from_markdown(self, data_dir: Path):
        """
        Load all markdown files into SQLite database

        Args:
            data_dir: Directory containing markdown subdirectories
        """
        data_dir = Path(data_dir)

        print(f"📁 Loading markdown files from: {data_dir.absolute()}")

        # Check if directory exists
        if not data_dir.exists():
            print(f"⚠️  WARNING: Directory {data_dir} does not exist!")
            return

        # Load each type
        people_count = self._load_people(data_dir / "people")
        snippets_count = self._load_snippets(data_dir / "snippets")
        projects_count = self._load_projects(data_dir / "projects")
        abbreviations_count = self._load_abbreviations(data_dir / "abbreviations")

        # Build relationships from wikilinks
        relationships_count = self._resolve_wikilinks()

        self.db.commit()

        print(f"\n📊 Markdown Data Loaded:")
        print(f"  - {people_count} people")
        print(f"  - {snippets_count} snippets")
        print(f"  - {projects_count} projects")
        print(f"  - {abbreviations_count} abbreviations")
        print(f"  - {relationships_count} relationships")

        # Show some examples of what was loaded
        if abbreviations_count > 0:
            cursor = self.db.execute("SELECT abbr FROM abbreviations LIMIT 3")
            abbrs = [row['abbr'] for row in cursor.fetchall()]
            print(f"  - Sample abbreviations: {', '.join(abbrs)}")

        if people_count > 0:
            cursor = self.db.execute("SELECT name FROM contacts LIMIT 3")
            names = [row['name'] for row in cursor.fetchall()]
            print(f"  - Sample people: {', '.join(names)}")

    def parse_markdown_file(self, filepath: Path) -> Tuple[Dict[str, Any], str]:
        """
        Parse markdown file with YAML frontmatter

        Args:
            filepath: Path to markdown file

        Returns:
            Tuple of (frontmatter dict, markdown body)
        """
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()

        # Check for frontmatter (--- at start)
        if not content.startswith('---'):
            # No frontmatter, entire file is body
            return {}, content

        # Split frontmatter and body
        parts = content.split('---', 2)
        if len(parts) < 3:
            # Malformed, treat as no frontmatter
            return {}, content

        frontmatter_text = parts[1].strip()
        body = parts[2].strip()

        # Parse YAML frontmatter
        try:
            frontmatter = yaml.safe_load(frontmatter_text) or {}
        except yaml.YAMLError as e:
            print(f"Warning: Could not parse frontmatter in {filepath}: {e}")
            frontmatter = {}

        return frontmatter, body

    def extract_wikilinks(self, text: str) -> List[str]:
        """
        Extract wikilinks from markdown text

        Args:
            text: Markdown text

        Returns:
            List of wikilink targets (without brackets)
        """
        # Match [[Link]] or [[Link|Display Text]]
        pattern = r'\[\[([^\]|]+)(?:\|[^\]]+)?\]\]'
        matches = re.findall(pattern, text)
        return [m.strip() for m in matches]

    def normalize_name(self, name: str) -> str:
        """
        Normalize a name for matching

        Args:
            name: Raw name

        Returns:
            Normalized name
        """
        # Convert to lowercase, remove extra spaces
        return ' '.join(name.lower().split())

    def _load_people(self, people_dir: Path) -> int:
        """Load people from markdown files"""
        if not people_dir.exists():
            print(f"Warning: {people_dir} not found, skipping")
            return 0

        count = 0
        for md_file in people_dir.glob("*.md"):
            frontmatter, body = self.parse_markdown_file(md_file)

            # Extract name: Priority order:
            # 1. frontmatter 'name' field
            # 2. First markdown header (# Name)
            # 3. Filename as fallback
            name = frontmatter.get('name')
            if not name:
                # Try to extract from first header in markdown
                header_match = re.search(r'^#\s+(.+)$', body, re.MULTILINE)
                if header_match:
                    name = header_match.group(1).strip()
                else:
                    # Fallback to filename
                    name = md_file.stem.replace('-', ' ').title()

            email = frontmatter.get('email')
            role = frontmatter.get('role')
            last_contact = frontmatter.get('last_contact')
            next_event = frontmatter.get('next_event')
            tags = frontmatter.get('tags', [])

            # Everything else goes into metadata
            metadata_fields = {
                k: v for k, v in frontmatter.items()
                if k not in ['type', 'name', 'email', 'role', 'last_contact', 'next_event', 'tags']
            }
            metadata_fields['body'] = body  # Store markdown body

            # Insert into database
            cursor = self.db.execute("""
                INSERT INTO contacts (name, email, role, context, last_contact, next_event, tags, metadata)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                name,
                email,
                role,
                body[:200] if body else None,  # First 200 chars as context
                last_contact,
                next_event,
                json.dumps(self._serialize_value(tags)),
                json.dumps(self._serialize_value(metadata_fields))
            ))

            person_id = cursor.lastrowid

            # Extract wikilinks for later relationship resolution
            wikilinks = self.extract_wikilinks(body)
            wikilinks += self.extract_wikilinks(str(frontmatter))
            for link in wikilinks:
                self.wikilinks_to_resolve.append(('contact', person_id, link))

            count += 1

        return count

    def _load_snippets(self, snippets_dir: Path) -> int:
        """Load snippets from markdown files"""
        if not snippets_dir.exists():
            print(f"Warning: {snippets_dir} not found, skipping")
            return 0

        count = 0
        for md_file in snippets_dir.glob("*.md"):
            frontmatter, body = self.parse_markdown_file(md_file)

            # Extract fields
            saved_date = frontmatter.get('date', frontmatter.get('created'))
            source = frontmatter.get('source')
            tags = frontmatter.get('tags', [])

            # Use first heading or filename as title
            title_match = re.search(r'^#\s+(.+)$', body, re.MULTILINE)
            title = title_match.group(1) if title_match else md_file.stem.replace('-', ' ').title()

            # Everything else goes into metadata
            metadata_fields = {
                k: v for k, v in frontmatter.items()
                if k not in ['type', 'date', 'created', 'source', 'tags', 'text']
            }
            metadata_fields['body'] = body
            metadata_fields['title'] = title

            # Insert into database
            cursor = self.db.execute("""
                INSERT INTO snippets (text, saved_date, tags, source, metadata)
                VALUES (?, ?, ?, ?, ?)
            """, (
                body,
                str(saved_date) if saved_date else None,
                json.dumps(self._serialize_value(tags)),
                source,
                json.dumps(self._serialize_value(metadata_fields))
            ))

            snippet_id = cursor.lastrowid

            # Extract wikilinks
            wikilinks = self.extract_wikilinks(body)
            wikilinks += self.extract_wikilinks(str(frontmatter))
            for link in wikilinks:
                self.wikilinks_to_resolve.append(('snippet', snippet_id, link))

            count += 1

        return count

    def _load_projects(self, projects_dir: Path) -> int:
        """Load projects from markdown files"""
        if not projects_dir.exists():
            print(f"Warning: {projects_dir} not found, skipping")
            return 0

        count = 0
        for md_file in projects_dir.glob("*.md"):
            frontmatter, body = self.parse_markdown_file(md_file)

            # Extract fields
            name = frontmatter.get('name') or md_file.stem.replace('-', ' ').title()
            status = frontmatter.get('status')
            tags = frontmatter.get('tags', [])

            # Use first paragraph or first 200 chars as description
            description = body[:200] if len(body) <= 200 else body[:197] + "..."

            # Everything else goes into metadata
            metadata_fields = {
                k: v for k, v in frontmatter.items()
                if k not in ['type', 'name', 'status', 'description', 'tags']
            }
            metadata_fields['body'] = body

            # Insert into database
            cursor = self.db.execute("""
                INSERT INTO projects (name, status, description, tags, metadata)
                VALUES (?, ?, ?, ?, ?)
            """, (
                name,
                status,
                description,
                json.dumps(self._serialize_value(tags)),
                json.dumps(self._serialize_value(metadata_fields))
            ))

            project_id = cursor.lastrowid

            # Extract wikilinks
            wikilinks = self.extract_wikilinks(body)
            wikilinks += self.extract_wikilinks(str(frontmatter))
            for link in wikilinks:
                self.wikilinks_to_resolve.append(('project', project_id, link))

            count += 1

        return count

    def _load_abbreviations(self, abbr_dir: Path) -> int:
        """Load abbreviations from markdown files (recursive)"""
        if not abbr_dir.exists():
            print(f"Warning: {abbr_dir} not found, skipping")
            return 0

        count = 0
        # Find all .md files recursively in abbreviations directory
        for md_file in abbr_dir.rglob("*.md"):
            frontmatter, body = self.parse_markdown_file(md_file)

            # Extract abbreviation from frontmatter or filename
            abbr = frontmatter.get('abbr')
            if not abbr:
                # Try to extract from filename
                abbr = md_file.stem.upper()

            # Extract full form from first heading or frontmatter
            full = frontmatter.get('full')
            if not full:
                # Try to extract from first heading: "# ABBR - Full Form"
                heading_match = re.search(r'^#\s+\w+\s*-\s*(.+)$', body, re.MULTILINE)
                if heading_match:
                    full = heading_match.group(1).strip()

            category = frontmatter.get('category', 'General')
            examples = frontmatter.get('examples', [])
            related = frontmatter.get('related', [])
            links = frontmatter.get('links', [])

            # Use body as definition
            definition = body

            # Everything else goes into metadata
            metadata_fields = {
                k: v for k, v in frontmatter.items()
                if k not in ['type', 'abbr', 'full', 'category', 'examples', 'related', 'links', 'definition']
            }
            metadata_fields['body'] = body

            # Insert into database
            cursor = self.db.execute("""
                INSERT INTO abbreviations (abbr, full, definition, category, examples, related, links, metadata)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                abbr,
                full,
                definition,
                category,
                json.dumps(self._serialize_value(examples)),
                json.dumps(self._serialize_value(related)),
                json.dumps(self._serialize_value(links)),
                json.dumps(self._serialize_value(metadata_fields))
            ))

            abbr_id = cursor.lastrowid

            # Extract wikilinks (for related concepts)
            wikilinks = self.extract_wikilinks(body)
            wikilinks += self.extract_wikilinks(str(frontmatter))
            # Also add explicit related items
            wikilinks += [r.strip('[]') for r in related if isinstance(r, str) and r.startswith('[')]

            for link in wikilinks:
                self.wikilinks_to_resolve.append(('abbreviation', abbr_id, link))

            count += 1

        return count

    def _resolve_wikilinks(self) -> int:
        """
        Resolve wikilinks to create relationships

        Returns:
            Number of relationships created
        """
        count = 0

        for from_type, from_id, link_text in self.wikilinks_to_resolve:
            # Try to find the target entity
            target_type, target_id = self._find_entity_by_name(link_text)

            if target_type and target_id:
                # Create relationship
                try:
                    self.db.execute("""
                        INSERT INTO relationships
                        (from_type, from_id, to_type, to_id, relationship_type, strength)
                        VALUES (?, ?, ?, ?, ?, ?)
                    """, (from_type, from_id, target_type, target_id, 'wikilink', 1.0))
                    count += 1
                except sqlite3.IntegrityError:
                    # Duplicate relationship, skip
                    pass

        return count

    def _find_entity_by_name(self, name: str) -> Tuple[Optional[str], Optional[int]]:
        """
        Find an entity by name across all tables

        Args:
            name: Name to search for

        Returns:
            Tuple of (entity_type, entity_id) or (None, None)
        """
        normalized = self.normalize_name(name)

        # Search contacts
        cursor = self.db.execute("""
            SELECT id FROM contacts
            WHERE LOWER(REPLACE(name, ' ', '')) = ?
        """, (normalized.replace(' ', ''),))
        row = cursor.fetchone()
        if row:
            return 'contact', row['id']

        # Search projects
        cursor = self.db.execute("""
            SELECT id FROM projects
            WHERE LOWER(REPLACE(name, ' ', '')) = ?
        """, (normalized.replace(' ', ''),))
        row = cursor.fetchone()
        if row:
            return 'project', row['id']

        # Search abbreviations
        cursor = self.db.execute("""
            SELECT id FROM abbreviations
            WHERE UPPER(abbr) = ? OR LOWER(REPLACE(COALESCE(full, ''), ' ', '')) = ?
        """, (name.upper(), normalized.replace(' ', '')))
        row = cursor.fetchone()
        if row:
            return 'abbreviation', row['id']

        # Not found
        return None, None


def load_markdown_data(db_connection: sqlite3.Connection, data_dir: Path):
    """
    Convenience function to load all markdown data

    Args:
        db_connection: Active SQLite database connection
        data_dir: Directory containing markdown subdirectories
    """
    loader = MarkdownDataLoader(db_connection)
    loader.load_from_markdown(data_dir)
