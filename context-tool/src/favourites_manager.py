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
