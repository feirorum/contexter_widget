"""Action Wheel Widget - Prototype 1 (Radial Navigation)

A modern circular action wheel with hierarchical radial navigation.
Navigate through matches like a tree: select direction → navigate up/down → expand outward.
"""

import tkinter as tk
from tkinter import ttk, font as tkfont
from typing import Dict, List, Any, Optional, Callable
import math
import webbrowser
import json
from datetime import datetime
import signal
import sys


class ActionWheelWidget:
    """
    Enhanced radial action wheel with tree-like hierarchical navigation
    """

    def __init__(self, on_save_snippet: Optional[Callable] = None):
        self.on_save_snippet = on_save_snippet
        self.current_data = None
        self.matches = []
        self.selected_match_index = 0
        self.navigation_mode = 'wheel'  # 'wheel' or 'matches'
        self.selected_action = None  # Which wheel slice is selected
        self.detail_level = 0  # 0=collapsed, 1=expanded

        # Create window
        self.root = tk.Toplevel()
        self.root.withdraw()  # Start hidden
        self.root.overrideredirect(True)
        self.root.attributes('-topmost', True)

        # Modern color scheme
        self.colors = {
            'primary': '#667eea',
            'secondary': '#764ba2',
            'accent': '#43e97b',
            'contact': '#4facfe',
            'project': '#43e97b',
            'abbreviation': '#fa709a',
            'snippet': '#feca57',
            'bg': '#ffffff',
            'text': '#2d3436',
            'text_light': '#636e72'
        }

        self.wheel_size = 700  # Larger to accommodate everything

        # Modern fonts
        self.title_font = tkfont.Font(family="Segoe UI", size=14, weight="bold")
        self.action_font = tkfont.Font(family="Segoe UI", size=12, weight="bold")
        self.normal_font = tkfont.Font(family="Segoe UI", size=11)
        self.small_font = tkfont.Font(family="Segoe UI", size=10)

        # Build UI
        self.build_wheel()

        # Bind keys
        self.bind_keys()

        # Setup signal handlers for clean Ctrl-C exit
        self.setup_signal_handlers()

    def build_wheel(self):
        """Build the hierarchical navigation wheel"""
        # Main container
        self.container = tk.Frame(
            self.root,
            bg=self.colors['bg'],
            width=self.wheel_size,
            height=self.wheel_size
        )
        self.container.pack()

        # Canvas for drawing
        self.canvas = tk.Canvas(
            self.container,
            width=self.wheel_size,
            height=self.wheel_size,
            bg=self.colors['bg'],
            highlightthickness=0
        )
        self.canvas.pack()

        center = self.wheel_size // 2

        # Selected text area (top)
        self.selected_text_frame = tk.Frame(self.canvas, bg='#f8f9fa', relief=tk.FLAT)
        self.selected_text_label = tk.Label(
            self.selected_text_frame,
            text="",
            font=self.normal_font,
            bg='#f8f9fa',
            fg=self.colors['text'],
            wraplength=600,
            justify=tk.LEFT,
            padx=15,
            pady=10
        )
        self.selected_text_label.pack()
        self.canvas.create_window(center, 60, window=self.selected_text_frame)

        # Central hub
        hub_radius = 60

        # Shadow effect
        for i in range(5, 0, -1):
            gray = 200 + i * 10
            self.canvas.create_oval(
                center - hub_radius - i,
                center - hub_radius - i + 80,
                center + hub_radius + i,
                center + hub_radius + i + 80,
                fill=f'#{gray:02x}{gray:02x}{gray:02x}',
                outline=''
            )

        # Main hub
        self.hub_circle = self.canvas.create_oval(
            center - hub_radius,
            center - hub_radius + 80,
            center + hub_radius,
            center + hub_radius + 80,
            fill=self.colors['primary'],
            outline='white',
            width=2
        )

        self.hub_icon = self.canvas.create_text(
            center,
            center + 70,
            text="🎯",
            font=tkfont.Font(size=28),
            fill='white'
        )

        self.hub_label = self.canvas.create_text(
            center,
            center + 95,
            text="Context",
            font=self.action_font,
            fill='white'
        )

        # Action slices (4 main directions)
        self.action_slices = {
            'matches': {'angle': 0, 'label': 'Matches', 'icon': '📑', 'color': self.colors['primary']},
            'save': {'angle': 90, 'label': 'Save', 'icon': '💾', 'color': self.colors['snippet']},
            'search': {'angle': 180, 'label': 'Search', 'icon': '🔍', 'color': self.colors['contact']},
            'actions': {'angle': 270, 'label': 'Actions', 'icon': '⚡', 'color': self.colors['project']}
        }

        # Detail area (right side) - for expanded info
        self.detail_frame = tk.Frame(self.canvas, bg='white', relief=tk.SOLID, bd=1)
        self.detail_text = tk.Text(
            self.detail_frame,
            width=35,
            height=15,
            font=self.normal_font,
            wrap=tk.WORD,
            padx=15,
            pady=15,
            bg='white',
            relief=tk.FLAT
        )
        self.detail_text.pack()
        # Create window and store ID for later show/hide
        self.detail_window_id = None

        # Match list area (left side) - for showing matches
        self.match_list_frame = tk.Frame(self.canvas, bg='white', relief=tk.SOLID, bd=1)
        self.match_list_window_id = None
        # Will be populated dynamically

        # Info and close buttons
        info_btn = tk.Button(
            self.canvas,
            text="ℹ️",
            font=self.action_font,
            bg=self.colors['bg'],
            fg=self.colors['primary'],
            relief=tk.FLAT,
            cursor='hand2',
            command=self.show_info,
            bd=0
        )
        self.canvas.create_window(30, 30, window=info_btn)

        close_btn = tk.Button(
            self.canvas,
            text="✕",
            font=self.action_font,
            bg=self.colors['bg'],
            fg=self.colors['text_light'],
            relief=tk.FLAT,
            cursor='hand2',
            command=self.hide,
            bd=0
        )
        self.canvas.create_window(self.wheel_size - 30, 30, window=close_btn)

        # Navigation hint
        self.nav_hint = self.canvas.create_text(
            center,
            self.wheel_size - 30,
            text="←→ Select | ↑↓ Navigate | →→ Expand | ESC Close",
            font=self.small_font,
            fill=self.colors['text_light']
        )

    def show(self, result: Dict[str, Any], x: int = None, y: int = None):
        """Show the wheel with analysis results"""
        self.current_data = result
        self.matches = []
        self.selected_match_index = 0
        self.navigation_mode = 'wheel'
        self.selected_action = None
        self.detail_level = 0

        # Update selected text
        selected_text = result.get('selected_text', '')
        display_text = selected_text if len(selected_text) <= 80 else selected_text[:77] + "..."
        self.selected_text_label.config(text=f'"{display_text}"')

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

            if match_type == 'contact':
                icon, label = '👤', data.get('name', 'Unknown')
            elif match_type == 'project':
                icon, label = '📁', data.get('name', 'Project')
            elif match_type == 'snippet':
                icon, label = '📝', 'Snippet'
            else:
                icon, label = '📄', match_type

            self.matches.append({
                'type': match_type,
                'icon': icon,
                'label': label,
                'data': data
            })

        # Initial render
        self.render_wheel()

        # Position window
        if x is None or y is None:
            screen_width = self.root.winfo_screenwidth()
            screen_height = self.root.winfo_screenheight()
            x = (screen_width - self.wheel_size) // 2
            y = (screen_height - self.wheel_size) // 2

        self.root.geometry(f'{self.wheel_size}x{self.wheel_size}+{x}+{y}')
        self.root.deiconify()
        self.root.focus_force()

    def render_wheel(self):
        """Render the wheel based on current navigation state"""
        center = self.wheel_size // 2

        # Clear previous action slice visuals
        self.canvas.delete('action_slice')
        self.canvas.delete('match_item')

        # Remove existing canvas windows if they exist
        if self.detail_window_id:
            self.canvas.delete(self.detail_window_id)
            self.detail_window_id = None

        if self.match_list_window_id:
            self.canvas.delete(self.match_list_window_id)
            self.match_list_window_id = None

        if self.navigation_mode == 'wheel':
            # Show action slices around the hub
            self.render_action_slices(center)

        elif self.navigation_mode == 'matches':
            # Show matches list on left
            self.render_matches_list(center)

            # If detail level > 0, show expanded details on right
            if self.detail_level > 0:
                self.render_match_details(center)

    def render_action_slices(self, center):
        """Render the 4 action slices around the hub"""
        distance = 120

        for action_key, action_info in self.action_slices.items():
            angle = action_info['angle']
            rad = math.radians(angle)

            x = center + distance * math.sin(rad)
            y = center + 80 + distance * -math.cos(rad)

            # Highlight if selected
            is_selected = (self.selected_action == action_key)
            color = action_info['color']
            bg_color = color if is_selected else self.colors['bg']
            text_color = 'white' if is_selected else self.colors['text']
            border_color = color

            # Create slice label
            slice_text = f"{action_info['icon']}\n{action_info['label']}"

            # Background circle for slice
            circle_radius = 40
            circle_id = self.canvas.create_oval(
                x - circle_radius,
                y - circle_radius,
                x + circle_radius,
                y + circle_radius,
                fill=bg_color,
                outline=border_color,
                width=3 if is_selected else 2,
                tags='action_slice'
            )

            # Label
            text_id = self.canvas.create_text(
                x, y,
                text=slice_text,
                font=self.action_font if is_selected else self.normal_font,
                fill=text_color,
                justify=tk.CENTER,
                tags='action_slice'
            )

            # Show match count for matches slice
            if action_key == 'matches':
                count_text = f"({len(self.matches)})"
                self.canvas.create_text(
                    x, y + 30,
                    text=count_text,
                    font=self.small_font,
                    fill=border_color,
                    tags='action_slice'
                )

    def render_matches_list(self, center):
        """Render the list of matches on the left side"""
        # Clear previous match list
        for widget in self.match_list_frame.winfo_children():
            widget.destroy()

        # Title
        title_label = tk.Label(
            self.match_list_frame,
            text=f"📑 Matches ({len(self.matches)})",
            font=self.title_font,
            bg='white',
            fg=self.colors['primary'],
            pady=10
        )
        title_label.pack()

        if not self.matches:
            no_match_label = tk.Label(
                self.match_list_frame,
                text="No matches found",
                font=self.normal_font,
                bg='white',
                fg=self.colors['text_light'],
                pady=20
            )
            no_match_label.pack()
        else:
            # Match items
            for i, match in enumerate(self.matches):
                is_selected = (i == self.selected_match_index)

                match_frame = tk.Frame(
                    self.match_list_frame,
                    bg=self.colors['primary'] if is_selected else 'white',
                    relief=tk.FLAT,
                    bd=0
                )
                match_frame.pack(fill=tk.X, padx=10, pady=5)

                match_label = tk.Label(
                    match_frame,
                    text=f"{match['icon']} {match['label']}",
                    font=self.action_font if is_selected else self.normal_font,
                    bg=self.colors['primary'] if is_selected else 'white',
                    fg='white' if is_selected else self.colors['text'],
                    anchor=tk.W,
                    padx=15,
                    pady=12
                )
                match_label.pack(fill=tk.X)

                # Type badge
                type_label = tk.Label(
                    match_frame,
                    text=match['type'].upper(),
                    font=self.small_font,
                    bg=self.colors['primary'] if is_selected else 'white',
                    fg='white' if is_selected else self.colors[match['type']],
                    padx=5
                )
                type_label.pack(anchor=tk.W, padx=15, pady=(0, 8))

        # Create canvas window and store ID
        self.match_list_window_id = self.canvas.create_window(180, center + 80, window=self.match_list_frame)

    def render_match_details(self, center):
        """Render detailed view of selected match on the right"""
        if not self.matches or self.selected_match_index >= len(self.matches):
            return

        match = self.matches[self.selected_match_index]

        # Clear and populate detail text
        self.detail_text.config(state=tk.NORMAL)
        self.detail_text.delete('1.0', tk.END)

        # Title
        self.detail_text.insert('end', f"{match['icon']} {match['label']}\n", 'title')
        self.detail_text.tag_config('title', font=self.title_font, foreground=self.colors['primary'])

        self.detail_text.insert('end', f"\nType: {match['type'].title()}\n\n", 'subtitle')
        self.detail_text.tag_config('subtitle', font=self.small_font, foreground=self.colors['text_light'])

        # Details based on type
        data = match['data']

        if match['type'] == 'contact':
            self.add_detail_field("Name", data.get('name', ''))
            self.add_detail_field("Email", data.get('email', ''))
            self.add_detail_field("Role", data.get('role', ''))
            self.add_detail_field("Context", data.get('context', ''))

        elif match['type'] == 'abbreviation':
            self.add_detail_field("Abbreviation", data.get('abbr', ''))
            self.add_detail_field("Full Form", data.get('full', ''))
            self.add_detail_field("Definition", data.get('definition', ''))

        elif match['type'] == 'project':
            self.add_detail_field("Name", data.get('name', ''))
            self.add_detail_field("Status", data.get('status', ''))
            self.add_detail_field("Description", data.get('description', ''))

        elif match['type'] == 'snippet':
            text = data.get('text', '')
            lines = text.split('\n')
            if len(lines) > 5:
                preview = '\n'.join(lines[:5]) + f"\n... ({len(lines) - 5} more lines)"
            else:
                preview = text
            self.add_detail_field("Text", preview)

        self.detail_text.config(state=tk.DISABLED)

        # Create canvas window and store ID
        self.detail_window_id = self.canvas.create_window(self.wheel_size - 200, center + 80, window=self.detail_frame)

    def add_detail_field(self, label, value):
        """Add a field to detail text"""
        if value:
            self.detail_text.insert('end', f"{label}:\n", 'field_label')
            self.detail_text.tag_config('field_label', font=self.small_font, foreground=self.colors['text_light'])

            self.detail_text.insert('end', f"{value}\n\n", 'field_value')
            self.detail_text.tag_config('field_value', font=self.normal_font, foreground=self.colors['text'])

    def navigate_left(self):
        """Navigate left in the wheel"""
        if self.navigation_mode == 'wheel':
            # Cycle through action slices counterclockwise
            actions = list(self.action_slices.keys())
            if self.selected_action is None:
                self.selected_action = actions[0]
            else:
                idx = actions.index(self.selected_action)
                self.selected_action = actions[(idx - 1) % len(actions)]
            self.render_wheel()

        elif self.navigation_mode == 'matches' and self.detail_level > 0:
            # Collapse details
            self.detail_level = 0
            self.render_wheel()

    def navigate_right(self):
        """Navigate right in the wheel"""
        if self.navigation_mode == 'wheel':
            # Cycle through action slices clockwise
            actions = list(self.action_slices.keys())
            if self.selected_action is None:
                self.selected_action = actions[0]
            else:
                idx = actions.index(self.selected_action)
                self.selected_action = actions[(idx + 1) % len(actions)]
            self.render_wheel()

        elif self.navigation_mode == 'matches':
            # Expand details
            if self.matches:
                self.detail_level = 1
                self.render_wheel()

    def navigate_up(self):
        """Navigate up"""
        if self.navigation_mode == 'matches' and self.matches:
            # Previous match
            self.selected_match_index = (self.selected_match_index - 1) % len(self.matches)
            self.render_wheel()

    def navigate_down(self):
        """Navigate down"""
        if self.navigation_mode == 'matches' and self.matches:
            # Next match
            self.selected_match_index = (self.selected_match_index + 1) % len(self.matches)
            self.render_wheel()

    def select_action(self):
        """Select/activate current action"""
        if self.navigation_mode == 'wheel' and self.selected_action:
            if self.selected_action == 'matches':
                # Enter matches navigation mode
                self.navigation_mode = 'matches'
                self.detail_level = 0
                self.selected_match_index = 0
                self.render_wheel()
            elif self.selected_action == 'save':
                self.save_snippet()
            elif self.selected_action == 'search':
                self.search_web()
            elif self.selected_action == 'actions':
                self.show_actions_menu()

    def go_back(self):
        """Go back to wheel from matches"""
        if self.navigation_mode == 'matches':
            if self.detail_level > 0:
                # Collapse details first
                self.detail_level = 0
                self.render_wheel()
            else:
                # Back to wheel
                self.navigation_mode = 'wheel'
                self.selected_action = 'matches'
                self.render_wheel()

    def save_snippet(self):
        """Save current selection"""
        if self.current_data and self.on_save_snippet:
            text = self.current_data.get('selected_text', '')
            if text:
                if hasattr(self.on_save_snippet, 'save'):
                    self.on_save_snippet.save(text, 'snippet')
                else:
                    self.on_save_snippet(text)
                self.show_message("Saved!")

    def search_web(self):
        """Search selected text on web"""
        if self.current_data:
            query = self.current_data.get('selected_text', '')
            if query:
                webbrowser.open(f"https://www.google.com/search?q={query.replace(' ', '+')}")

    def show_actions_menu(self):
        """Show additional actions"""
        # Could expand to show copy, export, etc.
        if self.current_data:
            text = self.current_data.get('selected_text', '')
            self.root.clipboard_clear()
            self.root.clipboard_append(text)
            self.show_message("Copied!")

    def show_message(self, text):
        """Show temporary message"""
        msg = self.canvas.create_text(
            self.wheel_size // 2,
            self.wheel_size - 60,
            text=text,
            font=self.action_font,
            fill=self.colors['accent'],
            tags='message'
        )
        self.root.after(2000, lambda: self.canvas.delete('message'))

    def bind_keys(self):
        """Bind keyboard shortcuts"""
        self.root.bind('<Left>', lambda e: self.navigate_left())
        self.root.bind('<Right>', lambda e: self.navigate_right())
        self.root.bind('<Up>', lambda e: self.navigate_up())
        self.root.bind('<Down>', lambda e: self.navigate_down())
        self.root.bind('<Return>', lambda e: self.select_action())
        self.root.bind('<space>', lambda e: self.select_action())
        self.root.bind('<BackSpace>', lambda e: self.go_back())
        self.root.bind('<Escape>', lambda e: self.hide())
        self.root.bind('<F1>', lambda e: self.show_info())

    def hide(self):
        """Hide the wheel"""
        self.root.withdraw()

    def show_info(self):
        """Show information about this prototype"""
        info_text = """
🎯 Action Wheel - Prototype 1

CONCEPT:
Hierarchical radial navigation for context matches.
Navigate through information like a tree using directional keys.

HOW TO USE:
1. Wheel appears showing 4 main slices
2. Use ←→ to select a slice (Matches/Save/Search/Actions)
3. Press ENTER/SPACE to activate selected slice
4. In Matches mode:
   • ↑↓ Navigate through matches
   • → Expand to show full details on right
   • ← Collapse details or go back to wheel
5. BACKSPACE to go back one level

KEYBOARD SHORTCUTS:
• ←→ - Navigate wheel slices (or collapse details)
• ↑↓ - Navigate through matches list
• → - Expand to show full details
• ENTER/SPACE - Select/activate
• BACKSPACE - Go back
• ESC - Close wheel
• F1 - Show this help

NAVIGATION LEVELS:
1. Wheel Mode: Select main action (Matches/Save/Search/Actions)
2. Matches Mode: Browse through all matches
3. Detail Mode: View full information about selected match

SPECIAL FEATURES:
• Selected text displayed at top
• Match count shown on Matches slice
• Hierarchical navigation (tree-like)
• Full keyboard control
• Detail expansion on demand

BEST FOR:
• Users who like radial/circular navigation
• Keyboard-driven workflows
• Organized hierarchical information browsing
• Quick action access combined with deep diving
        """

        info_window = tk.Toplevel(self.root)
        info_window.title("About Action Wheel")
        info_window.geometry("600x800")
        info_window.transient(self.root)
        info_window.attributes('-topmost', True)

        # Center on screen
        x = (info_window.winfo_screenwidth() - 600) // 2
        y = (info_window.winfo_screenheight() - 800) // 2
        info_window.geometry(f"+{x}+{y}")

        text_widget = tk.Text(
            info_window,
            wrap=tk.WORD,
            font=self.normal_font,
            padx=20,
            pady=20,
            bg='#f8f9fa',
            relief=tk.FLAT
        )
        text_widget.pack(fill=tk.BOTH, expand=True)
        text_widget.insert('1.0', info_text)
        text_widget.config(state=tk.DISABLED)

        tk.Button(
            info_window,
            text="Got it!",
            command=info_window.destroy,
            bg=self.colors['primary'],
            fg='white',
            relief=tk.FLAT,
            padx=20,
            pady=10,
            font=self.action_font,
            cursor='hand2'
        ).pack(pady=15)

        info_window.bind('<Escape>', lambda e: info_window.destroy())

    def run(self):
        """Run the main loop"""
        self.root.mainloop()

    def update(self):
        """Update GUI"""
        try:
            self.root.update()
        except tk.TclError:
            pass

    def setup_signal_handlers(self):
        """Setup signal handlers for clean exit on Ctrl-C"""
        signal.signal(signal.SIGINT, self.signal_handler)
        signal.signal(signal.SIGTERM, self.signal_handler)

    def signal_handler(self, sig, frame):
        """Handle interrupt signals (Ctrl-C) gracefully"""
        self.cleanup_and_exit()

    def cleanup_and_exit(self):
        """Clean up resources and exit"""
        try:
            self.root.quit()
            self.root.destroy()
        except:
            pass
        sys.exit(0)
