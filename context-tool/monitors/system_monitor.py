"""System-wide clipboard monitoring for text selection"""

import time
import asyncio
import pyperclip
from typing import Callable, Optional
import threading


class SystemMonitor:
    """Monitor system clipboard for text selection changes"""

    def __init__(
        self,
        on_selection: Callable[[str], None],
        poll_interval: float = 0.5,
        min_length: int = 3
    ):
        """
        Initialize system monitor

        Args:
            on_selection: Callback function when new text is selected
            poll_interval: How often to check clipboard (seconds)
            min_length: Minimum text length to trigger analysis
        """
        self.on_selection = on_selection
        self.poll_interval = poll_interval
        self.min_length = min_length
        self.last_text = ""
        self.running = False
        self.thread: Optional[threading.Thread] = None

    def start(self):
        """Start monitoring clipboard"""
        if self.running:
            print("System monitor already running")
            return

        self.running = True
        self.thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self.thread.start()
        print(f"System monitor started (polling every {self.poll_interval}s)")

    def stop(self):
        """Stop monitoring clipboard"""
        self.running = False
        if self.thread:
            self.thread.join(timeout=2)
        print("System monitor stopped")

    def _monitor_loop(self):
        """Main monitoring loop"""
        while self.running:
            try:
                # Get current clipboard content
                current_text = pyperclip.paste()

                # Check if it's new and meets minimum length
                if (current_text and
                    current_text != self.last_text and
                    len(current_text.strip()) >= self.min_length):

                    self.last_text = current_text
                    print(f"New selection detected: {current_text[:50]}...")

                    # Call the callback
                    self.on_selection(current_text)

            except Exception as e:
                print(f"Error reading clipboard: {e}")

            # Wait before next poll
            time.sleep(self.poll_interval)


class AsyncSystemMonitor:
    """Async version of system monitor for use with FastAPI"""

    def __init__(
        self,
        on_selection: Callable[[str], asyncio.Future],
        poll_interval: float = 0.5,
        min_length: int = 3
    ):
        """
        Initialize async system monitor

        Args:
            on_selection: Async callback function when new text is selected
            poll_interval: How often to check clipboard (seconds)
            min_length: Minimum text length to trigger analysis
        """
        self.on_selection = on_selection
        self.poll_interval = poll_interval
        self.min_length = min_length
        self.last_text = ""
        self.running = False
        self.task: Optional[asyncio.Task] = None

    async def start(self):
        """Start monitoring clipboard"""
        if self.running:
            print("Async system monitor already running")
            return

        self.running = True
        self.task = asyncio.create_task(self._monitor_loop())
        print(f"Async system monitor started (polling every {self.poll_interval}s)")

    async def stop(self):
        """Stop monitoring clipboard"""
        self.running = False
        if self.task:
            self.task.cancel()
            try:
                await self.task
            except asyncio.CancelledError:
                pass
        print("Async system monitor stopped")

    async def _monitor_loop(self):
        """Main monitoring loop"""
        while self.running:
            try:
                # Get current clipboard content (run in executor to avoid blocking)
                loop = asyncio.get_event_loop()
                current_text = await loop.run_in_executor(None, pyperclip.paste)

                # Check if it's new and meets minimum length
                if (current_text and
                    current_text != self.last_text and
                    len(current_text.strip()) >= self.min_length):

                    self.last_text = current_text
                    print(f"New selection detected: {current_text[:50]}...")

                    # Call the async callback
                    await self.on_selection(current_text)

            except asyncio.CancelledError:
                break
            except Exception as e:
                print(f"Error reading clipboard: {e}")

            # Wait before next poll
            await asyncio.sleep(self.poll_interval)
