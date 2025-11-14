"""Context detection manager - coordinates multiple detectors"""

import asyncio
from typing import Dict, List, Optional, Callable
from datetime import datetime

from .base_detector import BaseContextDetector, DetectionResult


class ContextDetectionManager:
    """
    Manages multiple context detectors and coordinates detection

    Supports:
    - Multiple simultaneous detectors
    - Periodic polling
    - Change notifications via callbacks
    - Confidence-based selection
    """

    def __init__(self):
        """Initialize context detection manager"""
        self.detectors: List[BaseContextDetector] = []
        self.current_context: Optional[str] = None
        self.last_detection: Optional[DetectionResult] = None
        self.on_context_change: Optional[Callable[[Optional[str], Optional[str]], None]] = None
        self._polling_task: Optional[asyncio.Task] = None
        self._is_running = False

    def add_detector(self, detector: BaseContextDetector):
        """
        Add a detector to the manager

        Args:
            detector: Detector instance to add
        """
        if detector.is_available():
            self.detectors.append(detector)
            print(f"✅ Added context detector: {detector.name}")
        else:
            print(f"⚠️  Detector {detector.name} not available on this system")

    def detect_once(self, project_patterns: Dict[str, List[str]]) -> Optional[DetectionResult]:
        """
        Run detection once using all enabled detectors

        Args:
            project_patterns: Dict mapping project names to patterns

        Returns:
            Best detection result, or None
        """
        if not self.detectors:
            return None

        results = []

        for detector in self.detectors:
            if not detector.enabled:
                continue

            try:
                result = detector.detect(project_patterns)
                if result.project_name and result.confidence > 0.0:
                    results.append(result)
            except Exception as e:
                print(f"⚠️  Error in detector {detector.name}: {e}")
                continue

        if not results:
            return None

        # Select best result by confidence
        best_result = max(results, key=lambda r: r.confidence)

        # Update current context if changed
        old_context = self.current_context
        new_context = best_result.project_name

        if old_context != new_context:
            self.current_context = new_context
            self.last_detection = best_result

            # Trigger callback if registered
            if self.on_context_change:
                try:
                    self.on_context_change(old_context, new_context)
                except Exception as e:
                    print(f"⚠️  Error in context change callback: {e}")

            # Log the change
            if new_context:
                raw_data = best_result.raw_data
                window_title = raw_data.get('window_title', 'unknown')
                print(f"🎯 Context changed: '{old_context or 'None'}' → '{new_context}'")
                print(f"   Source: {best_result.source}")
                print(f"   Window title: {window_title}")
                print(f"   Confidence: {best_result.confidence:.2f}")
            else:
                print(f"🎯 Context cleared: '{old_context}' → None")

        return best_result

    async def start_polling(
        self,
        project_patterns: Dict[str, List[str]],
        interval: float = 2.0
    ):
        """
        Start periodic context detection

        Args:
            project_patterns: Dict mapping project names to patterns
            interval: Polling interval in seconds (default: 2.0)
        """
        if self._is_running:
            print("⚠️  Context detection already running")
            return

        self._is_running = True
        print(f"🔍 Starting context detection (interval: {interval}s)")

        while self._is_running:
            try:
                self.detect_once(project_patterns)
                await asyncio.sleep(interval)
            except asyncio.CancelledError:
                break
            except Exception as e:
                print(f"⚠️  Error in polling loop: {e}")
                await asyncio.sleep(interval)

        print("🔍 Context detection stopped")

    async def stop_polling(self):
        """Stop periodic context detection"""
        self._is_running = False
        if self._polling_task:
            self._polling_task.cancel()
            try:
                await self._polling_task
            except asyncio.CancelledError:
                pass
            self._polling_task = None

    def get_current_context(self) -> Optional[str]:
        """Get currently detected project context"""
        return self.current_context

    def get_last_detection(self) -> Optional[DetectionResult]:
        """Get last detection result"""
        return self.last_detection

    def get_raw_contexts(self) -> Dict[str, any]:
        """
        Get raw context from all detectors without pattern matching

        Returns:
            Dict with raw context data from each detector
        """
        contexts = {}
        for detector in self.detectors:
            if detector.enabled:
                raw = detector.get_raw_context()
                if raw:
                    contexts[detector.name] = raw
        return contexts
