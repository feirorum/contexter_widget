"""Base class for context detectors"""

from abc import ABC, abstractmethod
from typing import Optional, Dict, Any, List
from dataclasses import dataclass
from datetime import datetime


@dataclass
class DetectionResult:
    """Result of context detection"""

    project_name: Optional[str]  # Name of detected project, or None
    confidence: float  # Confidence score 0.0-1.0
    source: str  # Detection source (e.g., "window_title", "git_repo", "file_path")
    raw_data: Dict[str, Any]  # Raw data used for detection
    timestamp: datetime

    def __post_init__(self):
        """Validate confidence score"""
        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError(f"Confidence must be between 0.0 and 1.0, got {self.confidence}")


class BaseContextDetector(ABC):
    """
    Base class for all context detectors

    Each detector implements a specific method of detecting the current
    work context (e.g., window title, git repository, file path, etc.)
    """

    def __init__(self, name: str, enabled: bool = True):
        """
        Initialize detector

        Args:
            name: Unique name for this detector
            enabled: Whether this detector is enabled
        """
        self.name = name
        self.enabled = enabled
        self.last_result: Optional[DetectionResult] = None

    @abstractmethod
    def detect(self, project_patterns: Dict[str, List[str]]) -> DetectionResult:
        """
        Detect current context

        Args:
            project_patterns: Dict mapping project names to list of patterns
                             (e.g., regex patterns, file paths, etc.)

        Returns:
            DetectionResult with detected project or None
        """
        pass

    @abstractmethod
    def is_available(self) -> bool:
        """
        Check if this detector is available on current system

        Returns:
            True if detector can run on this system
        """
        pass

    def get_raw_context(self) -> Optional[Dict[str, Any]]:
        """
        Get raw context data without pattern matching

        Returns:
            Dict with raw context data, or None if not available
        """
        return None

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(name={self.name}, enabled={self.enabled})"
