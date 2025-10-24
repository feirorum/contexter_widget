"""Smart saver module for Context Tool - detects entity types and saves as markdown"""

import re
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Tuple, Optional


class EntitySaver:
    """
    Smart saver that detects entity types and saves to appropriate markdown files

    Features:
    - Auto-detects person info (two uppercase words pattern)
    - Detects abbreviations (uppercase acronyms)
    - Detects email addresses
    - Suggests appropriate save types
    - Saves to markdown format with frontmatter
    - Logs all save actions
    """

    def __init__(self, data_dir: Path, log_file: Optional[Path] = None):
        """
        Initialize entity saver

        Args:
            data_dir: Base directory for data (e.g., data-md/)
            log_file: Path to log file (default: data_dir/saves.log)
        """
        self.data_dir = Path(data_dir)
        self.log_file = log_file or (self.data_dir / "saves.log")

        # Ensure directories exist
        self.people_dir = self.data_dir / "people"
        self.snippets_dir = self.data_dir / "snippets"
        self.projects_dir = self.data_dir / "projects"
        self.abbreviations_dir = self.data_dir / "abbreviations" / "custom"

        self._ensure_directories()

        # Log where saves will be recorded
        print(f"💾 Saves will be logged to: {self.log_file.absolute()}")

    def _ensure_directories(self):
        """Create necessary directories if they don't exist"""
        self.people_dir.mkdir(parents=True, exist_ok=True)
        self.snippets_dir.mkdir(parents=True, exist_ok=True)
        self.projects_dir.mkdir(parents=True, exist_ok=True)
        self.abbreviations_dir.mkdir(parents=True, exist_ok=True)

    def detect_entity_type(self, text: str) -> List[Tuple[str, float, str]]:
        """
        Detect possible entity types from text

        Args:
            text: Text to analyze

        Returns:
            List of (type, confidence, reason) tuples, sorted by confidence
        """
        detections = []

        # Detect person name (two or more capitalized words)
        person_confidence, person_reason = self._detect_person(text)
        if person_confidence > 0:
            detections.append(('person', person_confidence, person_reason))

        # Detect abbreviation (uppercase acronym)
        abbr_confidence, abbr_reason = self._detect_abbreviation(text)
        if abbr_confidence > 0:
            detections.append(('abbreviation', abbr_confidence, abbr_reason))

        # Detect email address
        email_confidence, email_reason = self._detect_email(text)
        if email_confidence > 0:
            detections.append(('person', email_confidence, email_reason))

        # Default to snippet if nothing else detected
        if not detections:
            detections.append(('snippet', 1.0, 'No specific pattern detected'))

        # Sort by confidence (highest first)
        detections.sort(key=lambda x: x[1], reverse=True)

        return detections

    def _detect_person(self, text: str) -> Tuple[float, str]:
        """
        Detect if text looks like a person name

        Returns:
            (confidence, reason) tuple
        """
        # Pattern: Two or more capitalized words
        # Examples: "John Doe", "Sarah Mitchell", "Dr. Jane Smith"
        pattern = r'\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)+\b'
        matches = re.findall(pattern, text)

        if matches:
            # Higher confidence if it's the entire text (not just part of it)
            if len(text.strip().split()) <= 4 and matches[0] == text.strip():
                return (0.9, f"Found name pattern: '{matches[0]}' (full match)")
            else:
                return (0.6, f"Found name pattern: '{matches[0]}'")

        return (0.0, "No name pattern detected")

    def _detect_abbreviation(self, text: str) -> Tuple[float, str]:
        """
        Detect if text looks like an abbreviation

        Returns:
            (confidence, reason) tuple
        """
        text_clean = text.strip()

        # Pattern: 2-6 uppercase letters, possibly with numbers
        if re.match(r'^[A-Z]{2,6}[0-9]*$', text_clean):
            return (0.8, f"Uppercase acronym pattern: '{text_clean}'")

        # Pattern: Acronym with dots (e.g., "U.S.A.")
        if re.match(r'^([A-Z]\.){2,}$', text_clean):
            return (0.8, f"Dotted acronym pattern: '{text_clean}'")

        return (0.0, "No abbreviation pattern detected")

    def _detect_email(self, text: str) -> Tuple[float, str]:
        """
        Detect if text contains an email address

        Returns:
            (confidence, reason) tuple
        """
        email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        matches = re.findall(email_pattern, text)

        if matches:
            return (0.95, f"Email address detected: '{matches[0]}'")

        return (0.0, "No email detected")

    def save_as_person(
        self,
        text: str,
        name: Optional[str] = None,
        email: Optional[str] = None,
        additional_info: Optional[Dict] = None
    ) -> Path:
        """
        Save text as a person markdown file

        Args:
            text: Original text that was saved
            name: Person's name (extracted from text if not provided)
            email: Person's email (extracted from text if not provided)
            additional_info: Additional metadata

        Returns:
            Path to created file
        """
        # Extract name if not provided
        if not name:
            name_match = re.search(r'\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)+\b', text)
            name = name_match.group(0) if name_match else "Unknown Person"

        # Extract email if not provided
        if not email:
            email_match = re.search(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', text)
            email = email_match.group(0) if email_match else None

        # Create filename from name
        filename = name.lower().replace(' ', '-')
        filename = re.sub(r'[^a-z0-9-]', '', filename)
        filepath = self.people_dir / f"{filename}.md"

        # If file exists, append number
        counter = 1
        while filepath.exists():
            filepath = self.people_dir / f"{filename}-{counter}.md"
            counter += 1

        # Build frontmatter
        frontmatter = {
            'type': 'person',
            'created': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'source': 'saved_from_clipboard'
        }

        if email:
            frontmatter['email'] = email

        if additional_info:
            frontmatter.update(additional_info)

        # Build markdown content
        content = self._build_markdown(
            title=name,
            frontmatter=frontmatter,
            body=f"## Notes\n\n{text}\n\n## Related\n\n- Add related items here\n"
        )

        # Write file
        filepath.write_text(content, encoding='utf-8')

        # Log the save
        self._log_save(
            save_type='person',
            filepath=filepath,
            reason=f"Detected person name: {name}",
            original_text=text[:100]
        )

        return filepath

    def save_as_snippet(
        self,
        text: str,
        tags: Optional[List[str]] = None,
        source: Optional[str] = None,
        additional_info: Optional[Dict] = None
    ) -> Path:
        """
        Save text as a snippet markdown file

        Args:
            text: Text to save
            tags: Optional tags
            source: Source of the snippet
            additional_info: Additional metadata

        Returns:
            Path to created file
        """
        # Create filename from date and first few words
        date_str = datetime.now().strftime('%Y-%m-%d')
        first_words = '-'.join(text.split()[:3])
        first_words = re.sub(r'[^a-z0-9-]', '', first_words.lower())
        filename = f"{date_str}-{first_words}"
        filepath = self.snippets_dir / f"{filename}.md"

        # If file exists, append time
        if filepath.exists():
            time_str = datetime.now().strftime('%H%M%S')
            filepath = self.snippets_dir / f"{filename}-{time_str}.md"

        # Build frontmatter
        frontmatter = {
            'type': 'snippet',
            'date': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'source': source or 'clipboard',
            'tags': tags or []
        }

        if additional_info:
            frontmatter.update(additional_info)

        # Build markdown content
        # Extract first line as title if available
        lines = text.strip().split('\n')
        if len(lines) > 1:
            title = lines[0][:50]
            body = '\n'.join(lines[1:])
        else:
            title = text[:50]
            body = text

        content = self._build_markdown(
            title=f"Saved Snippet - {title}",
            frontmatter=frontmatter,
            body=f"{body}\n\n## Related\n\n- Add related items here\n"
        )

        # Write file
        filepath.write_text(content, encoding='utf-8')

        # Log the save
        self._log_save(
            save_type='snippet',
            filepath=filepath,
            reason="Default save as snippet",
            original_text=text[:100]
        )

        return filepath

    def save_as_abbreviation(
        self,
        text: str,
        full_form: Optional[str] = None,
        category: str = "Custom",
        additional_info: Optional[Dict] = None
    ) -> Path:
        """
        Save text as an abbreviation markdown file

        Args:
            text: Abbreviation text
            full_form: Full form of abbreviation
            category: Category (default: Custom)
            additional_info: Additional metadata

        Returns:
            Path to created file
        """
        abbr = text.strip().upper()
        filename = abbr.lower()
        filepath = self.abbreviations_dir / f"{filename}.md"

        # If file exists, append number
        counter = 1
        while filepath.exists():
            filepath = self.abbreviations_dir / f"{filename}-{counter}.md"
            counter += 1

        # Build frontmatter
        frontmatter = {
            'type': 'abbreviation',
            'abbr': abbr,
            'category': category,
            'created': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'source': 'saved_from_clipboard'
        }

        if full_form:
            frontmatter['full'] = full_form

        if additional_info:
            frontmatter.update(additional_info)

        # Build markdown content
        title = f"{abbr}"
        if full_form:
            title += f" - {full_form}"

        content = self._build_markdown(
            title=title,
            frontmatter=frontmatter,
            body=f"## Definition\n\nAdd definition here.\n\n## Usage\n\nAdd usage examples.\n\n## Related\n\n- Add related abbreviations\n"
        )

        # Write file
        filepath.write_text(content, encoding='utf-8')

        # Log the save
        self._log_save(
            save_type='abbreviation',
            filepath=filepath,
            reason=f"Detected abbreviation pattern: {abbr}",
            original_text=text[:100]
        )

        return filepath

    def save_as_project(
        self,
        text: str,
        name: Optional[str] = None,
        status: str = "planning",
        additional_info: Optional[Dict] = None
    ) -> Path:
        """
        Save text as a project markdown file

        Args:
            text: Text to save
            name: Project name
            status: Project status
            additional_info: Additional metadata

        Returns:
            Path to created file
        """
        # Extract name from text if not provided
        if not name:
            first_line = text.strip().split('\n')[0]
            name = first_line[:50] if first_line else "New Project"

        # Create filename
        filename = name.lower().replace(' ', '-')
        filename = re.sub(r'[^a-z0-9-]', '', filename)
        filepath = self.projects_dir / f"{filename}.md"

        # If file exists, append number
        counter = 1
        while filepath.exists():
            filepath = self.projects_dir / f"{filename}-{counter}.md"
            counter += 1

        # Build frontmatter
        frontmatter = {
            'type': 'project',
            'status': status,
            'created': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'source': 'saved_from_clipboard',
            'tags': []
        }

        if additional_info:
            frontmatter.update(additional_info)

        # Build markdown content
        content = self._build_markdown(
            title=name,
            frontmatter=frontmatter,
            body=f"## Description\n\n{text}\n\n## Status\n\nStatus: {status}\n\n## Related\n\n- Add team members\n- Add technologies\n"
        )

        # Write file
        filepath.write_text(content, encoding='utf-8')

        # Log the save
        self._log_save(
            save_type='project',
            filepath=filepath,
            reason="Saved as project",
            original_text=text[:100]
        )

        return filepath

    def _build_markdown(self, title: str, frontmatter: Dict, body: str) -> str:
        """
        Build markdown file content with frontmatter

        Args:
            title: Title for the markdown file
            frontmatter: Frontmatter dictionary
            body: Markdown body content

        Returns:
            Complete markdown file content
        """
        import yaml

        # Build frontmatter
        frontmatter_yaml = yaml.dump(frontmatter, default_flow_style=False, allow_unicode=True)

        # Build complete content
        content = f"---\n{frontmatter_yaml}---\n\n# {title}\n\n{body}"

        return content

    def _log_save(self, save_type: str, filepath: Path, reason: str, original_text: str):
        """
        Log a save action

        Args:
            save_type: Type of entity saved
            filepath: Path where file was saved
            reason: Reason for choosing this type
            original_text: Original text (truncated)
        """
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        log_entry = {
            'timestamp': timestamp,
            'type': save_type,
            'file': str(filepath.relative_to(self.data_dir)),
            'reason': reason,
            'text_preview': original_text[:80] + ('...' if len(original_text) > 80 else '')
        }

        # Append to log file
        with open(self.log_file, 'a', encoding='utf-8') as f:
            # Write as JSON line
            f.write(json.dumps(log_entry) + '\n')

        print(f"📝 Saved as {save_type}: {filepath.name}")
        print(f"   Reason: {reason}")


def get_save_choices(text: str, saver: EntitySaver) -> List[Dict[str, str]]:
    """
    Get save choices for text based on detected patterns

    Args:
        text: Text to analyze
        saver: EntitySaver instance

    Returns:
        List of choice dictionaries with 'type', 'label', 'confidence', 'reason'
    """
    detections = saver.detect_entity_type(text)

    choices = []

    # Add detected types (if confidence > 0.5)
    for entity_type, confidence, reason in detections:
        if confidence >= 0.5:
            label_map = {
                'person': '👤 Save as Person',
                'abbreviation': '📖 Save as Abbreviation',
                'project': '📁 Save as Project',
                'snippet': '📝 Save as Snippet'
            }

            choices.append({
                'type': entity_type,
                'label': label_map.get(entity_type, f'Save as {entity_type.title()}'),
                'confidence': confidence,
                'reason': reason
            })

    # Always include snippet as fallback
    if not any(c['type'] == 'snippet' for c in choices):
        choices.append({
            'type': 'snippet',
            'label': '📝 Save as Snippet',
            'confidence': 0.5,
            'reason': 'Default option'
        })

    return choices


class SmartSaver:
    """
    Wrapper for EntitySaver that provides a simple interface for widget callbacks

    This class is designed to be passed as the on_save_snippet callback to the widget.
    """

    def __init__(self, data_dir: Path, log_file: Optional[Path] = None):
        """
        Initialize smart saver

        Args:
            data_dir: Base directory for data
            log_file: Path to log file
        """
        self.saver = EntitySaver(data_dir, log_file)

    def get_save_choices(self, text: str) -> List[Dict[str, str]]:
        """Get save choices for text"""
        return get_save_choices(text, self.saver)

    def save(self, text: str, save_type: str) -> Optional[Path]:
        """
        Save text as specified type

        Args:
            text: Text to save
            save_type: Type to save as ('person', 'snippet', 'abbreviation', 'project')

        Returns:
            Path to saved file
        """
        if save_type == 'person':
            return self.saver.save_as_person(text)
        elif save_type == 'abbreviation':
            return self.saver.save_as_abbreviation(text)
        elif save_type == 'project':
            return self.saver.save_as_project(text)
        else:  # Default to snippet
            return self.saver.save_as_snippet(text)

    def __call__(self, text: str):
        """
        Allow SmartSaver to be called as a function (for backward compatibility)

        Args:
            text: Text to save (defaults to snippet)
        """
        return self.save(text, 'snippet')
