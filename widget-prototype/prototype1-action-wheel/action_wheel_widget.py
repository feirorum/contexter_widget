"""Action Wheel Widget - Prototype 1

A compact circular action wheel that appears near the cursor when text is selected.
"""

import tkinter as tk
from tkinter import ttk, font as tkfont
from typing import Dict, List, Any, Optional, Callable
import math
import webbrowser


class ActionWheelWidget:
    """
    Radial action wheel widget with quick actions and detected items ring
    """

    def __init__(self, on_save_snippet: Optional[Callable] = None):
        self.on_save_snippet = on_save_snippet
        self.current_data = None
        self.matches = []
        self.selected_index = 0
        self.is_expanded = False

        # Create window
        self.root = tk.Toplevel()
        self.root.withdraw()  # Start hidden
        self.root.overrideredirect(True)  # No window decorations
        self.root.attributes('-topmost', True)
        self.root.attributes('-alpha', 0.95)

        # Styling
        self.bg_color = "#667eea"
        self.fg_color = "#ffffff"
        self.accent_color = "#764ba2"
        self.hub_size = 200
        self.button_size = 50

        # Fonts
        self.action_font = tkfont.Font(family="Helvetica", size=10, weight="bold")
        self.item_font = tkfont.Font(family="Helvetica", size=9)

        # Build UI
        self.build_wheel()

        # Bind keys
        self.bind_keys()

    def build_wheel(self):
        """Build the circular action wheel"""
        # Main container
        self.container = tk.Frame(
            self.root,
            bg=self.bg_color,
            width=self.hub_size,
            height=self.hub_size
        )
        self.container.pack()

        # Canvas for circular layout
        self.canvas = tk.Canvas(
            self.container,
            width=self.hub_size,
            height=self.hub_size,
            bg=self.bg_color,
            highlightthickness=0
        )
        self.canvas.pack()

        # Center hub circle
        center = self.hub_size // 2
        hub_radius = 40

        self.canvas.create_oval(
            center - hub_radius,
            center - hub_radius,
            center + hub_radius,
            center + hub_radius,
            fill=self.accent_color,
            outline="white",
            width=2
        )

        # Quick action buttons in cardinal directions
        self.action_buttons = []
        actions = [
            ("💾", "Save", self.save_snippet, 0),      # North
            ("🔍", "Search", self.search_web, 90),     # East
            ("📋", "Copy", self.copy_to_clipboard, 180),  # South
            ("✕", "Close", self.hide, 270)             # West
        ]

        for icon, label, command, angle in actions:
            self.add_action_button(icon, label, command, angle, center, 70)

        # Detected items ring (outer circle)
        self.item_widgets = []
        self.item_ring_radius = 90

    def add_action_button(self, icon, label, command, angle, center, distance):
        """Add a quick action button at specified angle"""
        # Convert angle to radians
        rad = math.radians(angle)

        # Calculate position
        x = center + distance * math.sin(rad)
        y = center - distance * math.cos(rad)

        # Create button
        btn = tk.Button(
            self.canvas,
            text=icon,
            font=self.action_font,
            bg="white",
            fg=self.bg_color,
            relief=tk.FLAT,
            width=4,
            height=2,
            cursor="hand2",
            command=command
        )

        # Place on canvas
        self.canvas.create_window(x, y, window=btn)
        self.action_buttons.append(btn)

    def show(self, result: Dict[str, Any], x: int = None, y: int = None):
        """
        Show the action wheel with analysis results

        Args:
            result: Analysis result from ContextAnalyzer
            x, y: Position to display (default: center of screen)
        """
        self.current_data = result
        self.matches = []
        self.selected_index = 0

        # Build list of matches
        # Abbreviation first
        if result.get('abbreviation'):
            self.matches.append({
                'type': 'abbreviation',
                'icon': '🟣',
                'label': result['abbreviation']['abbr'],
                'data': result['abbreviation']
            })

        # Exact matches
        for match in result.get('exact_matches', []):
            match_type = match['type']
            data = match['data']

            if match_type == 'contact':
                icon = '👤'
                label = data.get('name', 'Unknown')
            elif match_type == 'snippet':
                icon = '📝'
                label = 'Snippet'
            elif match_type == 'project':
                icon = '📁'
                label = data.get('name', 'Project')
            else:
                icon = '📄'
                label = match_type

            self.matches.append({
                'type': match_type,
                'icon': icon,
                'label': label,
                'data': data
            })

        # Render detected items ring
        self.render_items_ring()

        # Position window
        if x is None or y is None:
            # Center on screen
            screen_width = self.root.winfo_screenwidth()
            screen_height = self.root.winfo_screenheight()
            x = (screen_width - self.hub_size) // 2
            y = (screen_height - self.hub_size) // 2

        # Adjust if would go off-screen
        if x + self.hub_size > self.root.winfo_screenwidth():
            x = self.root.winfo_screenwidth() - self.hub_size - 20
        if y + self.hub_size > self.root.winfo_screenheight():
            y = self.root.winfo_screenheight() - self.hub_size - 20
        if x < 20:
            x = 20
        if y < 20:
            y = 20

        self.root.geometry(f'{self.hub_size}x{self.hub_size}+{x}+{y}')
        self.root.deiconify()
        self.root.focus_force()

    def render_items_ring(self):
        """Render detected items as segments around outer ring"""
        # Clear existing
        for widget in self.item_widgets:
            self.canvas.delete(widget)
        self.item_widgets.clear()

        if not self.matches:
            return

        center = self.hub_size // 2
        count = min(len(self.matches), 6)  # Max 6 items

        for i in range(count):
            match = self.matches[i]
            angle = (360 / count) * i
            rad = math.radians(angle)

            # Position
            x = center + self.item_ring_radius * math.sin(rad)
            y = center - self.item_ring_radius * math.cos(rad)

            # Highlight if selected
            bg = "#ffffff" if i == self.selected_index else "#f0f0f0"
            border_color = self.accent_color if i == self.selected_index else "#cccccc"

            # Create item label
            item_text = f"{match['icon']}\n{self.truncate(match['label'], 8)}"

            label_id = self.canvas.create_text(
                x, y,
                text=item_text,
                font=self.item_font,
                fill="#333333" if i != self.selected_index else self.accent_color,
                justify=tk.CENTER
            )

            # Create background circle
            bbox = self.canvas.bbox(label_id)
            if bbox:
                padding = 8
                circle_id = self.canvas.create_oval(
                    bbox[0] - padding,
                    bbox[1] - padding,
                    bbox[2] + padding,
                    bbox[3] + padding,
                    fill=bg,
                    outline=border_color,
                    width=2
                )

                # Lower circle behind text
                self.canvas.tag_lower(circle_id, label_id)
                self.item_widgets.append(circle_id)

            self.item_widgets.append(label_id)

            # Bind click
            self.canvas.tag_bind(label_id, '<Button-1>', lambda e, idx=i: self.select_item(idx))

    def truncate(self, text: str, max_len: int = 12) -> str:
        """Truncate text to max length"""
        if len(text) <= max_len:
            return text
        return text[:max_len-2] + ".."

    def select_item(self, index: int):
        """Select an item from the ring"""
        if 0 <= index < len(self.matches):
            self.selected_index = index
            self.render_items_ring()

    def navigate(self, direction: int):
        """Navigate items with arrow keys"""
        if not self.matches:
            return

        self.selected_index = (self.selected_index + direction) % len(self.matches)
        self.render_items_ring()

    def expand_details(self):
        """Expand to show details of selected item"""
        if not self.matches or self.selected_index >= len(self.matches):
            return

        match = self.matches[self.selected_index]

        # Create details popup
        self.show_details_popup(match)

    def show_details_popup(self, match: Dict):
        """Show details popup for selected match"""
        # Create popup window
        popup = tk.Toplevel(self.root)
        popup.title("Details")
        popup.geometry("400x300")
        popup.transient(self.root)
        popup.attributes('-topmost', True)

        # Position near wheel
        wheel_x = self.root.winfo_x()
        wheel_y = self.root.winfo_y()
        popup.geometry(f"+{wheel_x + self.hub_size + 10}+{wheel_y}")

        # Content frame
        content = tk.Frame(popup, bg="white", padx=20, pady=20)
        content.pack(fill=tk.BOTH, expand=True)

        # Title
        title_label = tk.Label(
            content,
            text=f"{match['icon']} {match['label']}",
            font=tkfont.Font(family="Helvetica", size=14, weight="bold"),
            bg="white",
            fg="#333333"
        )
        title_label.pack(anchor=tk.W, pady=(0, 10))

        # Type badge
        type_label = tk.Label(
            content,
            text=match['type'].upper(),
            font=tkfont.Font(family="Helvetica", size=9),
            bg=self.bg_color,
            fg="white",
            padx=8,
            pady=4
        )
        type_label.pack(anchor=tk.W, pady=(0, 10))

        # Details
        data = match['data']
        detail_text = tk.Text(
            content,
            wrap=tk.WORD,
            font=tkfont.Font(family="Helvetica", size=10),
            bg="#f8f9fa",
            relief=tk.FLAT,
            padx=10,
            pady=10
        )
        detail_text.pack(fill=tk.BOTH, expand=True)

        # Render details based on type
        details = self.format_details(match['type'], data)
        detail_text.insert('1.0', details)
        detail_text.config(state=tk.DISABLED)

        # Close button
        close_btn = tk.Button(
            content,
            text="Close",
            command=popup.destroy,
            bg=self.bg_color,
            fg="white",
            relief=tk.FLAT,
            padx=20,
            pady=8
        )
        close_btn.pack(pady=(10, 0))

        # ESC to close
        popup.bind('<Escape>', lambda e: popup.destroy())

    def format_details(self, match_type: str, data: Dict) -> str:
        """Format details text for display"""
        lines = []

        if match_type == 'contact':
            if data.get('name'):
                lines.append(f"Name: {data['name']}")
            if data.get('email'):
                lines.append(f"Email: {data['email']}")
            if data.get('role'):
                lines.append(f"Role: {data['role']}")
            if data.get('context'):
                lines.append(f"\nContext:\n{data['context']}")

        elif match_type == 'abbreviation':
            if data.get('full'):
                lines.append(f"{data.get('abbr', '')} = {data['full']}")
            if data.get('definition'):
                lines.append(f"\n{data['definition']}")
            if data.get('category'):
                lines.append(f"\nCategory: {data['category']}")

        elif match_type == 'project':
            if data.get('name'):
                lines.append(f"Project: {data['name']}")
            if data.get('status'):
                lines.append(f"Status: {data['status']}")
            if data.get('description'):
                lines.append(f"\n{data['description']}")

        else:
            # Generic display
            for key, value in data.items():
                if key != 'id' and value:
                    lines.append(f"{key.replace('_', ' ').title()}: {value}")

        return '\n'.join(lines) if lines else "No details available"

    def bind_keys(self):
        """Bind keyboard shortcuts"""
        self.root.bind('<Up>', lambda e: self.navigate(-1))
        self.root.bind('<Down>', lambda e: self.navigate(1))
        self.root.bind('<Right>', lambda e: self.expand_details())
        self.root.bind('<Return>', lambda e: self.expand_details())
        self.root.bind('<Escape>', lambda e: self.hide())
        self.root.bind('s', lambda e: self.save_snippet())
        self.root.bind('w', lambda e: self.search_web())
        self.root.bind('c', lambda e: self.copy_to_clipboard())

    def save_snippet(self):
        """Save current text as snippet"""
        if self.current_data and self.on_save_snippet:
            text = self.current_data.get('selected_text', '')
            if text:
                if hasattr(self.on_save_snippet, 'save'):
                    self.on_save_snippet.save(text, 'snippet')
                    self.show_toast("Snippet saved!")
                else:
                    self.on_save_snippet(text)
                    self.show_toast("Snippet saved!")

    def search_web(self):
        """Search selected text on web"""
        if self.current_data:
            query = self.current_data.get('selected_text', '')
            if query:
                url = f"https://www.google.com/search?q={query.replace(' ', '+')}"
                webbrowser.open(url)
                self.show_toast("Opened web search")

    def copy_to_clipboard(self):
        """Copy to clipboard"""
        if self.current_data:
            text = self.current_data.get('selected_text', '')
            if text:
                self.root.clipboard_clear()
                self.root.clipboard_append(text)
                self.show_toast("Copied to clipboard!")

    def show_toast(self, message: str):
        """Show temporary toast message"""
        toast = tk.Label(
            self.canvas,
            text=message,
            font=self.item_font,
            bg="#4CAF50",
            fg="white",
            padx=10,
            pady=5
        )

        center = self.hub_size // 2
        toast_id = self.canvas.create_window(center, center, window=toast)

        # Auto-hide after 2 seconds
        self.root.after(2000, lambda: self.canvas.delete(toast_id))

    def hide(self):
        """Hide the action wheel"""
        self.root.withdraw()

    def update(self):
        """Update GUI (for integration with event loop)"""
        try:
            self.root.update()
        except tk.TclError:
            pass
