"""Smart Context Bar Widget - Prototype 4

A compact bar appearing above/below selected text, like IDE hints.
"""

import tkinter as tk
from tkinter import font as tkfont
from typing import Dict, List, Any, Optional, Callable
import webbrowser


class ContextBarWidget:
    """Inline context bar appearing near selection"""

    def __init__(self, on_save_snippet: Optional[Callable] = None):
        self.on_save_snippet = on_save_snippet
        self.current_data = None
        self.matches = []
        self.current_index = 0
        self.is_expanded = False

        # Create compact bar window
        self.bar_window = tk.Toplevel()
        self.bar_window.withdraw()
        self.bar_window.overrideredirect(True)
        self.bar_window.attributes('-topmost', True)

        # Styling
        self.bg_color = "#ffffff"
        self.primary_color = "#667eea"
        self.bar_width = 300
        self.bar_height = 40

        # Fonts
        self.normal_font = tkfont.Font(family="Helvetica", size=10)
        self.small_font = tkfont.Font(family="Helvetica", size=9)

        # Build bar
        self.build_bar()

        # Expanded popup (created on demand)
        self.popup_window = None

        # Bind keys
        self.bind_keys()

    def build_bar(self):
        """Build compact context bar"""
        self.bar_frame = tk.Frame(
            self.bar_window,
            bg=self.bg_color,
            relief=tk.RAISED,
            bd=1,
            highlightbackground='#e0e0e0',
            highlightthickness=1
        )
        self.bar_frame.pack(fill=tk.BOTH, expand=True)

        # Content frame
        content = tk.Frame(self.bar_frame, bg=self.bg_color)
        content.pack(fill=tk.BOTH, expand=True, padx=10, pady=8)

        # Match label
        self.match_label = tk.Label(
            content,
            text="",
            font=self.normal_font,
            bg=self.bg_color,
            fg='#333',
            anchor=tk.W
        )
        self.match_label.pack(side=tk.LEFT, fill=tk.X, expand=True)

        # Navigation indicator
        self.nav_label = tk.Label(
            content,
            text="",
            font=self.small_font,
            bg=self.bg_color,
            fg='#999'
        )
        self.nav_label.pack(side=tk.RIGHT, padx=(5, 0))

        # Expand button
        self.expand_btn = tk.Button(
            content,
            text="▼",
            font=self.small_font,
            bg=self.bg_color,
            fg=self.primary_color,
            relief=tk.FLAT,
            cursor='hand2',
            command=self.toggle_expand
        )
        self.expand_btn.pack(side=tk.RIGHT)

    def show(self, result: Dict[str, Any], x: int = None, y: int = None):
        """Show context bar with results"""
        self.current_data = result
        self.matches = []
        self.current_index = 0

        # Build matches list
        if result.get('abbreviation'):
            self.matches.append({
                'type': 'abbreviation',
                'icon': '🟣',
                'label': result['abbreviation']['abbr'],
                'data': result['abbreviation']
            })

        for match in result.get('exact_matches', []):
            match_type = match['type']
            data = match['data']
            icon = {'contact': '👤', 'project': '📁', 'snippet': '📝'}.get(match_type, '📄')

            if match_type == 'contact':
                label = data.get('name', 'Unknown')
            elif match_type == 'project':
                label = data.get('name', 'Project')
            else:
                label = match_type

            self.matches.append({
                'type': match_type,
                'icon': icon,
                'label': label,
                'data': data
            })

        if not self.matches:
            self.matches.append({
                'type': 'none',
                'icon': 'ℹ️',
                'label': 'No context found',
                'data': {}
            })

        # Update display
        self.update_bar_display()

        # Position bar
        if x is None or y is None:
            # Center on screen
            screen_width = self.bar_window.winfo_screenwidth()
            screen_height = self.bar_window.winfo_screenheight()
            x = (screen_width - self.bar_width) // 2
            y = (screen_height - self.bar_height) // 2
        else:
            # Position near selection (above)
            y = y - self.bar_height - 10

            # Adjust if off-screen
            if y < 20:
                y = y + self.bar_height + 30  # Below instead

        self.bar_window.geometry(f'{self.bar_width}x{self.bar_height}+{x}+{y}')
        self.bar_window.deiconify()

        # Auto-hide after 5 seconds
        self.bar_window.after(5000, self.hide)

    def update_bar_display(self):
        """Update bar display with current match"""
        if not self.matches:
            return

        match = self.matches[self.current_index]

        # Update label
        label_text = f"{match['icon']} {match['label']} ({match['type'].title()})"
        self.match_label.config(text=label_text)

        # Update navigation
        if len(self.matches) > 1:
            nav_text = f"[{self.current_index + 1}/{len(self.matches)}]"
            self.nav_label.config(text=nav_text)
        else:
            self.nav_label.config(text="")

    def cycle_match(self, direction: int = 1):
        """Cycle through matches"""
        if not self.matches or len(self.matches) <= 1:
            return

        self.current_index = (self.current_index + direction) % len(self.matches)
        self.update_bar_display()

    def toggle_expand(self):
        """Toggle expanded view"""
        if self.is_expanded:
            self.collapse()
        else:
            self.expand()

    def expand(self):
        """Expand to show full details"""
        if not self.matches:
            return

        self.is_expanded = True
        match = self.matches[self.current_index]

        # Create popup window
        if self.popup_window:
            self.popup_window.destroy()

        self.popup_window = tk.Toplevel(self.bar_window)
        self.popup_window.title("Details")
        self.popup_window.overrideredirect(True)
        self.popup_window.attributes('-topmost', True)

        # Position near bar
        bar_x = self.bar_window.winfo_x()
        bar_y = self.bar_window.winfo_y()

        popup_width = 400
        popup_height = 300

        self.popup_window.geometry(f'{popup_width}x{popup_height}+{bar_x}+{bar_y + self.bar_height + 5}')

        # Content frame
        frame = tk.Frame(self.popup_window, bg='white', relief=tk.RAISED, bd=1)
        frame.pack(fill=tk.BOTH, expand=True)

        # Header
        header = tk.Frame(frame, bg=self.primary_color, height=50)
        header.pack(fill=tk.X)
        header.pack_propagate(False)

        tk.Label(
            header,
            text=f"{match['icon']} {match['label']}",
            font=tkfont.Font(family="Helvetica", size=12, weight="bold"),
            bg=self.primary_color,
            fg='white'
        ).pack(side=tk.LEFT, padx=15, pady=12)

        tk.Button(
            header,
            text="▲",
            font=self.small_font,
            bg=self.primary_color,
            fg='white',
            relief=tk.FLAT,
            command=self.collapse
        ).pack(side=tk.RIGHT, padx=15)

        # Details
        details_frame = tk.Frame(frame, bg='white', padx=15, pady=15)
        details_frame.pack(fill=tk.BOTH, expand=True)

        details_text = self.format_details(match['type'], match['data'])

        tk.Label(
            details_frame,
            text=details_text,
            font=self.normal_font,
            bg='white',
            fg='#333',
            justify=tk.LEFT,
            anchor=tk.NW,
            wraplength=360
        ).pack(fill=tk.BOTH, expand=True)

        # Actions
        actions = tk.Frame(frame, bg='#f5f5f5')
        actions.pack(fill=tk.X, padx=15, pady=10)

        tk.Button(
            actions,
            text="💾 Save",
            font=self.small_font,
            bg=self.primary_color,
            fg='white',
            relief=tk.FLAT,
            padx=10,
            pady=5,
            command=self.save_snippet
        ).pack(side=tk.LEFT, padx=(0, 5))

        tk.Button(
            actions,
            text="🔍 Search",
            font=self.small_font,
            bg=self.primary_color,
            fg='white',
            relief=tk.FLAT,
            padx=10,
            pady=5,
            command=self.search_web
        ).pack(side=tk.LEFT, padx=5)

        tk.Button(
            actions,
            text="📋 Copy",
            font=self.small_font,
            bg=self.primary_color,
            fg='white',
            relief=tk.FLAT,
            padx=10,
            pady=5,
            command=self.copy_to_clipboard
        ).pack(side=tk.LEFT, padx=5)

        # Update button
        self.expand_btn.config(text="▲")

    def collapse(self):
        """Collapse back to bar"""
        self.is_expanded = False
        if self.popup_window:
            self.popup_window.destroy()
            self.popup_window = None
        self.expand_btn.config(text="▼")

    def format_details(self, match_type: str, data: Dict) -> str:
        """Format details for display"""
        lines = []

        if match_type == 'contact':
            for key in ['name', 'email', 'role', 'last_contact']:
                if data.get(key):
                    lines.append(f"{key.replace('_', ' ').title()}: {data[key]}")

        elif match_type == 'abbreviation':
            if data.get('full'):
                lines.append(f"{data.get('abbr', '')} = {data['full']}")
            if data.get('definition'):
                lines.append(f"\n{data['definition']}")

        elif match_type == 'project':
            for key in ['name', 'status', 'description']:
                if data.get(key):
                    lines.append(f"{key.title()}: {data[key]}")

        return '\n\n'.join(lines) if lines else "No details available"

    def save_snippet(self):
        """Save as snippet"""
        if self.current_data and self.on_save_snippet:
            text = self.current_data.get('selected_text', '')
            if text:
                if hasattr(self.on_save_snippet, 'save'):
                    self.on_save_snippet.save(text, 'snippet')
                else:
                    self.on_save_snippet(text)

    def search_web(self):
        """Search web"""
        if self.current_data:
            query = self.current_data.get('selected_text', '')
            if query:
                webbrowser.open(f"https://www.google.com/search?q={query.replace(' ', '+')}")

    def copy_to_clipboard(self):
        """Copy to clipboard"""
        if self.current_data:
            text = self.current_data.get('selected_text', '')
            if text:
                self.bar_window.clipboard_clear()
                self.bar_window.clipboard_append(text)

    def bind_keys(self):
        """Bind keyboard shortcuts"""
        self.bar_window.bind('<Tab>', lambda e: self.cycle_match(1))
        self.bar_window.bind('<Down>', lambda e: self.cycle_match(1))
        self.bar_window.bind('<Up>', lambda e: self.cycle_match(-1))
        self.bar_window.bind('<Right>', lambda e: self.expand())
        self.bar_window.bind('<Return>', lambda e: self.expand())
        self.bar_window.bind('<Left>', lambda e: self.collapse())
        self.bar_window.bind('<Escape>', lambda e: self.hide())
        self.bar_window.bind('<Control-s>', lambda e: self.save_snippet())

    def hide(self):
        """Hide the bar"""
        self.collapse()
        self.bar_window.withdraw()

    def update(self):
        """Update GUI"""
        try:
            self.bar_window.update()
        except tk.TclError:
            pass
