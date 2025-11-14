"""Window title detector for WSL/Windows"""

import re
import subprocess
import platform
from typing import Dict, List, Optional
from datetime import datetime

from ..base_detector import BaseContextDetector, DetectionResult


class WindowTitleDetector(BaseContextDetector):
    """
    Detects context based on active window title

    Works on:
    - WSL (Windows Subsystem for Linux) - uses PowerShell to get Windows window title
    - Windows - uses PowerShell directly
    - Linux - uses xdotool (if available)
    - macOS - uses AppleScript (if available)
    """

    def __init__(self, enabled: bool = True):
        """Initialize window title detector"""
        super().__init__(name="window_title", enabled=enabled)
        self._system = platform.system().lower()
        self._is_wsl = self._detect_wsl()

    def _detect_wsl(self) -> bool:
        """Detect if running in WSL"""
        try:
            with open('/proc/version', 'r') as f:
                return 'microsoft' in f.read().lower()
        except:
            return False

    def is_available(self) -> bool:
        """Check if detector is available on current system"""
        if self._is_wsl or self._system == 'windows':
            # Check if PowerShell is available
            try:
                subprocess.run(
                    ['powershell.exe', '-Command', 'exit'],
                    capture_output=True,
                    timeout=1
                )
                return True
            except:
                return False

        elif self._system == 'linux':
            # Check if xdotool is available
            try:
                subprocess.run(
                    ['which', 'xdotool'],
                    capture_output=True,
                    timeout=1
                )
                return True
            except:
                return False

        elif self._system == 'darwin':
            # macOS - osascript should be available
            return True

        return False

    def get_active_window_title(self) -> Optional[str]:
        """
        Get the title of the currently active window

        Returns:
            Window title string, or None if unavailable
        """
        try:
            if self._is_wsl or self._system == 'windows':
                return self._get_window_title_powershell()
            elif self._system == 'linux':
                return self._get_window_title_linux()
            elif self._system == 'darwin':
                return self._get_window_title_macos()
        except Exception as e:
            print(f"⚠️  Error getting window title: {e}")
            return None

        return None

    def _get_window_title_powershell(self) -> Optional[str]:
        """Get window title using PowerShell (WSL/Windows)"""
        try:
            # PowerShell command to get active window title
            ps_command = """
            Add-Type @"
                using System;
                using System.Runtime.InteropServices;
                using System.Text;
                public class Win32 {
                    [DllImport("user32.dll")]
                    public static extern IntPtr GetForegroundWindow();
                    [DllImport("user32.dll")]
                    public static extern int GetWindowText(IntPtr hWnd, StringBuilder text, int count);
                }
"@
            $handle = [Win32]::GetForegroundWindow()
            $title = New-Object System.Text.StringBuilder 256
            [Win32]::GetWindowText($handle, $title, 256) | Out-Null
            $title.ToString()
            """

            result = subprocess.run(
                ['powershell.exe', '-Command', ps_command],
                capture_output=True,
                text=True,
                timeout=2
            )

            if result.returncode == 0:
                title = result.stdout.strip()
                if title:
                    return title

        except Exception as e:
            print(f"⚠️  PowerShell window title detection failed: {e}")

        return None

    def _get_window_title_linux(self) -> Optional[str]:
        """Get window title using xdotool (Linux)"""
        try:
            result = subprocess.run(
                ['xdotool', 'getactivewindow', 'getwindowname'],
                capture_output=True,
                text=True,
                timeout=1
            )

            if result.returncode == 0:
                return result.stdout.strip()

        except Exception as e:
            print(f"⚠️  xdotool window title detection failed: {e}")

        return None

    def _get_window_title_macos(self) -> Optional[str]:
        """Get window title using AppleScript (macOS)"""
        try:
            script = 'tell application "System Events" to get name of first application process whose frontmost is true'
            result = subprocess.run(
                ['osascript', '-e', script],
                capture_output=True,
                text=True,
                timeout=1
            )

            if result.returncode == 0:
                return result.stdout.strip()

        except Exception as e:
            print(f"⚠️  AppleScript window title detection failed: {e}")

        return None

    def detect(self, project_patterns: Dict[str, List[str]]) -> DetectionResult:
        """
        Detect project based on window title

        Args:
            project_patterns: Dict mapping project names to list of regex patterns

        Returns:
            DetectionResult with detected project or None
        """
        window_title = self.get_active_window_title()

        if not window_title:
            result = DetectionResult(
                project_name=None,
                confidence=0.0,
                source="window_title",
                raw_data={"window_title": None, "error": "Could not get window title"},
                timestamp=datetime.now()
            )
            self.last_result = result
            return result

        # Try to match against project patterns
        best_match = None
        best_confidence = 0.0

        for project_name, patterns in project_patterns.items():
            for pattern in patterns:
                try:
                    # Compile regex pattern
                    regex = re.compile(pattern, re.IGNORECASE)
                    match = regex.search(window_title)

                    if match:
                        # Calculate confidence based on match quality
                        match_length = len(match.group(0))
                        title_length = len(window_title)
                        confidence = min(0.5 + (match_length / title_length) * 0.5, 1.0)

                        if confidence > best_confidence:
                            best_match = project_name
                            best_confidence = confidence

                except re.error as e:
                    print(f"⚠️  Invalid regex pattern for {project_name}: {pattern} - {e}")
                    continue

        result = DetectionResult(
            project_name=best_match,
            confidence=best_confidence,
            source="window_title",
            raw_data={"window_title": window_title, "matched_project": best_match},
            timestamp=datetime.now()
        )

        self.last_result = result
        return result

    def get_raw_context(self) -> Optional[Dict[str, any]]:
        """Get raw window title without pattern matching"""
        title = self.get_active_window_title()
        if title:
            return {
                "window_title": title,
                "system": self._system,
                "is_wsl": self._is_wsl
            }
        return None
