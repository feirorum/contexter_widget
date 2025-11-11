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

        # Dimensions - modernized for better visibility
        self.width_collapsed = 50
        self.width_expanded = 420
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

        # Modern fonts - Segoe UI for cross-platform modern look
        self.title_font = tkfont.Font(family="Segoe UI", size=16, weight="bold")
        self.normal_font = tkfont.Font(family="Segoe UI", size=11)
        self.small_font = tkfont.Font(family="Segoe UI", size=10)

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

        # Collapsed view - Modern minimal design
        self.collapsed_frame = tk.Frame(self.container, bg=self.primary_color, width=self.width_collapsed)

        # Vertical text - Modern font
        canvas = tk.Canvas(self.collapsed_frame, bg=self.primary_color, width=self.width_collapsed, height=200, highlightthickness=0)
        canvas.pack(pady=20)
        canvas.create_text(25, 100, text="CONTEXT", fill='white', font=self.small_font, angle=90)

        # Expand button - Modern styling
        expand_btn = tk.Button(
            self.collapsed_frame,
            text="►",
            bg=self.primary_color,
            fg='white',
            relief=tk.FLAT,
            command=self.toggle_expand,
            cursor='hand2',
            font=self.normal_font,
            padx=8,
            pady=6
        )
        expand_btn.pack(pady=10)

        # Expanded view
        self.expanded_frame = tk.Frame(self.container, bg='white')

        # Header - Modern Material Design style
        header = tk.Frame(self.expanded_frame, bg=self.primary_color, height=64)
        header.pack(fill=tk.X)
        header.pack_propagate(False)

        tk.Label(
            header,
            text="Context Tool",
            font=self.title_font,
            bg=self.primary_color,
            fg='white'
        ).pack(side=tk.LEFT, padx=18, pady=16)

        # Info button - Modern styling
        info_btn = tk.Button(
            header,
            text="ℹ️",
            bg=self.primary_color,
            fg='white',
            relief=tk.FLAT,
            command=self.show_info,
            cursor='hand2',
            font=self.normal_font,
            padx=8,
            pady=4
        )
        info_btn.pack(side=tk.LEFT, padx=4)

        # Collapse button - Modern styling
        collapse_btn = tk.Button(
            header,
            text="◄",
            bg=self.primary_color,
            fg='white',
            relief=tk.FLAT,
            command=self.toggle_expand,
            cursor='hand2',
            font=self.normal_font,
            padx=12,
            pady=4
        )
        collapse_btn.pack(side=tk.RIGHT, padx=12)

        # Content area - Modern spacing
        content_frame = tk.Frame(self.expanded_frame, bg='white')
        content_frame.pack(fill=tk.BOTH, expand=True, padx=16, pady=16)

        # Selected text label - Modern Material Design card
        tk.Label(
            content_frame,
            text="Latest Analysis:",
            font=self.small_font,
            bg='white',
            fg='#666'
        ).pack(anchor=tk.W, pady=(0, 6))

        # Card container with shadow simulation
        selected_card_outer = tk.Frame(content_frame, bg='#e8e8e8')
        selected_card_outer.pack(fill=tk.X, pady=(0, 14))

        self.selected_text_label = tk.Label(
            selected_card_outer,
            text="",
            font=self.normal_font,
            bg='#f8f9fa',
            fg='#333',
            wraplength=360,
            justify=tk.LEFT,
            relief=tk.FLAT,
            padx=14,
            pady=12
        )
        self.selected_text_label.pack(fill=tk.X, padx=1, pady=1)

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
        """Render a result card - Modern Material Design style"""
        match_type = result['type']
        data = result['data']

        # Outer container for shadow simulation
        card_outer = tk.Frame(self.results_frame, bg='#e8e8e8')
        card_outer.pack(fill=tk.X, pady=8)

        # Inner card with modern styling
        card = tk.Frame(card_outer, bg='white', relief=tk.FLAT)
        card.pack(fill=tk.BOTH, expand=True, padx=1, pady=1)

        # Type badge and title
        icon = {'contact': '👤', 'abbreviation': '🟣', 'project': '📁', 'snippet': '📝'}.get(match_type, '📄')

        header = tk.Frame(card, bg='white')
        header.pack(fill=tk.X, padx=14, pady=12)

        # Icon with larger size
        tk.Label(
            header,
            text=icon,
            font=tkfont.Font(family="Segoe UI", size=14),
            bg='white'
        ).pack(side=tk.LEFT)

        # Title - determine text
        if match_type == 'contact':
            title = data.get('name', 'Unknown')
        elif match_type == 'abbreviation':
            title = data.get('abbr', '')
        elif match_type == 'project':
            title = data.get('name', 'Project')
        else:
            title = match_type

        # Title label with bold font
        tk.Label(
            header,
            text=title,
            font=tkfont.Font(family="Segoe UI", size=12, weight="bold"),
            bg='white',
            fg='#2d3436'
        ).pack(side=tk.LEFT, padx=(8, 0))

        # Preview text
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
                fg='#636e72',
                wraplength=360,
                justify=tk.LEFT
            ).pack(anchor=tk.W, padx=14, pady=(0, 12))

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

    def show_info(self):
        """Show information about this prototype"""
        info_text = """
📌 Always-On Sidebar - Prototype 3

CONCEPT:
A persistent sidebar docked to the screen edge, always available
for quick reference to your context matches.

HOW TO USE:
• Sidebar stays open and docked to right (or left) edge
• Click ► button when collapsed to expand
• Click ◄ button to collapse back to minimal view
• Results appear automatically when you copy text
• Drag to resize (future enhancement)

KEYBOARD SHORTCUTS:
• Ctrl+[ - Collapse sidebar
• Ctrl+] - Expand sidebar
• Ctrl+Alt+S - Toggle expand/collapse
• F1 - Show this help

SPECIAL FEATURES:
• Persistent, always-visible design
• Switchable dock side (left/right)
• Minimal resource footprint when collapsed
• Type-specific color coding
• Settings panel for customization

BEST FOR:
• Users who want context always visible
• Multi-monitor setups
• Long work sessions with frequent lookups
        """

        info_window = tk.Toplevel(self.root)
        info_window.title("About This Prototype")
        info_window.geometry("500x550")
        info_window.transient(self.root)
        info_window.attributes('-topmost', True)

        # Position to the left of sidebar
        sidebar_x = self.root.winfo_x()
        sidebar_y = self.root.winfo_y()
        x = max(sidebar_x - 510, 20)  # 500 width + 10 padding
        y = sidebar_y + 50
        info_window.geometry(f"+{x}+{y}")

        # Content
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

        # Close button
        tk.Button(
            info_window,
            text="Got it!",
            command=info_window.destroy,
            bg=self.colors['primary'],
            fg='white',
            relief=tk.FLAT,
            padx=20,
            pady=10,
            font=self.normal_font,
            cursor='hand2'
        ).pack(pady=15)

        info_window.bind('<Escape>', lambda e: info_window.destroy())

    def bind_keys(self):
        """Bind keyboard shortcuts"""
        self.root.bind('<Control-bracketleft>', lambda e: self.set_collapsed())
        self.root.bind('<Control-bracketright>', lambda e: self.set_expanded())
        self.root.bind('<Control-Alt-s>', lambda e: self.toggle_expand())
        self.root.bind('<F1>', lambda e: self.show_info())

    def run(self):
        """Run main loop"""
        self.root.mainloop()

    def update(self):
        """Update GUI"""
        try:
            self.root.update()
        except tk.TclError:
            pass
