"""IDE project detector - detects open IDE workspaces"""

import os
import json
import subprocess
import platform
from typing import Dict, List, Optional
from datetime import datetime
from pathlib import Path

from ..base_detector import BaseContextDetector, DetectionResult


class IdeProjectDetector(BaseContextDetector):
    """
    Detects context based on active IDE project/workspace

    Supports:
    - VS Code (reads workspace files and process args)
    - IntelliJ IDEA / PyCharm / WebStorm (reads .idea directory)
    - Sublime Text (reads project files)
    """

    def __init__(self, enabled: bool = True):
        """Initialize IDE project detector"""
        super().__init__(name="ide_project", enabled=enabled)
        self._system = platform.system().lower()

    def is_available(self) -> bool:
        """Check if detector can find IDE processes"""
        # Always available - will check for IDE processes
        return True

    def _get_running_processes(self) -> List[Dict[str, str]]:
        """Get list of running processes with their command lines"""
        processes = []

        try:
            if self._system == 'windows':
                # Use PowerShell on Windows
                result = subprocess.run(
                    ['powershell.exe', '-Command',
                     'Get-Process | Select-Object Name, CommandLine | ConvertTo-Json'],
                    capture_output=True,
                    text=True,
                    timeout=3
                )
                if result.returncode == 0:
                    data = json.loads(result.stdout)
                    for proc in data if isinstance(data, list) else [data]:
                        if proc.get('CommandLine'):
                            processes.append({
                                'name': proc.get('Name', ''),
                                'cmdline': proc.get('CommandLine', '')
                            })
            else:
                # Use ps on Linux/macOS
                result = subprocess.run(
                    ['ps', 'aux'],
                    capture_output=True,
                    text=True,
                    timeout=3
                )
                if result.returncode == 0:
                    for line in result.stdout.splitlines()[1:]:  # Skip header
                        parts = line.split(None, 10)
                        if len(parts) > 10:
                            cmdline = parts[10]
                            # Extract process name
                            name = cmdline.split()[0].split('/')[-1] if cmdline.split() else ''
                            processes.append({
                                'name': name,
                                'cmdline': cmdline
                            })
        except Exception as e:
            print(f"⚠️  Error getting processes: {e}")

        return processes

    def _extract_vscode_workspace(self, cmdline: str) -> Optional[str]:
        """Extract workspace path from VS Code command line"""
        # VS Code often has the workspace path as an argument
        # Common patterns: code /path/to/workspace, code --folder-uri file:///path

        # Try to find directory paths in command line
        parts = cmdline.split()
        for i, part in enumerate(parts):
            # Skip flags
            if part.startswith('-'):
                continue

            # Check if it's a directory
            if os.path.isdir(part):
                return os.path.basename(os.path.abspath(part))

            # Check for .code-workspace files
            if part.endswith('.code-workspace'):
                try:
                    workspace_name = Path(part).stem
                    return workspace_name
                except:
                    pass

        return None

    def _extract_intellij_project(self, cmdline: str) -> Optional[str]:
        """Extract project name from IntelliJ-based IDE command line"""
        # IntelliJ often opens with project path as argument
        parts = cmdline.split()
        for part in parts:
            if os.path.isdir(part):
                # Check if it has .idea directory (IntelliJ marker)
                idea_dir = os.path.join(part, '.idea')
                if os.path.exists(idea_dir):
                    return os.path.basename(os.path.abspath(part))

        return None

    def _find_ide_projects(self) -> List[Dict[str, str]]:
        """Find active IDE projects from running processes"""
        processes = self._get_running_processes()
        projects = []

        for proc in processes:
            name = proc['name'].lower()
            cmdline = proc['cmdline']

            # VS Code
            if 'code' in name or 'vscode' in name:
                workspace = self._extract_vscode_workspace(cmdline)
                if workspace:
                    projects.append({
                        'ide': 'VS Code',
                        'project': workspace,
                        'cmdline': cmdline
                    })

            # IntelliJ-based IDEs
            elif any(ide in name for ide in ['idea', 'pycharm', 'webstorm', 'phpstorm', 'goland', 'rider']):
                project = self._extract_intellij_project(cmdline)
                if project:
                    ide_name = 'IntelliJ IDEA' if 'idea' in name else name.title()
                    projects.append({
                        'ide': ide_name,
                        'project': project,
                        'cmdline': cmdline
                    })

            # Sublime Text
            elif 'sublime' in name:
                # Look for .sublime-project files in cmdline
                parts = cmdline.split()
                for part in parts:
                    if part.endswith('.sublime-project'):
                        project_name = Path(part).stem
                        projects.append({
                            'ide': 'Sublime Text',
                            'project': project_name,
                            'cmdline': cmdline
                        })

        return projects

    def detect(self, project_patterns: Dict[str, List[str]]) -> DetectionResult:
        """
        Detect project based on active IDE workspaces

        Args:
            project_patterns: Dict mapping project names to patterns
                             (for IDE detector, we match project names directly)

        Returns:
            DetectionResult with detected project or None
        """
        ide_projects = self._find_ide_projects()

        if not ide_projects:
            result = DetectionResult(
                project_name=None,
                confidence=0.0,
                source="ide_project",
                raw_data={"ide_projects": [], "error": "No IDE projects found"},
                timestamp=datetime.now()
            )
            self.last_result = result
            return result

        # Try to match IDE project names to known projects
        best_match = None
        best_confidence = 0.0
        matched_ide_project = None

        for ide_project in ide_projects:
            project_name_lower = ide_project['project'].lower()

            # Check exact match first
            for known_project in project_patterns.keys():
                known_lower = known_project.lower()

                # Exact match
                if project_name_lower == known_lower:
                    best_match = known_project
                    best_confidence = 1.0
                    matched_ide_project = ide_project
                    break

                # Partial match (IDE project contains known project name)
                if known_lower in project_name_lower or project_name_lower in known_lower:
                    confidence = 0.7
                    if confidence > best_confidence:
                        best_match = known_project
                        best_confidence = confidence
                        matched_ide_project = ide_project

        result = DetectionResult(
            project_name=best_match,
            confidence=best_confidence,
            source="ide_project",
            raw_data={
                "ide_projects": ide_projects,
                "matched_project": matched_ide_project
            },
            timestamp=datetime.now()
        )

        self.last_result = result
        return result

    def get_raw_context(self) -> Optional[Dict[str, any]]:
        """Get raw IDE project data without pattern matching"""
        ide_projects = self._find_ide_projects()
        if ide_projects:
            return {
                "ide_projects": ide_projects,
                "count": len(ide_projects)
            }
        return None
