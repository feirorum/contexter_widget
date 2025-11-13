"""Git repository detector - detects active git repositories"""

import os
import subprocess
import platform
from typing import Dict, List, Optional
from datetime import datetime
from pathlib import Path

from ..base_detector import BaseContextDetector, DetectionResult


class GitRepoDetector(BaseContextDetector):
    """
    Detects context based on active git repositories

    Finds git repositories in:
    - Shell working directories
    - Parent directories of shell working directories
    Extracts repo name, current branch, remote URL
    """

    def __init__(self, enabled: bool = True):
        """Initialize git repository detector"""
        super().__init__(name="git_repo", enabled=enabled)
        self._system = platform.system().lower()

    def is_available(self) -> bool:
        """Check if git is available"""
        try:
            result = subprocess.run(
                ['git', '--version'],
                capture_output=True,
                timeout=1
            )
            return result.returncode == 0
        except:
            return False

    def _find_git_root(self, path: str) -> Optional[str]:
        """Find git root directory for given path"""
        try:
            result = subprocess.run(
                ['git', '-C', path, 'rev-parse', '--show-toplevel'],
                capture_output=True,
                text=True,
                timeout=1
            )
            if result.returncode == 0:
                return result.stdout.strip()
        except:
            pass
        return None

    def _get_git_info(self, repo_path: str) -> Optional[Dict[str, str]]:
        """Get git repository information"""
        try:
            # Get current branch
            branch_result = subprocess.run(
                ['git', '-C', repo_path, 'branch', '--show-current'],
                capture_output=True,
                text=True,
                timeout=1
            )
            branch = branch_result.stdout.strip() if branch_result.returncode == 0 else 'unknown'

            # Get remote URL
            remote_result = subprocess.run(
                ['git', '-C', repo_path, 'remote', 'get-url', 'origin'],
                capture_output=True,
                text=True,
                timeout=1
            )
            remote_url = remote_result.stdout.strip() if remote_result.returncode == 0 else None

            # Get repo name from path
            repo_name = os.path.basename(repo_path)

            # Try to extract repo name from remote URL if available
            if remote_url:
                # Extract from URLs like: git@github.com:user/repo.git or https://github.com/user/repo.git
                if remote_url.endswith('.git'):
                    remote_url = remote_url[:-4]
                url_parts = remote_url.replace(':', '/').split('/')
                if url_parts:
                    repo_name = url_parts[-1]

            return {
                'path': repo_path,
                'name': repo_name,
                'branch': branch,
                'remote_url': remote_url or 'none'
            }

        except Exception as e:
            print(f"⚠️  Error getting git info for {repo_path}: {e}")
            return None

    def _get_shell_working_dirs(self) -> List[str]:
        """Get working directories of shell processes"""
        working_dirs = []

        try:
            if self._system == 'linux':
                # Find shell processes
                result = subprocess.run(
                    ['ps', 'aux'],
                    capture_output=True,
                    text=True,
                    timeout=3
                )

                if result.returncode == 0:
                    shell_names = ['bash', 'zsh', 'fish', 'sh']
                    shell_pids = []

                    for line in result.stdout.splitlines()[1:]:
                        parts = line.split(None, 10)
                        if len(parts) > 10:
                            pid = parts[1]
                            cmdline = parts[10]
                            proc_name = cmdline.split()[0].split('/')[-1] if cmdline.split() else ''

                            if any(shell in proc_name for shell in shell_names):
                                shell_pids.append(pid)

                    # Get CWD for each shell
                    for pid in shell_pids:
                        try:
                            cwd_path = f'/proc/{pid}/cwd'
                            if os.path.exists(cwd_path):
                                cwd = os.readlink(cwd_path)
                                if os.path.isdir(cwd):
                                    working_dirs.append(cwd)
                        except:
                            continue

            elif self._system == 'darwin':
                # For macOS, use lsof (simplified)
                result = subprocess.run(
                    ['lsof', '-c', 'bash', '-c', 'zsh', '-c', 'fish', '-a', '-d', 'cwd', '-Fn'],
                    capture_output=True,
                    text=True,
                    timeout=3
                )
                if result.returncode == 0:
                    for line in result.stdout.splitlines():
                        if line.startswith('n') and len(line) > 1:
                            path = line[1:]
                            if os.path.isdir(path):
                                working_dirs.append(path)

        except Exception as e:
            print(f"⚠️  Error getting shell working dirs: {e}")

        return working_dirs

    def _find_active_git_repos(self) -> List[Dict[str, str]]:
        """Find all active git repositories"""
        working_dirs = self._get_shell_working_dirs()
        git_repos = []
        seen_repos = set()

        for wd in working_dirs:
            # Try to find git root for this directory
            git_root = self._find_git_root(wd)

            if git_root and git_root not in seen_repos:
                git_info = self._get_git_info(git_root)
                if git_info:
                    git_repos.append(git_info)
                    seen_repos.add(git_root)

        return git_repos

    def detect(self, project_patterns: Dict[str, List[str]]) -> DetectionResult:
        """
        Detect project based on active git repositories

        Args:
            project_patterns: Dict mapping project names to patterns

        Returns:
            DetectionResult with detected project or None
        """
        git_repos = self._find_active_git_repos()

        if not git_repos:
            result = DetectionResult(
                project_name=None,
                confidence=0.0,
                source="git_repo",
                raw_data={"git_repos": [], "error": "No git repositories found"},
                timestamp=datetime.now()
            )
            self.last_result = result
            return result

        # Try to match repo names to known projects
        best_match = None
        best_confidence = 0.0
        matched_repo = None

        for repo in git_repos:
            repo_name = repo['name']
            repo_name_lower = repo_name.lower()

            for known_project in project_patterns.keys():
                known_lower = known_project.lower()

                # Exact match
                if repo_name_lower == known_lower:
                    best_match = known_project
                    best_confidence = 1.0
                    matched_repo = repo
                    break

                # Repo name contains project name
                if known_lower in repo_name_lower or repo_name_lower in known_lower:
                    confidence = 0.8
                    if confidence > best_confidence:
                        best_match = known_project
                        best_confidence = confidence
                        matched_repo = repo

        result = DetectionResult(
            project_name=best_match,
            confidence=best_confidence,
            source="git_repo",
            raw_data={
                "git_repos": git_repos,
                "matched_repo": matched_repo
            },
            timestamp=datetime.now()
        )

        self.last_result = result
        return result

    def get_raw_context(self) -> Optional[Dict[str, any]]:
        """Get raw git repository data without pattern matching"""
        git_repos = self._find_active_git_repos()
        if git_repos:
            return {
                "git_repos": git_repos,
                "count": len(git_repos)
            }
        return None
