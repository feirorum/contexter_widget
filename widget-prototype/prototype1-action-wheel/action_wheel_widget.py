"""Action Wheel Widget - Prototype 1 (Enhanced)

A modern circular action wheel with glassmorphism effects, smooth animations,
and enhanced functionality for context analysis.
"""

import tkinter as tk
from tkinter import ttk, font as tkfont
from typing import Dict, List, Any, Optional, Callable
import math
import webbrowser
import json
from datetime import datetime


class ActionWheelWidget:
    """
    Enhanced radial action wheel widget with modern UI and advanced features
    """

    def __init__(self, on_save_snippet: Optional[Callable] = None):
        self.on_save_snippet = on_save_snippet
        self.current_data = None
        self.matches = []
        self.selected_index = 0
        self.is_expanded = False
        self.history = []  # Recent analyses
        self.favorites = []  # Pinned items
        self.show_history = False

        # Create window
        self.root = tk.Toplevel()
        self.root.withdraw()  # Start hidden
        self.root.overrideredirect(True)  # No window decorations
        self.root.attributes('-topmost', True)
        self.root.attributes('-alpha', 0.95)
        # Use window-level alpha for translucency (cross-platform)
        # This gives a global transparency which we can use to simulate
        # semi-transparent shadows and overlays without per-item alpha.
        try:
            self.root.wm_attributes('-alpha', 0.95)
        except Exception:
            # wm_attributes may not be supported on some platforms; ignore safely
            pass

        # Modern color scheme with gradients
        self.color_scheme = {
            'primary': '#667eea',
            'secondary': '#764ba2',
            'accent': '#f093fb',
            'contact': '#4facfe',
            'project': '#43e97b',
            'abbreviation': '#fa709a',
            'snippet': '#feca57',
            'bg_light': '#ffffff',
            'bg_dark': '#f8f9fa',
            'text_primary': '#2d3436',
            'text_secondary': '#636e72'
        }

        self.hub_size = 280  # Larger for modern look
        self.button_size = 60

        # Modern fonts
        self.action_font = tkfont.Font(family="Segoe UI", size=12, weight="bold")
        self.item_font = tkfont.Font(family="Segoe UI", size=10)
        self.title_font = tkfont.Font(family="Segoe UI", size=11, weight="bold")

        # Build UI
        self.build_wheel()

        # Bind keys
        self.bind_keys()

    def build_wheel(self):
        """Build the enhanced circular action wheel"""
        # Main container with modern shadow effect
        self.container = tk.Frame(
            self.root,
            bg=self.color_scheme['bg_light'],
            width=self.hub_size,
            height=self.hub_size,
            highlightthickness=0
        )
        self.container.pack(padx=8, pady=8)

        # Canvas for circular layout with modern styling
        self.canvas = tk.Canvas(
            self.container,
            width=self.hub_size,
            height=self.hub_size,
            bg=self.color_scheme['bg_light'],
            highlightthickness=3,
            highlightbackground='#e0e0e0'
        )
        self.canvas.pack()

        # Center hub circle with modern gradient effect
        center = self.hub_size // 2
        hub_radius = 50

        # Shadow circles (layered for depth)
        for i in range(5, 0, -1):
            gray_val = 200 + i * 10
            self.canvas.create_oval(
                center - hub_radius - i,
                center - hub_radius - i,
                center + hub_radius + i,
                center + hub_radius + i,
                fill=f'#{gray_val:02x}{gray_val:02x}{gray_val:02x}',
                outline=''
            )

        # Main hub with modern flat design
        self.hub_circle = self.canvas.create_oval(
            center - hub_radius,
            center - hub_radius,
            center + hub_radius,
            center + hub_radius,
            fill=self.color_scheme['primary'],
            outline='',
            width=0
        )

        # Inner highlight circle for depth
        self.canvas.create_oval(
            center - hub_radius + 3,
            center - hub_radius + 3,
            center + hub_radius - 3,
            center + hub_radius - 3,
            fill='',
            outline='white',
            width=1
        )

        # Hub icon/text with modern styling
        self.hub_text = self.canvas.create_text(
            center,
            center - 12,
            text="🎯",
            font=tkfont.Font(size=24),
            fill='white'
        )

        self.hub_label = self.canvas.create_text(
            center,
            center + 18,
            text="Actions",
            font=tkfont.Font(family="Segoe UI", size=10, weight="bold"),
            fill='white'
        )

        # Make hub clickable for settings
        self.canvas.tag_bind(self.hub_circle, '<Button-1>', lambda e: self.toggle_history())
        self.canvas.tag_bind(self.hub_text, '<Button-1>', lambda e: self.toggle_history())
        self.canvas.tag_bind(self.hub_label, '<Button-1>', lambda e: self.toggle_history())

        # Enhanced action buttons with better icons and colors
        self.action_buttons = []
        actions = [
            ("💾", "Save", self.save_snippet, 0, self.color_scheme['snippet']),
            ("🔍", "Search", self.search_web, 90, self.color_scheme['contact']),
            ("📋", "Copy", self.copy_to_clipboard, 180, self.color_scheme['project']),
            ("⭐", "Pin", self.pin_item, 270, self.color_scheme['abbreviation'])
        ]

        for icon, label, command, angle, color in actions:
            self.add_action_button(icon, label, command, angle, center, 85, color)

        # Detected items ring (outer circle)
        self.item_widgets = []
        self.item_ring_radius = 100

        # Info button (top-left corner)
        info_btn = tk.Button(
            self.canvas,
            text="ℹ️",
            font=self.action_font,
            bg=self.color_scheme['bg_light'],
            fg=self.color_scheme['primary'],
            relief=tk.FLAT,
            cursor="hand2",
            command=self.show_info,
            bd=0
        )
        self.canvas.create_window(20, 20, window=info_btn)

        # Close button (top-right corner)
        close_btn = tk.Button(
            self.canvas,
            text="✕",
            font=self.action_font,
            bg=self.color_scheme['bg_light'],
            fg=self.color_scheme['text_secondary'],
            relief=tk.FLAT,
            cursor="hand2",
            command=self.hide,
            bd=0
        )
        self.canvas.create_window(self.hub_size - 20, 20, window=close_btn)

    def add_action_button(self, icon, label, command, angle, center, distance, color):
        """Add an enhanced action button at specified angle"""
        rad = math.radians(angle)

        # Calculate position
        x = center + distance * math.sin(rad)
        y = center - distance * math.cos(rad)

        # Create button frame for shadow effect
        btn_frame = tk.Frame(self.canvas, bg=self.color_scheme['bg_light'])

        # Create button with modern flat design
        btn = tk.Button(
            btn_frame,
            text=f"{icon}\n{label}",
            font=self.action_font,
            bg=color,
            fg='white',
            activebackground=self.darken_color(color),
            activeforeground='white',
            relief=tk.FLAT,
            width=7,
            height=3,
            cursor="hand2",
            command=command,
            bd=0,
            padx=8,
            pady=8,
            highlightthickness=0
        )
        btn.pack()

        # Modern hover effect
        btn.bind('<Enter>', lambda e: btn.config(bg=self.lighten_color(color), font=tkfont.Font(family="Segoe UI", size=13, weight="bold")))
        btn.bind('<Leave>', lambda e: btn.config(bg=color, font=self.action_font))

        # Place on canvas
        self.canvas.create_window(x, y, window=btn_frame)
        self.action_buttons.append(btn)

    def darken_color(self, hex_color, factor=0.8):
        """Darken a hex color"""
        hex_color = hex_color.lstrip('#')
        r, g, b = int(hex_color[0:2], 16), int(hex_color[2:4], 16), int(hex_color[4:6], 16)
        r, g, b = int(r * factor), int(g * factor), int(b * factor)
        return f'#{r:02x}{g:02x}{b:02x}'

    def lighten_color(self, hex_color, factor=1.2):
        """Lighten a hex color"""
        hex_color = hex_color.lstrip('#')
        r, g, b = int(hex_color[0:2], 16), int(hex_color[2:4], 16), int(hex_color[4:6], 16)
        r, g, b = min(255, int(r * factor)), min(255, int(g * factor)), min(255, int(b * factor))
        return f'#{r:02x}{g:02x}{b:02x}'

    def show(self, result: Dict[str, Any], x: int = None, y: int = None):
        """
        Show the action wheel with analysis results and smooth animation

        Args:
            result: Analysis result from ContextAnalyzer
            x, y: Position to display (default: center of screen)
        """
        self.current_data = result
        self.matches = []
        self.selected_index = 0

        # Add to history
        if result not in self.history:
            self.history.insert(0, result)
            self.history = self.history[:10]  # Keep last 10

        # Build list of matches with confidence scores
        if result.get('abbreviation'):
            self.matches.append({
                'type': 'abbreviation',
                'icon': '🟣',
                'label': result['abbreviation']['abbr'],
                'data': result['abbreviation'],
                'confidence': 0.95
            })

        # Exact matches
        for match in result.get('exact_matches', []):
            match_type = match['type']
            data = match['data']
            confidence = match.get('confidence', 0.9)

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
                'data': data,
                'confidence': confidence
            })

        # Render detected items ring
        self.render_items_ring()

        # Position window
        if x is None or y is None:
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

        # Animate appearance
        self.root.attributes('-alpha', 0.0)
        self.root.deiconify()
        self.root.focus_force()
        self.animate_fade_in()

    def animate_fade_in(self, alpha=0.0):
        """Smooth fade-in animation"""
        if alpha < 0.95:
            alpha += 0.15
            self.root.attributes('-alpha', alpha)
            self.root.after(20, lambda: self.animate_fade_in(alpha))

    def render_items_ring(self):
        """Render detected items as enhanced segments around outer ring"""
        # Clear existing
        for widget in self.item_widgets:
            self.canvas.delete(widget)
        self.item_widgets.clear()

        if not self.matches:
            # No matches message
            msg_id = self.canvas.create_text(
                self.hub_size // 2,
                self.hub_size - 30,
                text="No matches found",
                font=self.item_font,
                fill=self.color_scheme['text_secondary']
            )
            self.item_widgets.append(msg_id)
            return

        center = self.hub_size // 2
        count = min(len(self.matches), 8)  # Max 8 items

        for i in range(count):
            match = self.matches[i]
            angle = (360 / count) * i
            rad = math.radians(angle)

            # Position
            x = center + self.item_ring_radius * math.sin(rad)
            y = center - self.item_ring_radius * math.cos(rad)

            # Get type color
            type_color = self.color_scheme.get(match['type'], self.color_scheme['text_primary'])

            # Highlight if selected
            is_selected = (i == self.selected_index)
            bg = type_color if is_selected else self.color_scheme['bg_light']
            text_color = 'white' if is_selected else self.color_scheme['text_primary']
            border_color = type_color

            # Create item label with confidence indicator
            confidence = match.get('confidence', 0)
            confidence_bar = '█' * int(confidence * 5)
            item_text = f"{match['icon']}\n{self.truncate(match['label'], 10)}"

            # Add to favorites indicator
            if self.is_favorite(match):
                item_text = f"⭐{match['icon']}\n{self.truncate(match['label'], 10)}"

            label_id = self.canvas.create_text(
                x, y,
                text=item_text,
                font=self.item_font,
                fill=text_color,
                justify=tk.CENTER
            )

            # Create background circle with shadow effect
            bbox = self.canvas.bbox(label_id)
            if bbox:
                padding = 10

                # Shadow
                shadow_id = self.canvas.create_oval(
                    bbox[0] - padding + 2,
                    bbox[1] - padding + 2,
                    bbox[2] + padding + 2,
                    bbox[3] + padding + 2,
                    fill='#333333',
                    outline=''
                )

                # Main circle
                circle_id = self.canvas.create_oval(
                    bbox[0] - padding,
                    bbox[1] - padding,
                    bbox[2] + padding,
                    bbox[3] + padding,
                    fill=bg,
                    outline=border_color,
                    width=2
                )

                # Lower behind text
                self.canvas.tag_lower(shadow_id, label_id)
                self.canvas.tag_lower(circle_id, label_id)
                self.item_widgets.append(shadow_id)
                self.item_widgets.append(circle_id)

            self.item_widgets.append(label_id)

            # Bind click and hover
            self.canvas.tag_bind(label_id, '<Button-1>', lambda e, idx=i: self.select_item(idx))
            self.canvas.tag_bind(label_id, '<Button-3>', lambda e, idx=i: self.show_item_context_menu(e, idx))
            self.canvas.tag_bind(label_id, '<Enter>', lambda e, idx=i: self.on_item_hover(idx))

    def is_favorite(self, match: Dict) -> bool:
        """Check if item is in favorites"""
        for fav in self.favorites:
            if fav.get('label') == match.get('label') and fav.get('type') == match.get('type'):
                return True
        return False

    def on_item_hover(self, index: int):
        """Show quick preview on hover"""
        if 0 <= index < len(self.matches):
            match = self.matches[index]
            # Could show a tooltip here in future enhancement
            pass

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
        self.show_details_popup(match)

    def show_details_popup(self, match: Dict):
        """Show enhanced details popup for selected match"""
        popup = tk.Toplevel(self.root)
        popup.title("Details")
        popup.geometry("450x350")
        popup.transient(self.root)
        popup.attributes('-topmost', True)

        # Position near wheel
        wheel_x = self.root.winfo_x()
        wheel_y = self.root.winfo_y()
        popup.geometry(f"+{wheel_x + self.hub_size + 10}+{wheel_y}")

        # Header with gradient effect (simulated)
        header = tk.Frame(popup, bg=self.color_scheme['primary'], height=70)
        header.pack(fill=tk.X)
        header.pack_propagate(False)

        # Title with type badge
        title_frame = tk.Frame(header, bg=self.color_scheme['primary'])
        title_frame.pack(fill=tk.X, padx=20, pady=15)

        tk.Label(
            title_frame,
            text=f"{match['icon']} {match['label']}",
            font=tkfont.Font(family="Helvetica", size=16, weight="bold"),
            bg=self.color_scheme['primary'],
            fg="white"
        ).pack(side=tk.LEFT)

        # Type badge
        type_color = self.color_scheme.get(match['type'], self.color_scheme['text_primary'])
        type_badge = tk.Label(
            title_frame,
            text=match['type'].upper(),
            font=tkfont.Font(family="Helvetica", size=9),
            bg=type_color,
            fg="white",
            padx=8,
            pady=4
        )
        type_badge.pack(side=tk.RIGHT)

        # Content frame
        content = tk.Frame(popup, bg="white", padx=20, pady=20)
        content.pack(fill=tk.BOTH, expand=True)

        # Confidence row
        conf_frame = tk.Frame(content, bg='white')
        conf_frame.pack(fill=tk.X, pady=(0, 10))

        tk.Label(
            conf_frame,
            text=f"Confidence: {int(match.get('confidence', 0) * 100)}%",
            font=self.item_font,
            bg='white',
            fg=self.color_scheme['text_secondary']
        ).pack(side=tk.LEFT)

        # Progress bar
        conf_bar = tk.Canvas(conf_frame, height=8, bg='#e0e0e0', highlightthickness=0)
        conf_bar.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=10)
        bar_width = int(300 * match.get('confidence', 0))
        conf_bar.create_rectangle(0, 0, bar_width, 8, fill=self.color_scheme['project'], outline='')

        # Details text
        data = match['data']
        detail_text = tk.Text(
            content,
            wrap=tk.WORD,
            font=tkfont.Font(family="Helvetica", size=10),
            bg="#f8f9fa",
            relief=tk.FLAT,
            padx=15,
            pady=15
        )
        detail_text.pack(fill=tk.BOTH, expand=True)

        details = self.format_details(match['type'], data)
        detail_text.insert('1.0', details)
        detail_text.config(state=tk.DISABLED)

        # Action buttons
        actions_frame = tk.Frame(content, bg='white')
        actions_frame.pack(pady=(10, 0))

        # Copy JSON button
        tk.Button(
            actions_frame,
            text="📋 Copy JSON",
            command=lambda: self.copy_as_json(data),
            bg=self.color_scheme['contact'],
            fg="white",
            relief=tk.FLAT,
            padx=15,
            pady=8,
            cursor="hand2"
        ).pack(side=tk.LEFT, padx=5)

        # Close button
        tk.Button(
            actions_frame,
            text="Close",
            command=popup.destroy,
            bg=self.color_scheme['primary'],
            fg="white",
            relief=tk.FLAT,
            padx=20,
            pady=8,
            cursor="hand2"
        ).pack(side=tk.LEFT, padx=5)

        popup.bind('<Escape>', lambda e: popup.destroy())

    def format_details(self, match_type: str, data: Dict) -> str:
        """Format details text for display"""
        lines = []

        if match_type == 'contact':
            if data.get('name'):
                lines.append(f"👤 Name: {data['name']}")
            if data.get('email'):
                lines.append(f"✉️  Email: {data['email']}")
            if data.get('role'):
                lines.append(f"💼 Role: {data['role']}")
            if data.get('last_contact'):
                lines.append(f"📅 Last Contact: {data['last_contact']}")
            if data.get('context'):
                lines.append(f"\n📝 Context:\n{data['context']}")

        elif match_type == 'abbreviation':
            if data.get('full'):
                lines.append(f"🔤 {data.get('abbr', '')} = {data['full']}")
            if data.get('definition'):
                lines.append(f"\n📖 Definition:\n{data['definition']}")
            if data.get('category'):
                lines.append(f"\n🏷️  Category: {data['category']}")

        elif match_type == 'project':
            if data.get('name'):
                lines.append(f"📁 Project: {data['name']}")
            if data.get('status'):
                lines.append(f"📊 Status: {data['status']}")
            if data.get('description'):
                lines.append(f"\n📝 Description:\n{data['description']}")

        else:
            for key, value in data.items():
                if key != 'id' and value:
                    lines.append(f"{key.replace('_', ' ').title()}: {value}")

        return '\n\n'.join(lines) if lines else "No details available"

    def show_item_context_menu(self, event, index: int):
        """Show context menu for item"""
        if not (0 <= index < len(self.matches)):
            return

        match = self.matches[index]

        menu = tk.Menu(self.root, tearoff=0)
        menu.add_command(label="View Details", command=lambda: self.show_details_popup(match))
        menu.add_command(label="⭐ Add to Favorites" if not self.is_favorite(match) else "Remove from Favorites",
                        command=lambda: self.toggle_favorite(match))
        menu.add_command(label="Copy as JSON", command=lambda: self.copy_as_json(match['data']))
        menu.add_separator()
        menu.add_command(label="Search Web", command=self.search_web)

        menu.post(event.x_root, event.y_root)

    def toggle_favorite(self, match: Dict):
        """Toggle favorite status"""
        if self.is_favorite(match):
            self.favorites = [f for f in self.favorites
                            if not (f.get('label') == match.get('label') and f.get('type') == match.get('type'))]
            self.show_toast("Removed from favorites")
        else:
            self.favorites.append(match)
            self.show_toast("Added to favorites ⭐")
        self.render_items_ring()

    def toggle_history(self):
        """Toggle history view"""
        self.show_history = not self.show_history
        if self.show_history:
            self.show_history_panel()
        else:
            self.render_items_ring()

    def show_history_panel(self):
        """Show recent history in a panel"""
        # Clear current items
        for widget in self.item_widgets:
            self.canvas.delete(widget)
        self.item_widgets.clear()

        if not self.history:
            msg = self.canvas.create_text(
                self.hub_size // 2,
                self.hub_size - 30,
                text="No history yet",
                font=self.item_font,
                fill=self.color_scheme['text_secondary']
            )
            self.item_widgets.append(msg)
            return

        # Show recent items
        y_pos = 30
        for i, item in enumerate(self.history[:5]):
            text = item.get('selected_text', '')[:30]
            label = self.canvas.create_text(
                20,
                y_pos,
                text=f"{i+1}. {text}...",
                font=self.item_font,
                fill=self.color_scheme['text_primary'],
                anchor=tk.W
            )
            self.item_widgets.append(label)
            y_pos += 20

    def show_info(self):
        """Show information about this prototype"""
        info_text = """
🎯 Action Wheel - Prototype 1

CONCEPT:
A radial menu that appears near your cursor, showing matches
in a circular layout with quick actions at cardinal points.

HOW TO USE:
• Wheel appears automatically when you copy text
• Click center hub to toggle history view
• Click items in the outer ring to select them
• Right-click items for context menu
• Use action buttons (Save, Search, Copy, Pin)

KEYBOARD SHORTCUTS:
• ↑↓←→ - Navigate through matches
• Enter/Space - Show full details
• S - Save snippet
• W - Web search
• C - Copy to clipboard
• P - Pin/unpin current item
• H - Toggle history view
• ESC - Close wheel

SPECIAL FEATURES:
• Favorites/pinning system with star indicators
• History tracking (last 10 analyses)
• Smooth fade animations
• Type-specific color coding
• Confidence scores on details
• Copy as JSON option
        """

        info_window = tk.Toplevel(self.root)
        info_window.title("About This Prototype")
        info_window.geometry("500x550")
        info_window.transient(self.root)
        info_window.attributes('-topmost', True)

        # Position near wheel
        wheel_x = self.root.winfo_x()
        wheel_y = self.root.winfo_y()
        info_window.geometry(f"+{wheel_x + self.hub_size + 10}+{wheel_y}")

        # Content
        text_widget = tk.Text(
            info_window,
            wrap=tk.WORD,
            font=self.item_font,
            padx=20,
            pady=20,
            bg='#f8f9fa',
            relief=tk.FLAT
        )
        text_widget.pack(fill=tk.BOTH, expand=True)
        text_widget.insert('1.0', info_text)
        text_widget.config(state=tk.DISABLED)

        # Close button
        tk.Button(
            info_window,
            text="Got it!",
            command=info_window.destroy,
            bg=self.color_scheme['primary'],
            fg='white',
            relief=tk.FLAT,
            padx=20,
            pady=10,
            cursor='hand2'
        ).pack(pady=15)

        info_window.bind('<Escape>', lambda e: info_window.destroy())

    def bind_keys(self):
        """Bind keyboard shortcuts"""
        self.root.bind('<Up>', lambda e: self.navigate(-1))
        self.root.bind('<Down>', lambda e: self.navigate(1))
        self.root.bind('<Left>', lambda e: self.navigate(-1))
        self.root.bind('<Right>', lambda e: self.navigate(1))
        self.root.bind('<Return>', lambda e: self.expand_details())
        self.root.bind('<space>', lambda e: self.expand_details())
        self.root.bind('<Escape>', lambda e: self.hide())
        self.root.bind('s', lambda e: self.save_snippet())
        self.root.bind('w', lambda e: self.search_web())
        self.root.bind('c', lambda e: self.copy_to_clipboard())
        self.root.bind('p', lambda e: self.pin_item())
        self.root.bind('h', lambda e: self.toggle_history())
        self.root.bind('<F1>', lambda e: self.show_info())

    def save_snippet(self):
        """Save current text as snippet"""
        if self.current_data and self.on_save_snippet:
            text = self.current_data.get('selected_text', '')
            if text:
                if hasattr(self.on_save_snippet, 'save'):
                    self.on_save_snippet.save(text, 'snippet')
                    self.show_toast("💾 Snippet saved!")
                else:
                    self.on_save_snippet(text)
                    self.show_toast("💾 Snippet saved!")

    def search_web(self):
        """Search selected text on web"""
        if self.current_data:
            query = self.current_data.get('selected_text', '')
            if query:
                url = f"https://www.google.com/search?q={query.replace(' ', '+')}"
                webbrowser.open(url)
                self.show_toast("🔍 Opened web search")

    def copy_to_clipboard(self):
        """Copy to clipboard"""
        if self.current_data:
            text = self.current_data.get('selected_text', '')
            if text:
                self.root.clipboard_clear()
                self.root.clipboard_append(text)
                self.show_toast("📋 Copied to clipboard!")

    def copy_as_json(self, data: Dict):
        """Copy data as JSON"""
        json_str = json.dumps(data, indent=2)
        self.root.clipboard_clear()
        self.root.clipboard_append(json_str)
        self.show_toast("📋 Copied as JSON!")

    def pin_item(self):
        """Pin selected item to favorites"""
        if self.matches and 0 <= self.selected_index < len(self.matches):
            match = self.matches[self.selected_index]
            self.toggle_favorite(match)

    def show_toast(self, message: str, duration: int = 2000):
        """Show enhanced toast message with modern styling"""
        toast_frame = tk.Frame(
            self.canvas,
            bg=self.color_scheme['project'],
            relief=tk.FLAT,
            bd=0
        )

        toast_label = tk.Label(
            toast_frame,
            text=message,
            font=self.item_font,
            bg=self.color_scheme['project'],
            fg="white",
            padx=15,
            pady=8
        )
        toast_label.pack()

        center = self.hub_size // 2
        toast_id = self.canvas.create_window(center, center + 60, window=toast_frame)

        # Fade out and remove
        def fade_out(alpha=1.0):
            if alpha > 0:
                alpha -= 0.1
                # Tkinter doesn't support per-widget alpha, so just wait and delete
                self.root.after(int(duration * alpha / 10), lambda: fade_out(alpha))
            else:
                self.canvas.delete(toast_id)

        self.root.after(duration, lambda: self.canvas.delete(toast_id))

    def hide(self):
        """Hide the action wheel with fade animation"""
        self.animate_fade_out()

    def animate_fade_out(self, alpha=0.95):
        """Smooth fade-out animation"""
        if alpha > 0:
            alpha -= 0.15
            self.root.attributes('-alpha', alpha)
            self.root.after(20, lambda: self.animate_fade_out(alpha))
        else:
            self.root.withdraw()
            self.root.attributes('-alpha', 0.95)  # Reset for next show

    def run(self):
        """Run the main loop"""
        self.root.mainloop()

    def update(self):
        """Update GUI (for integration with event loop)"""
        try:
            self.root.update()
        except tk.TclError:
            pass
