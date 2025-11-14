"""Running process detector - detects project-specific running processes"""

import subprocess
import platform
import re
from typing import Dict, List, Optional
from datetime import datetime

from ..base_detector import BaseContextDetector, DetectionResult


class ProcessDetector(BaseContextDetector):
    """
    Detects context based on running processes

    Looks for project-specific processes:
    - npm/yarn dev servers
    - docker containers with project names
    - python/node processes with project names in args
    - gradle/maven builds
    - etc.
    """

    def __init__(self, enabled: bool = True):
        """Initialize process detector"""
        super().__init__(name="running_process", enabled=enabled)
        self._system = platform.system().lower()

    def is_available(self) -> bool:
        """Check if detector can list processes"""
        return True  # Always available (uses ps/PowerShell)

    def _get_all_processes(self) -> List[Dict[str, str]]:
        """Get all running processes with command lines"""
        processes = []

        try:
            if self._system == 'windows':
                # Use PowerShell on Windows
                result = subprocess.run(
                    ['powershell.exe', '-Command',
                     'Get-Process | Select-Object Name, Id, CommandLine | ConvertTo-Json'],
                    capture_output=True,
                    text=True,
                    timeout=5
                )

                if result.returncode == 0 and result.stdout.strip():
                    import json
                    data = json.loads(result.stdout)
                    items = data if isinstance(data, list) else [data]

                    for proc in items:
                        cmdline = proc.get('CommandLine', '')
                        if cmdline:
                            processes.append({
                                'pid': str(proc.get('Id', '')),
                                'name': proc.get('Name', ''),
                                'cmdline': cmdline
                            })

            else:
                # Use ps on Linux/macOS
                result = subprocess.run(
                    ['ps', 'aux'],
                    capture_output=True,
                    text=True,
                    timeout=5
                )

                if result.returncode == 0:
                    for line in result.stdout.splitlines()[1:]:  # Skip header
                        parts = line.split(None, 10)
                        if len(parts) > 10:
                            pid = parts[1]
                            cmdline = parts[10]
                            name = cmdline.split()[0].split('/')[-1] if cmdline.split() else ''

                            processes.append({
                                'pid': pid,
                                'name': name,
                                'cmdline': cmdline
                            })

        except Exception as e:
            print(f"⚠️  Error getting processes: {e}")

        return processes

    def _find_project_processes(self) -> List[Dict[str, str]]:
        """Find processes that might be project-specific"""
        all_processes = self._get_all_processes()
        project_processes = []

        # Keywords that indicate development/project processes
        dev_keywords = [
            'npm', 'yarn', 'node', 'webpack', 'vite', 'next',
            'python', 'uvicorn', 'gunicorn', 'flask', 'django',
            'docker', 'compose',
            'gradle', 'maven', 'mvn',
            'rails', 'bundle',
            'cargo', 'rust',
            'go run', 'go build'
        ]

        for proc in all_processes:
            cmdline = proc['cmdline'].lower()
            name = proc['name'].lower()

            # Check if process matches dev keywords
            if any(keyword in cmdline or keyword in name for keyword in dev_keywords):
                # Try to extract project context from command line
                project_hint = self._extract_project_hint(proc['cmdline'])

                project_processes.append({
                    'pid': proc['pid'],
                    'name': proc['name'],
                    'cmdline': proc['cmdline'],
                    'project_hint': project_hint
                })

        return project_processes

    def _extract_project_hint(self, cmdline: str) -> Optional[str]:
        """Try to extract project name/context from command line"""
        # Look for common patterns:
        # - npm run dev (in /path/to/project)
        # - python manage.py runserver (in /path/to/project)
        # - docker-compose -p projectname
        # - node server.js (look for file paths)

        # Try to find directory paths in command
        import os
        parts = cmdline.split()

        for part in parts:
            # Skip flags
            if part.startswith('-'):
                continue

            # Check if it looks like a file path
            if '/' in part or '\\' in part:
                # Try to extract directory name
                try:
                    if os.path.sep in part:
                        path_parts = part.split(os.path.sep)
                        # Find meaningful directory names (not root, usr, etc.)
                        for p in reversed(path_parts):
                            if p and p not in ['', '.', '..', 'usr', 'bin', 'local', 'lib', 'src', 'app']:
                                return p
                except:
                    pass

        # Look for docker-compose project names
        if 'docker' in cmdline and '-p ' in cmdline:
            match = re.search(r'-p\s+(\S+)', cmdline)
            if match:
                return match.group(1)

        return None

    def detect(self, project_patterns: Dict[str, List[str]]) -> DetectionResult:
        """
        Detect project based on running processes

        Args:
            project_patterns: Dict mapping project names to patterns

        Returns:
            DetectionResult with detected project or None
        """
        project_processes = self._find_project_processes()

        if not project_processes:
            result = DetectionResult(
                project_name=None,
                confidence=0.0,
                source="running_process",
                raw_data={"processes": [], "error": "No project-related processes found"},
                timestamp=datetime.now()
            )
            self.last_result = result
            return result

        # Try to match process hints to known projects
        best_match = None
        best_confidence = 0.0
        matched_process = None

        for proc in project_processes:
            project_hint = proc.get('project_hint', '')
            cmdline = proc['cmdline']

            if not project_hint:
                continue

            project_hint_lower = project_hint.lower()
            cmdline_lower = cmdline.lower()

            for known_project in project_patterns.keys():
                known_lower = known_project.lower()

                # Exact match with hint
                if project_hint_lower == known_lower:
                    best_match = known_project
                    best_confidence = 0.9
                    matched_process = proc
                    break

                # Hint contains project name
                if known_lower in project_hint_lower or project_hint_lower in known_lower:
                    confidence = 0.7
                    if confidence > best_confidence:
                        best_match = known_project
                        best_confidence = confidence
                        matched_process = proc

                # Command line contains project name
                if known_lower in cmdline_lower:
                    confidence = 0.5
                    if confidence > best_confidence:
                        best_match = known_project
                        best_confidence = confidence
                        matched_process = proc

        result = DetectionResult(
            project_name=best_match,
            confidence=best_confidence,
            source="running_process",
            raw_data={
                "processes": project_processes,
                "matched_process": matched_process,
                "total_count": len(project_processes)
            },
            timestamp=datetime.now()
        )

        self.last_result = result
        return result

    def get_raw_context(self) -> Optional[Dict[str, any]]:
        """Get raw process data without pattern matching"""
        processes = self._find_project_processes()
        if processes:
            return {
                "processes": processes,
                "count": len(processes)
            }
        return None
