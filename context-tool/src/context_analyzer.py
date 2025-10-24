"""Main context analysis engine"""

import sqlite3
import json
from typing import Dict, List, Any, Optional
from .pattern_matcher import PatternMatcher
from .action_suggester import ActionSuggester


class ContextAnalyzer:
    """Main analysis engine that combines pattern matching, database lookups, and action suggestions"""

    def __init__(
        self,
        db: sqlite3.Connection,
        pattern_matcher: PatternMatcher,
        action_suggester: ActionSuggester,
        semantic_searcher: Optional[Any] = None
    ):
        """
        Initialize context analyzer

        Args:
            db: Database connection
            pattern_matcher: Pattern matcher instance
            action_suggester: Action suggester instance
            semantic_searcher: Optional semantic searcher for similarity matching
        """
        self.db = db
        self.pattern_matcher = pattern_matcher
        self.action_suggester = action_suggester
        self.semantic = semantic_searcher

    def analyze(self, selected_text: str) -> Dict[str, Any]:
        """
        Main analysis entry point

        Args:
            selected_text: Text selected by the user

        Returns:
            Complete context analysis result
        """
        # 1. Detect patterns (deterministic)
        patterns = self.pattern_matcher.detect(selected_text)
        text_type = self.pattern_matcher.get_type(selected_text)

        # 2. Find exact matches in database
        exact_matches = self._find_exact_matches(selected_text)

        # Deduplicate exact matches (type + id or type + data)
        exact_matches = self._dedupe_entities(exact_matches)

        # 2.5. Check for abbreviations (direct hit)
        abbreviation_match = self._find_abbreviation(selected_text)

        # 3. Find semantic matches (LLM-enhanced) if available
        semantic_matches = []
        if self.semantic:
            semantic_matches = self.semantic.find_similar(selected_text, limit=5)

        # 4. Build knowledge graph context
        related_items = self._get_related_items(exact_matches)

        # Deduplicate related items as well
        related_items = self._dedupe_entities(related_items)

        # 5. Generate smart context
        smart_context = self._generate_smart_context(
            selected_text, text_type, exact_matches, related_items, abbreviation_match
        )

        # 6. Suggest actions
        actions = self.action_suggester.suggest_actions(
            selected_text, text_type, exact_matches, patterns
        )

        # 7. Generate insights
        insights = self._generate_insights(exact_matches, related_items)

        return {
            'selected_text': selected_text,
            'detected_type': text_type,
            'patterns': patterns,
            'abbreviation': abbreviation_match,
            'exact_matches': exact_matches,
            'semantic_matches': semantic_matches,
            'related_items': related_items,
            'smart_context': smart_context,
            'actions': actions,
            'insights': insights
        }

    def _find_exact_matches(self, text: str) -> List[Dict]:
        """
        Find exact matches in contacts, snippets, projects

        Args:
            text: Text to search for

        Returns:
            List of matches with type and data
        """
        results = []

        # Search contacts by name or email
        cursor = self.db.execute("""
            SELECT * FROM contacts
            WHERE name LIKE ? OR email LIKE ?
        """, (f'%{text}%', f'%{text}%'))

        for row in cursor.fetchall():
            results.append({
                'type': 'contact',
                'data': self._row_to_dict(row)
            })

        # Search snippets by text or tags
        cursor = self.db.execute("""
            SELECT * FROM snippets
            WHERE text LIKE ? OR tags LIKE ?
        """, (f'%{text}%', f'%{text}%'))

        for row in cursor.fetchall():
            results.append({
                'type': 'snippet',
                'data': self._row_to_dict(row)
            })

        # Search projects by name
        cursor = self.db.execute("""
            SELECT * FROM projects
            WHERE name LIKE ? OR tags LIKE ?
        """, (f'%{text}%', f'%{text}%'))

        for row in cursor.fetchall():
            results.append({
                'type': 'project',
                'data': self._row_to_dict(row)
            })

        return results

    def _find_abbreviation(self, text: str) -> Optional[Dict]:
        """
        Find exact abbreviation match (case-insensitive)

        Args:
            text: Text to check for abbreviation

        Returns:
            Abbreviation data if found, None otherwise
        """
        # Try exact match first (case-insensitive)
        cursor = self.db.execute("""
            SELECT * FROM abbreviations
            WHERE UPPER(abbr) = UPPER(?)
        """, (text.strip(),))

        row = cursor.fetchone()
        if row:
            return self._row_to_dict(row)

        return None

    def _get_related_items(self, matches: List[Dict]) -> List[Dict]:
        """
        Get items related to matches via knowledge graph

        Args:
            matches: Exact matches found

        Returns:
            List of related items
        """
        related = []

        for match in matches:
            match_type = match['type']
            match_id = match['data']['id']

            # Find outgoing relationships
            cursor = self.db.execute("""
                SELECT * FROM relationships
                WHERE from_type = ? AND from_id = ?
            """, (match_type, match_id))

            for rel_row in cursor.fetchall():
                to_type = rel_row['to_type']
                to_id = rel_row['to_id']
                relationship_type = rel_row['relationship_type']

                # Fetch the related entity
                entity = self._fetch_entity(to_type, to_id)
                if entity:
                    related.append({
                        'type': to_type,
                        'data': entity,
                        'relationship': relationship_type,
                        'strength': rel_row['strength']
                    })

            # Find incoming relationships
            cursor = self.db.execute("""
                SELECT * FROM relationships
                WHERE to_type = ? AND to_id = ?
            """, (match_type, match_id))

            for rel_row in cursor.fetchall():
                from_type = rel_row['from_type']
                from_id = rel_row['from_id']
                relationship_type = rel_row['relationship_type']

                # Fetch the related entity
                entity = self._fetch_entity(from_type, from_id)
                if entity:
                    related.append({
                        'type': from_type,
                        'data': entity,
                        'relationship': f'inverse_{relationship_type}',
                        'strength': rel_row['strength']
                    })

        return related

    def _dedupe_entities(self, items: List[Dict]) -> List[Dict]:
        """
        Generic deduplication for lists of entity dicts.

        Prefers unique key of (type, id) when available, otherwise falls back to
        (type, json-serialized-data). Preserves original order.
        """
        seen = set()
        deduped = []

        for item in items:
            typ = item.get('type')
            data = item.get('data', {})
            key = None

            # Prefer numeric id if present
            if isinstance(data, dict) and data.get('id') is not None:
                key = (typ, int(data.get('id')))
            else:
                # Fallback to stable serialization
                try:
                    key = (typ, json.dumps(data, sort_keys=True))
                except Exception:
                    # As a final fallback, use repr
                    key = (typ, repr(data))

            if key not in seen:
                seen.add(key)
                deduped.append(item)

        return deduped

    def _fetch_entity(self, entity_type: str, entity_id: int) -> Optional[Dict]:
        """Fetch an entity by type and ID"""
        table_name = f"{entity_type}s"  # contacts, snippets, projects

        try:
            cursor = self.db.execute(
                f"SELECT * FROM {table_name} WHERE id = ?",
                (entity_id,)
            )
            row = cursor.fetchone()
            return self._row_to_dict(row) if row else None
        except sqlite3.OperationalError:
            return None

    def _generate_smart_context(
        self,
        text: str,
        text_type: Optional[str],
        exact_matches: List[Dict],
        related_items: List[Dict],
        abbreviation: Optional[Dict] = None
    ) -> str:
        """
        Generate human-readable context summary

        Args:
            text: Selected text
            text_type: Detected type
            exact_matches: Exact matches
            related_items: Related items from knowledge graph
            abbreviation: Abbreviation match if found

        Returns:
            Smart context string
        """
        context_parts = []

        # Abbreviation context (highest priority)
        if abbreviation:
            context_parts.append(f"'{abbreviation['abbr']}' stands for {abbreviation['full']}.")
            if abbreviation.get('category'):
                context_parts.append(f"Category: {abbreviation['category']}")
            return ' '.join(context_parts)

        # Type-based context
        if text_type:
            context_parts.append(f"This looks like a {text_type.replace('_', ' ')}.")

        # Contact context
        contacts = [m for m in exact_matches if m['type'] == 'contact']
        if contacts:
            contact = contacts[0]['data']
            parts = []
            if contact.get('role'):
                parts.append(f"{contact['role']}")
            if contact.get('last_contact'):
                parts.append(f"Last contact: {contact['last_contact']}")
            if contact.get('next_event'):
                parts.append(f"Upcoming: {contact['next_event']}")

            if parts:
                context_parts.append(f"{contact['name']}: {', '.join(parts)}")

        # Project context
        projects = [m for m in exact_matches if m['type'] == 'project']
        if projects:
            project = projects[0]['data']
            metadata = json.loads(project.get('metadata', '{}'))

            parts = []
            if project.get('status'):
                parts.append(f"Status: {project['status']}")
            if metadata.get('team_lead'):
                parts.append(f"Lead: {metadata['team_lead']}")

            context_parts.append(f"Project '{project['name']}': {', '.join(parts)}")

        # Related items context
        if related_items:
            related_contacts = [r for r in related_items if r['type'] == 'contact']
            if related_contacts:
                names = [r['data']['name'] for r in related_contacts[:3]]
                context_parts.append(f"Related to: {', '.join(names)}")

        return ' '.join(context_parts) if context_parts else "No additional context found."

    def _generate_insights(
        self,
        exact_matches: List[Dict],
        related_items: List[Dict]
    ) -> List[str]:
        """
        Generate actionable insights

        Args:
            exact_matches: Exact matches
            related_items: Related items

        Returns:
            List of insight strings
        """
        insights = []

        # Check for contacts with upcoming events
        for match in exact_matches:
            if match['type'] == 'contact':
                contact = match['data']
                if contact.get('next_event'):
                    insights.append(
                        f"Upcoming event with {contact['name']}: {contact['next_event']}"
                    )

        # Check for project-related work
        for match in exact_matches:
            if match['type'] == 'snippet':
                snippet = match['data']
                metadata = json.loads(snippet.get('metadata', '{}'))

                linked_projects = metadata.get('linked_projects', [])
                if linked_projects:
                    insights.append(
                        f"This is related to: {', '.join(linked_projects)}"
                    )

        # Knowledge graph insights
        contact_relations = [r for r in related_items if r['type'] == 'contact']
        if len(contact_relations) > 1:
            names = [r['data']['name'] for r in contact_relations[:3]]
            insights.append(f"Multiple people involved: {', '.join(names)}")

        return insights

    def _row_to_dict(self, row: sqlite3.Row) -> Dict:
        """Convert SQLite Row to dictionary"""
        return {key: row[key] for key in row.keys()}
