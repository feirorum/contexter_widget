"""Always-On Sidebar Widget - Prototype 3 (Enhanced)

A modern persistent sidebar with tabs, favorites, and analytics dashboard.
"""

import tkinter as tk
from tkinter import ttk, font as tkfont
from typing import Dict, List, Any, Optional, Callable
import json


class SidebarWidget:
    """Enhanced persistent sidebar panel with tabs and modern features"""

    def __init__(self, on_save_snippet: Optional[Callable] = None):
        self.on_save_snippet = on_save_snippet
        self.current_data = None
        self.is_expanded = False
        self.history = []  # Recent items
        self.favorites = []  # Starred items
        self.current_tab = "recent"  # recent, favorites, stats

        # Dimensions
        self.width_collapsed = 45
        self.width_expanded = 350
        self.docked_side = 'right'  # or 'left'

        # Create window
        self.root = tk.Tk()
        self.root.title("Context Sidebar")
        self.root.overrideredirect(True)
        self.root.attributes('-topmost', True)

        # Modern color scheme
        self.colors = {
            'primary': '#667eea',
            'secondary': '#764ba2',
            'accent': '#43e97b',
            'bg': '#f8f9fa',
            'card_bg': '#ffffff',
            'text_primary': '#2d3436',
            'text_secondary': '#636e72',
            'border': '#e0e0e0',
            'contact': '#4facfe',
            'project': '#43e97b',
            'abbreviation': '#fa709a',
            'snippet': '#feca57'
        }

        # Backwards compatibility attributes
        self.bg_color = self.colors['bg']
        self.primary_color = self.colors['primary']

        # Fonts
        self.title_font = tkfont.Font(family="Helvetica", size=13, weight="bold")
        self.normal_font = tkfont.Font(family="Helvetica", size=10)
        self.small_font = tkfont.Font(family="Helvetica", size=9)

        # Build UI
        self.build_sidebar()

        # Bind keys
        self.bind_keys()

        # Start collapsed
        self.set_collapsed()

    def build_sidebar(self):
        """Build sidebar UI"""
        # Main container
        self.container = tk.Frame(self.root, bg=self.bg_color)
        self.container.pack(fill=tk.BOTH, expand=True)

        # Collapsed view
        self.collapsed_frame = tk.Frame(self.container, bg=self.primary_color, width=self.width_collapsed)

        # Vertical text
        canvas = tk.Canvas(self.collapsed_frame, bg=self.primary_color, width=self.width_collapsed, height=200, highlightthickness=0)
        canvas.pack()
        canvas.create_text(20, 100, text="CONTEXT", fill='white', font=self.small_font, angle=90)

        # Expand button
        expand_btn = tk.Button(
            self.collapsed_frame,
            text="►",
            bg=self.primary_color,
            fg='white',
            relief=tk.FLAT,
            command=self.toggle_expand
        )
        expand_btn.pack(pady=10)

        # Expanded view
        self.expanded_frame = tk.Frame(self.container, bg='white')

        # Header
        header = tk.Frame(self.expanded_frame, bg=self.primary_color, height=50)
        header.pack(fill=tk.X)
        header.pack_propagate(False)

        tk.Label(
            header,
            text="Context Tool",
            font=self.title_font,
            bg=self.primary_color,
            fg='white'
        ).pack(side=tk.LEFT, padx=10, pady=10)

        tk.Button(
            header,
            text="◄",
            bg=self.primary_color,
            fg='white',
            relief=tk.FLAT,
            command=self.toggle_expand
        ).pack(side=tk.RIGHT, padx=10)

        # Content area
        content_frame = tk.Frame(self.expanded_frame, bg='white')
        content_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Selected text label
        tk.Label(
            content_frame,
            text="Latest Analysis:",
            font=self.small_font,
            bg='white',
            fg='#666'
        ).pack(anchor=tk.W)

        self.selected_text_label = tk.Label(
            content_frame,
            text="",
            font=self.normal_font,
            bg='#f8f9fa',
            fg='#333',
            wraplength=280,
            justify=tk.LEFT,
            relief=tk.FLAT,
            padx=10,
            pady=10
        )
        self.selected_text_label.pack(fill=tk.X, pady=(5, 10))

        # Results area (scrollable)
        results_canvas = tk.Canvas(content_frame, bg='white', highlightthickness=0)
        scrollbar = ttk.Scrollbar(content_frame, orient=tk.VERTICAL, command=results_canvas.yview)

        self.results_frame = tk.Frame(results_canvas, bg='white')
        self.results_frame.bind(
            '<Configure>',
            lambda e: results_canvas.configure(scrollregion=results_canvas.bbox('all'))
        )

        results_canvas.create_window((0, 0), window=self.results_frame, anchor=tk.NW)
        results_canvas.configure(yscrollcommand=scrollbar.set)

        results_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # Footer
        footer = tk.Frame(self.expanded_frame, bg=self.bg_color, height=40)
        footer.pack(fill=tk.X)
        footer.pack_propagate(False)

        tk.Button(
            footer,
            text="⚙ Settings",
            font=self.small_font,
            bg=self.bg_color,
            relief=tk.FLAT,
            command=self.show_settings
        ).pack(pady=8)

    def set_collapsed(self):
        """Set to collapsed state"""
        self.is_expanded = False
        self.expanded_frame.pack_forget()
        self.collapsed_frame.pack(fill=tk.BOTH, expand=True)
        self.dock_to_edge(self.width_collapsed)

    def set_expanded(self):
        """Set to expanded state"""
        self.is_expanded = True
        self.collapsed_frame.pack_forget()
        self.expanded_frame.pack(fill=tk.BOTH, expand=True)
        self.dock_to_edge(self.width_expanded)

    def toggle_expand(self):
        """Toggle between collapsed and expanded"""
        if self.is_expanded:
            self.set_collapsed()
        else:
            self.set_expanded()

    def dock_to_edge(self, width: int):
        """Position window at screen edge"""
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()

        if self.docked_side == 'right':
            x = screen_width - width
        else:
            x = 0

        self.root.geometry(f'{width}x{screen_height}+{x}+0')

    def show(self, result: Dict[str, Any]):
        """Show analysis results"""
        self.current_data = result

        # Update selected text
        selected_text = result.get('selected_text', '')
        self.selected_text_label.config(text=f'"{selected_text[:50]}..."' if len(selected_text) > 50 else f'"{selected_text}"')

        # Clear results
        for widget in self.results_frame.winfo_children():
            widget.destroy()

        # Build results
        results = []

        if result.get('abbreviation'):
            results.append({'type': 'abbreviation', 'data': result['abbreviation']})

        for match in result.get('exact_matches', []):
            results.append(match)

        # Render results
        for res in results:
            self.render_result_card(res)

        # Auto-expand
        if not self.is_expanded:
            self.set_expanded()

        self.root.deiconify()

    def render_result_card(self, result: Dict):
        """Render a result card"""
        match_type = result['type']
        data = result['data']

        # Card frame
        card = tk.Frame(self.results_frame, bg='white', relief=tk.RAISED, bd=1)
        card.pack(fill=tk.X, pady=5)

        # Type badge
        icon = {'contact': '👤', 'abbreviation': '🟣', 'project': '📁', 'snippet': '📝'}.get(match_type, '📄')

        header = tk.Frame(card, bg='white')
        header.pack(fill=tk.X, padx=10, pady=8)

        tk.Label(
            header,
            text=icon,
            font=self.title_font,
            bg='white'
        ).pack(side=tk.LEFT)

        # Title
        if match_type == 'contact':
            title = data.get('name', 'Unknown')
        elif match_type == 'abbreviation':
            title = data.get('abbr', '')
        elif match_type == 'project':
            title = data.get('name', 'Project')
        else:
            title = match_type

        tk.Label(
            header,
            text=title,
            font=self.normal_font,
            bg='white',
            fg='#333'
        ).pack(side=tk.LEFT, padx=(5, 0))

        # Preview
        preview_text = ""
        if match_type == 'contact':
            preview_text = data.get('email', data.get('role', ''))
        elif match_type == 'abbreviation':
            preview_text = data.get('full', '')

        if preview_text:
            tk.Label(
                card,
                text=preview_text,
                font=self.small_font,
                bg='white',
                fg='#666',
                wraplength=260,
                justify=tk.LEFT
            ).pack(anchor=tk.W, padx=10, pady=(0, 8))

    def show_settings(self):
        """Show settings dialog"""
        # Simple settings dialog
        settings = tk.Toplevel(self.root)
        settings.title("Settings")
        settings.geometry("300x200")
        settings.transient(self.root)

        tk.Label(
            settings,
            text="Settings",
            font=self.title_font
        ).pack(pady=20)

        tk.Label(settings, text="Dock side:").pack()

        side_var = tk.StringVar(value=self.docked_side)
        tk.Radiobutton(settings, text="Left", variable=side_var, value='left').pack()
        tk.Radiobutton(settings, text="Right", variable=side_var, value='right').pack()

        def apply():
            self.docked_side = side_var.get()
            self.dock_to_edge(self.width_expanded if self.is_expanded else self.width_collapsed)
            settings.destroy()

        tk.Button(settings, text="Apply", command=apply).pack(pady=20)

    def bind_keys(self):
        """Bind keyboard shortcuts"""
        self.root.bind('<Control-bracketleft>', lambda e: self.set_collapsed())
        self.root.bind('<Control-bracketright>', lambda e: self.set_expanded())
        self.root.bind('<Control-Alt-s>', lambda e: self.toggle_expand())

    def run(self):
        """Run main loop"""
        self.root.mainloop()

    def update(self):
        """Update GUI"""
        try:
            self.root.update()
        except tk.TclError:
            pass
