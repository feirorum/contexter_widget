"""Favourites manager for project markdown files"""

import re
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple


class FavouritesManager:
    """
    Manage favourites section in project markdown files

    Handles parsing and updating the "## Favourites" section in project files
    """

    def __init__(self, data_dir: Path):
        """
        Initialize favourites manager

        Args:
            data_dir: Base data directory (contains projects/ subdirectory)
        """
        self.data_dir = Path(data_dir)
        self.projects_dir = self.data_dir / "projects"

    def get_project_file(self, project_name: str) -> Optional[Path]:
        """
        Find the markdown file for a project by name

        Args:
            project_name: Name of the project

        Returns:
            Path to project file, or None if not found
        """
        if not self.projects_dir.exists():
            return None

        # Try exact match with slugified name
        slug = project_name.lower().replace(' ', '-')
        exact_path = self.projects_dir / f"{slug}.md"
        if exact_path.exists():
            return exact_path

        # Search all project files for matching name
        for md_file in self.projects_dir.glob("*.md"):
            # Read and check if this is the right project
            try:
                with open(md_file, 'r', encoding='utf-8') as f:
                    content = f.read()

                # Check frontmatter for name field
                if content.startswith('---'):
                    parts = content.split('---', 2)
                    if len(parts) >= 3:
                        import yaml
                        try:
                            frontmatter = yaml.safe_load(parts[1].strip()) or {}
                            if frontmatter.get('name', '').lower() == project_name.lower():
                                return md_file
                        except yaml.YAMLError:
                            pass

                # Check first heading
                header_match = re.search(r'^#\s+(.+)$', content, re.MULTILINE)
                if header_match:
                    if header_match.group(1).strip().lower() == project_name.lower():
                        return md_file

            except Exception:
                continue

        return None

    def parse_favourites(self, project_name: str) -> List[str]:
        """
        Extract favourites from project markdown file

        Args:
            project_name: Name of the project

        Returns:
            List of wikilink names (without brackets)
        """
        project_file = self.get_project_file(project_name)
        if not project_file:
            return []

        try:
            with open(project_file, 'r', encoding='utf-8') as f:
                content = f.read()

            # Find the Favourites section
            # Match: ## Favourites (case insensitive, with or without trailing content)
            favourites_match = re.search(
                r'^##\s+Favourites?\s*$.*?(?=^##\s+|\Z)',
                content,
                re.MULTILINE | re.DOTALL | re.IGNORECASE
            )

            if not favourites_match:
                return []

            favourites_section = favourites_match.group(0)

            # Extract wikilinks from this section
            wikilink_pattern = r'\[\[([^\]|]+)(?:\|[^\]]+)?\]\]'
            matches = re.findall(wikilink_pattern, favourites_section)

            return [m.strip() for m in matches]

        except Exception as e:
            print(f"Error parsing favourites from {project_file}: {e}")
            return []

    def update_favourites(self, project_name: str, favourites: List[str]) -> bool:
        """
        Update the favourites section in a project markdown file

        Args:
            project_name: Name of the project
            favourites: List of wikilink names to set as favourites

        Returns:
            True if successful, False otherwise
        """
        project_file = self.get_project_file(project_name)
        if not project_file:
            print(f"Project file not found for: {project_name}")
            return False

        try:
            with open(project_file, 'r', encoding='utf-8') as f:
                content = f.read()

            # Build new favourites section
            favourites_lines = ["## Favourites\n"]
            for fav in favourites:
                favourites_lines.append(f"- [[{fav}]]\n")

            new_favourites_section = "\n" + "".join(favourites_lines)

            # Check if Favourites section exists
            favourites_match = re.search(
                r'^##\s+Favourites?\s*$.*?(?=^##\s+|\Z)',
                content,
                re.MULTILINE | re.DOTALL | re.IGNORECASE
            )

            if favourites_match:
                # Replace existing section
                new_content = (
                    content[:favourites_match.start()] +
                    new_favourites_section.strip() +
                    "\n\n" +
                    content[favourites_match.end():].lstrip()
                )
            else:
                # Append new section at the end
                new_content = content.rstrip() + "\n\n" + new_favourites_section.strip() + "\n"

            # Write back to file
            with open(project_file, 'w', encoding='utf-8') as f:
                f.write(new_content)

            return True

        except Exception as e:
            print(f"Error updating favourites in {project_file}: {e}")
            return False

    def add_favourite(self, project_name: str, favourite: str) -> bool:
        """
        Add a single favourite to a project

        Args:
            project_name: Name of the project
            favourite: Wikilink name to add

        Returns:
            True if successful, False otherwise
        """
        current_favourites = self.parse_favourites(project_name)
        if favourite not in current_favourites:
            current_favourites.append(favourite)
            return self.update_favourites(project_name, current_favourites)
        return True  # Already exists

    def remove_favourite(self, project_name: str, favourite: str) -> bool:
        """
        Remove a single favourite from a project

        Args:
            project_name: Name of the project
            favourite: Wikilink name to remove

        Returns:
            True if successful, False otherwise
        """
        current_favourites = self.parse_favourites(project_name)
        if favourite in current_favourites:
            current_favourites.remove(favourite)
            return self.update_favourites(project_name, current_favourites)
        return True  # Already doesn't exist

    def parse_window_title_patterns(self, project_name: str) -> List[str]:
        """
        Extract window title patterns from project markdown file

        Looks for patterns in:
        1. "## Window Title Patterns" section (list of regex patterns)
        2. Frontmatter "window_patterns" field
        3. If none found, returns default pattern: .*{project_name}.*

        Args:
            project_name: Name of the project

        Returns:
            List of regex patterns for matching window titles
        """
        project_file = self.get_project_file(project_name)
        if not project_file:
            # Default pattern: match project name anywhere in title
            return [f".*{re.escape(project_name)}.*"]

        try:
            with open(project_file, 'r', encoding='utf-8') as f:
                content = f.read()

            patterns = []

            # 1. Check frontmatter for window_patterns field
            if content.startswith('---'):
                parts = content.split('---', 2)
                if len(parts) >= 3:
                    import yaml
                    try:
                        frontmatter = yaml.safe_load(parts[1].strip()) or {}
                        window_patterns = frontmatter.get('window_patterns', [])
                        if isinstance(window_patterns, list):
                            patterns.extend(window_patterns)
                        elif isinstance(window_patterns, str):
                            patterns.append(window_patterns)
                    except yaml.YAMLError:
                        pass

            # 2. Check for "## Window Title Patterns" section
            patterns_match = re.search(
                r'^##\s+Window\s+Title\s+Patterns?\s*$.*?(?=^##\s+|\Z)',
                content,
                re.MULTILINE | re.DOTALL | re.IGNORECASE
            )

            if patterns_match:
                patterns_section = patterns_match.group(0)
                # Extract patterns from list items or code blocks
                # Look for: - pattern or `pattern`
                list_patterns = re.findall(r'^[-*]\s+`?(.+?)`?\s*$', patterns_section, re.MULTILINE)
                patterns.extend([p.strip() for p in list_patterns if p.strip()])

            # 3. If no patterns found, use default
            if not patterns:
                patterns = [f".*{re.escape(project_name)}.*"]

            return patterns

        except Exception as e:
            print(f"Error parsing window title patterns from {project_file}: {e}")
            # Return default pattern on error
            return [f".*{re.escape(project_name)}.*"]

    def get_all_project_patterns(self) -> Dict[str, List[str]]:
        """
        Get window title patterns for all projects

        Returns:
            Dict mapping project names to lists of regex patterns
        """
        if not self.projects_dir.exists():
            return {}

        patterns_map = {}

        for md_file in self.projects_dir.glob("*.md"):
            try:
                # Extract project name
                with open(md_file, 'r', encoding='utf-8') as f:
                    content = f.read()

                project_name = None

                # Try frontmatter first
                if content.startswith('---'):
                    parts = content.split('---', 2)
                    if len(parts) >= 3:
                        import yaml
                        try:
                            frontmatter = yaml.safe_load(parts[1].strip()) or {}
                            project_name = frontmatter.get('name')
                        except yaml.YAMLError:
                            pass

                # Try first heading if no frontmatter name
                if not project_name:
                    header_match = re.search(r'^#\s+(.+)$', content, re.MULTILINE)
                    if header_match:
                        project_name = header_match.group(1).strip()

                # Fallback to filename
                if not project_name:
                    project_name = md_file.stem.replace('-', ' ').title()

                # Get patterns for this project
                patterns = self.parse_window_title_patterns(project_name)
                patterns_map[project_name] = patterns

            except Exception as e:
                print(f"Error loading project patterns from {md_file}: {e}")
                continue

        return patterns_map

    def get_project_content(self, project_name: str) -> Optional[str]:
        """
        Get the full markdown content of a project file

        Args:
            project_name: Name of the project

        Returns:
            Full markdown content, or None if file not found
        """
        project_file = self.get_project_file(project_name)
        if not project_file:
            return None

        try:
            with open(project_file, 'r', encoding='utf-8') as f:
                return f.read()
        except Exception as e:
            print(f"Error reading project content from {project_file}: {e}")
            return None

    def save_project_content(self, project_name: str, content: str) -> bool:
        """
        Save the full markdown content to a project file

        Args:
            project_name: Name of the project
            content: Full markdown content to save

        Returns:
            True if successful, False otherwise
        """
        project_file = self.get_project_file(project_name)
        if not project_file:
            print(f"Project file not found for: {project_name}")
            return False

        try:
            with open(project_file, 'w', encoding='utf-8') as f:
                f.write(content)
            return True
        except Exception as e:
            print(f"Error saving project content to {project_file}: {e}")
            return False
