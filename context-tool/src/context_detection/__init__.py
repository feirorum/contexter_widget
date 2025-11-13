"""Context detection module for automatic project detection"""

from .base_detector import BaseContextDetector, DetectionResult
from .context_manager import ContextDetectionManager

__all__ = ['BaseContextDetector', 'DetectionResult', 'ContextDetectionManager']
