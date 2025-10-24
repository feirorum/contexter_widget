"""Deterministic pattern detection for known formats"""

import re
from typing import Dict, List, Optional


class PatternMatcher:
    """Detect patterns like Jira tickets, emails, URLs, etc."""

    PATTERNS = {
        'jira_ticket': r'\b(JT-?\d+)\b',
        'email': r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',
        'url': r'https?://[^\s]+',
        'phone': r'\b\d{3}[-.]?\d{3}[-.]?\d{4}\b',
        'date': r'\b\d{4}-\d{2}-\d{2}\b'
    }

    def detect(self, text: str) -> Dict[str, List[str]]:
        """
        Detect all patterns in text

        Args:
            text: Text to analyze

        Returns:
            Dictionary mapping pattern types to list of matches
        """
        results = {}
        for pattern_type, regex in self.PATTERNS.items():
            matches = re.findall(regex, text, re.IGNORECASE)
            if matches:
                results[pattern_type] = matches
        return results

    def get_type(self, text: str) -> Optional[str]:
        """
        Get primary type of the text

        Args:
            text: Text to classify

        Returns:
            Most specific pattern type found, or None
        """
        detections = self.detect(text)
        if not detections:
            return None

        # Return most specific pattern found (priority order)
        priority = ['jira_ticket', 'email', 'url', 'phone', 'date']
        for ptype in priority:
            if ptype in detections:
                return ptype

        return list(detections.keys())[0]

    def is_pattern_type(self, text: str, pattern_type: str) -> bool:
        """
        Check if text matches a specific pattern type

        Args:
            text: Text to check
            pattern_type: Pattern type to check for

        Returns:
            True if text matches the pattern type
        """
        if pattern_type not in self.PATTERNS:
            return False

        regex = self.PATTERNS[pattern_type]
        return bool(re.search(regex, text, re.IGNORECASE))

    def extract_first(self, text: str, pattern_type: str) -> Optional[str]:
        """
        Extract first match of a specific pattern type

        Args:
            text: Text to search
            pattern_type: Pattern type to extract

        Returns:
            First match or None
        """
        if pattern_type not in self.PATTERNS:
            return None

        regex = self.PATTERNS[pattern_type]
        match = re.search(regex, text, re.IGNORECASE)
        return match.group(0) if match else None

    def add_pattern(self, pattern_type: str, regex: str):
        """
        Add a custom pattern

        Args:
            pattern_type: Name for the new pattern
            regex: Regular expression pattern
        """
        self.PATTERNS[pattern_type] = regex
