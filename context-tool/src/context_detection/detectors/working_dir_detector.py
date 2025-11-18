"""Working directory detector - detects active terminal/shell working directories"""

import os
import subprocess
import platform
from typing import Dict, List, Optional
from datetime import datetime
from pathlib import Path

from ..base_detector import BaseContextDetector, DetectionResult


class WorkingDirectoryDetector(BaseContextDetector):
    """
    Detects context based on working directories of active terminal sessions

    Checks PWD of running shell processes (bash, zsh, fish, powershell, etc.)
    """

    def __init__(self, enabled: bool = True):
        """Initialize working directory detector"""
        super().__init__(name="working_directory", enabled=enabled)
        self._system = platform.system().lower()

    def is_available(self) -> bool:
        """Check if detector can access process information"""
        # Available on Linux/macOS with /proc or lsof
        # Available on Windows with PowerShell
        if self._system == 'linux':
            return os.path.exists('/proc')
        return True

    def _get_shell_working_dirs_linux(self) -> List[Dict[str, str]]:
        """Get working directories of shell processes on Linux"""
        working_dirs = []

        try:
            # Find shell processes
            result = subprocess.run(
                ['ps', 'aux'],
                capture_output=True,
                text=True,
                timeout=3
            )

            if result.returncode != 0:
                return working_dirs

            shell_names = ['bash', 'zsh', 'fish', 'sh', 'ksh', 'tcsh']
            shell_pids = []

            # Find shell PIDs
            for line in result.stdout.splitlines()[1:]:
                parts = line.split(None, 10)
                if len(parts) > 10:
                    pid = parts[1]
                    cmdline = parts[10]
                    proc_name = cmdline.split()[0].split('/')[-1] if cmdline.split() else ''

                    if any(shell in proc_name for shell in shell_names):
                        shell_pids.append(pid)

            # Get working directory for each shell PID
            for pid in shell_pids:
                try:
                    cwd_path = f'/proc/{pid}/cwd'
                    if os.path.exists(cwd_path):
                        cwd = os.readlink(cwd_path)
                        if os.path.isdir(cwd):
                            working_dirs.append({
                                'pid': pid,
                                'cwd': cwd,
                                'basename': os.path.basename(cwd)
                            })
                except:
                    continue

        except Exception as e:
            print(f"⚠️  Error getting shell working dirs (Linux): {e}")

        return working_dirs

    def _get_shell_working_dirs_macos(self) -> List[Dict[str, str]]:
        """Get working directories of shell processes on macOS"""
        working_dirs = []

        try:
            # Use lsof to find working directories
            result = subprocess.run(
                ['lsof', '-c', 'bash', '-c', 'zsh', '-c', 'fish', '-Fn'],
                capture_output=True,
                text=True,
                timeout=3
            )

            if result.returncode != 0:
                return working_dirs

            current_pid = None
            current_cwd = None

            for line in result.stdout.splitlines():
                if line.startswith('p'):
                    # Process ID
                    current_pid = line[1:]
                elif line.startswith('n'):
                    # File name - look for cwd
                    path = line[1:]
                    if os.path.isdir(path):
                        current_cwd = path

                # When we have both PID and CWD, add it
                if current_pid and current_cwd:
                    working_dirs.append({
                        'pid': current_pid,
                        'cwd': current_cwd,
                        'basename': os.path.basename(current_cwd)
                    })
                    current_cwd = None

        except Exception as e:
            print(f"⚠️  Error getting shell working dirs (macOS): {e}")

        return working_dirs

    def _get_shell_working_dirs_windows(self) -> List[Dict[str, str]]:
        """Get working directories of shell processes on Windows"""
        working_dirs = []

        try:
            # PowerShell command to get shell processes and their working dirs
            ps_command = """
            Get-Process -Name powershell,pwsh,cmd,bash,zsh -ErrorAction SilentlyContinue |
            ForEach-Object {
                try {
                    $path = $_.Path
                    if ($path) {
                        [PSCustomObject]@{
                            PID = $_.Id
                            Name = $_.Name
                            Path = (Get-Location -PSProvider FileSystem).Path
                        }
                    }
                } catch {}
            } | ConvertTo-Json
            """

            result = subprocess.run(
                ['powershell.exe', '-Command', ps_command],
                capture_output=True,
                text=True,
                timeout=3
            )

            if result.returncode == 0 and result.stdout.strip():
                import json
                data = json.loads(result.stdout)
                items = data if isinstance(data, list) else [data]

                for item in items:
                    cwd = item.get('Path', '')
                    if cwd and os.path.isdir(cwd):
                        working_dirs.append({
                            'pid': str(item.get('PID', '')),
                            'cwd': cwd,
                            'basename': os.path.basename(cwd)
                        })

        except Exception as e:
            print(f"⚠️  Error getting shell working dirs (Windows): {e}")

        return working_dirs

    def _get_all_working_dirs(self) -> List[Dict[str, str]]:
        """Get all shell working directories for current platform"""
        if self._system == 'linux':
            return self._get_shell_working_dirs_linux()
        elif self._system == 'darwin':
            return self._get_shell_working_dirs_macos()
        elif self._system == 'windows':
            return self._get_shell_working_dirs_windows()
        return []

    def detect(self, project_patterns: Dict[str, List[str]]) -> DetectionResult:
        """
        Detect project based on shell working directories

        Args:
            project_patterns: Dict mapping project names to patterns
                             (we match against directory names/paths)

        Returns:
            DetectionResult with detected project or None
        """
        working_dirs = self._get_all_working_dirs()

        if not working_dirs:
            result = DetectionResult(
                project_name=None,
                confidence=0.0,
                source="working_directory",
                raw_data={"working_dirs": [], "error": "No shell processes found"},
                timestamp=datetime.now()
            )
            self.last_result = result
            return result

        # Try to match working directory names to known projects
        best_match = None
        best_confidence = 0.0
        matched_dir = None

        for wd in working_dirs:
            cwd = wd['cwd']
            basename = wd['basename']

            for known_project in project_patterns.keys():
                known_lower = known_project.lower()
                basename_lower = basename.lower()
                cwd_lower = cwd.lower()

                # Exact basename match
                if basename_lower == known_lower:
                    best_match = known_project
                    best_confidence = 1.0
                    matched_dir = wd
                    break

                # Basename contains project name
                if known_lower in basename_lower:
                    confidence = 0.8
                    if confidence > best_confidence:
                        best_match = known_project
                        best_confidence = confidence
                        matched_dir = wd

                # Full path contains project name
                if known_lower in cwd_lower:
                    confidence = 0.6
                    if confidence > best_confidence:
                        best_match = known_project
                        best_confidence = confidence
                        matched_dir = wd

        result = DetectionResult(
            project_name=best_match,
            confidence=best_confidence,
            source="working_directory",
            raw_data={
                "working_dirs": working_dirs,
                "matched_dir": matched_dir
            },
            timestamp=datetime.now()
        )

        self.last_result = result
        return result

    def get_raw_context(self) -> Optional[Dict[str, any]]:
        """Get raw working directory data without pattern matching"""
        working_dirs = self._get_all_working_dirs()
        if working_dirs:
            return {
                "working_dirs": working_dirs,
                "count": len(working_dirs),
                "unique_dirs": list(set(wd['cwd'] for wd in working_dirs))
            }
        return None
