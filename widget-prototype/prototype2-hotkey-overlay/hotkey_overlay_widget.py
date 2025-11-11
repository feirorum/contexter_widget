"""Hotkey Overlay Widget - Prototype 2

A full-screen overlay that appears when triggered by a global hotkey.
"""

import tkinter as tk
from tkinter import ttk, font as tkfont
from typing import Dict, List, Any, Optional, Callable
import json
import webbrowser


class HotkeyOverlayWidget:
    """
    Full-screen overlay with centered dialog for context analysis
    """

    def __init__(self, on_save_snippet: Optional[Callable] = None):
        self.on_save_snippet = on_save_snippet
        self.current_data = None
        self.results = []
        self.selected_index = 0

        # Create fullscreen window
        self.root = tk.Tk()
        self.root.withdraw()
        self.root.title("Context Tool")

        # Fullscreen overlay
        self.root.attributes('-fullscreen', True)
        self.root.attributes('-topmost', True)
        # Tkinter does not accept 8-digit hex with alpha on all platforms.
        # Use solid black background and rely on wm_attributes('-alpha') for transparency.
        self.root.configure(bg='#000000')  # Black (transparency via wm_attributes)

        # Fonts
        self.title_font = tkfont.Font(family="Helvetica", size=16, weight="bold")
        self.normal_font = tkfont.Font(family="Helvetica", size=11)
        self.small_font = tkfont.Font(family="Helvetica", size=9)

        # Colors
        self.primary_color = "#667eea"
        self.accent_color = "#764ba2"

        # Build UI
        self.build_overlay()

        # Bind keys
        self.bind_keys()

    def build_overlay(self):
        """Build the overlay UI"""
        # Backdrop (click to close)
        self.backdrop = tk.Frame(self.root, bg='#000000', cursor='arrow')
        self.backdrop.place(relx=0, rely=0, relwidth=1, relheight=1)
        self.backdrop.bind('<Button-1>', lambda e: self.hide())

        # Set backdrop opacity
        self.root.wm_attributes('-alpha', 0.6)

        # Dialog container (centered)
        self.dialog_width = 800
        self.dialog_height = 600

        self.dialog = tk.Frame(
            self.root,
            bg='white',
            relief=tk.RAISED,
            bd=0
        )
        self.dialog.place(
            relx=0.5,
            rely=0.5,
            anchor=tk.CENTER,
            width=self.dialog_width,
            height=self.dialog_height
        )

        # Round corners effect (simulate with styling)
        self.dialog.configure(highlightbackground='#e0e0e0', highlightthickness=1)

        # Header
        header = tk.Frame(self.dialog, bg=self.primary_color, height=60)
        header.pack(fill=tk.X)
        header.pack_propagate(False)

        title_label = tk.Label(
            header,
            text="🔍 Context Tool",
            font=self.title_font,
            bg=self.primary_color,
            fg='white'
        )
        title_label.pack(side=tk.LEFT, padx=20, pady=15)

        close_btn = tk.Button(
            header,
            text="✕",
            font=self.title_font,
            bg=self.primary_color,
            fg='white',
            relief=tk.FLAT,
            cursor='hand2',
            command=self.hide
        )
        close_btn.pack(side=tk.RIGHT, padx=20)

        # Search box
        search_frame = tk.Frame(self.dialog, bg='white', height=60)
        search_frame.pack(fill=tk.X, padx=20, pady=(10, 0))
        search_frame.pack_propagate(False)

        self.search_var = tk.StringVar()
        self.search_entry = tk.Entry(
            search_frame,
            textvariable=self.search_var,
            font=self.normal_font,
            relief=tk.SOLID,
            bd=1
        )
        self.search_entry.pack(fill=tk.X, side=tk.LEFT, expand=True, ipady=8)

        search_hint = tk.Label(
            search_frame,
            text="Ctrl+K",
            font=self.small_font,
            bg='white',
            fg='#999'
        )
        search_hint.pack(side=tk.RIGHT, padx=(10, 0))

        # Results area
        results_frame = tk.Frame(self.dialog, bg='white')
        results_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)

        # Scrollable canvas
        self.results_canvas = tk.Canvas(
            results_frame,
            bg='white',
            highlightthickness=0
        )
        scrollbar = ttk.Scrollbar(
            results_frame,
            orient=tk.VERTICAL,
            command=self.results_canvas.yview
        )

        self.results_content = tk.Frame(self.results_canvas, bg='white')
        self.results_content.bind(
            '<Configure>',
            lambda e: self.results_canvas.configure(
                scrollregion=self.results_canvas.bbox('all')
            )
        )

        self.results_canvas.create_window((0, 0), window=self.results_content, anchor=tk.NW)
        self.results_canvas.configure(yscrollcommand=scrollbar.set)

        self.results_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # Footer with shortcuts
        footer = tk.Frame(self.dialog, bg='#f5f5f5', height=40)
        footer.pack(fill=tk.X)
        footer.pack_propagate(False)

        hints = tk.Label(
            footer,
            text="💡 Press ↑↓ to navigate  •  ↵ to expand  •  Ctrl+S to save  •  ESC to close",
            font=self.small_font,
            bg='#f5f5f5',
            fg='#666'
        )
        hints.pack(pady=10)

    def show(self, result: Dict[str, Any]):
        """Show overlay with analysis results"""
        self.current_data = result
        self.results = []
        self.selected_index = 0

        # Build results list
        if result.get('abbreviation'):
            self.results.append({
                'type': 'abbreviation',
                'data': result['abbreviation']
            })

        for match in result.get('exact_matches', []):
            self.results.append(match)

        for item in result.get('related_items', []):
            self.results.append(item)

        # Render results
        self.render_results()

        # Show window
        self.root.deiconify()
        self.root.focus_force()
        self.search_entry.focus_set()

    def render_results(self):
        """Render results cards"""
        # Clear existing
        for widget in self.results_content.winfo_children():
            widget.destroy()

        if not self.results:
            # No results message
            no_results = tk.Label(
                self.results_content,
                text="No matches found",
                font=self.title_font,
                fg='#999',
                bg='white'
            )
            no_results.pack(pady=50)
            return

        # Selected text header
        if self.current_data:
            selected_text = self.current_data.get('selected_text', '')
            header = tk.Frame(self.results_content, bg='#f8f9fa', relief=tk.FLAT)
            header.pack(fill=tk.X, pady=(0, 10))

            tk.Label(
                header,
                text=f'"{selected_text}"',
                font=self.normal_font,
                bg='#f8f9fa',
                fg='#333'
            ).pack(padx=15, pady=10)

        # Render each result
        for i, result in enumerate(self.results):
            self.render_result_card(result, i)

    def render_result_card(self, result: Dict, index: int):
        """Render a single result card"""
        is_selected = (index == self.selected_index)

        # Card frame
        card = tk.Frame(
            self.results_content,
            bg='#e8eaf6' if is_selected else 'white',
            relief=tk.RAISED,
            bd=1
        )
        card.pack(fill=tk.X, pady=5)

        # Type and title
        match_type = result['type']
        data = result['data']

        # Icon and label
        icon = self.get_type_icon(match_type)
        title = self.get_result_title(match_type, data)

        header_frame = tk.Frame(card, bg='#e8eaf6' if is_selected else 'white')
        header_frame.pack(fill=tk.X, padx=15, pady=10)

        tk.Label(
            header_frame,
            text=f"{icon} {title}",
            font=self.normal_font,
            bg='#e8eaf6' if is_selected else 'white',
            fg='#333',
            anchor=tk.W
        ).pack(side=tk.LEFT)

        # Type badge
        badge = tk.Label(
            header_frame,
            text=match_type.upper(),
            font=self.small_font,
            bg=self.primary_color,
            fg='white',
            padx=6,
            pady=2
        )
        badge.pack(side=tk.RIGHT)

        # Preview content
        preview = self.get_result_preview(match_type, data)
        if preview:
            tk.Label(
                card,
                text=preview,
                font=self.small_font,
                bg='#e8eaf6' if is_selected else 'white',
                fg='#666',
                anchor=tk.W,
                justify=tk.LEFT,
                wraplength=700
            ).pack(anchor=tk.W, padx=15, pady=(0, 10))

        # Bind click
        card.bind('<Button-1>', lambda e, idx=index: self.select_result(idx))
        for child in card.winfo_children():
            child.bind('<Button-1>', lambda e, idx=index: self.select_result(idx))

    def get_type_icon(self, match_type: str) -> str:
        """Get icon for match type"""
        icons = {
            'contact': '👤',
            'abbreviation': '🟣',
            'project': '📁',
            'snippet': '📝'
        }
        return icons.get(match_type, '📄')

    def get_result_title(self, match_type: str, data: Dict) -> str:
        """Get title for result"""
        if match_type == 'contact':
            return data.get('name', 'Unknown')
        elif match_type == 'abbreviation':
            return f"{data.get('abbr', '')} = {data.get('full', '')}"
        elif match_type == 'project':
            return data.get('name', 'Unknown Project')
        elif match_type == 'snippet':
            return 'Snippet'
        return match_type.title()

    def get_result_preview(self, match_type: str, data: Dict) -> str:
        """Get preview text for result"""
        if match_type == 'contact':
            parts = []
            if data.get('email'):
                parts.append(f"✉ {data['email']}")
            if data.get('role'):
                parts.append(f"👔 {data['role']}")
            return ' • '.join(parts)

        elif match_type == 'abbreviation':
            return data.get('definition', '')[:100]

        elif match_type == 'project':
            return data.get('description', '')[:100]

        elif match_type == 'snippet':
            return data.get('text', '')[:100]

        return ''

    def select_result(self, index: int):
        """Select a result"""
        if 0 <= index < len(self.results):
            self.selected_index = index
            self.render_results()

    def navigate(self, direction: int):
        """Navigate results with arrow keys"""
        if not self.results:
            return

        self.selected_index = (self.selected_index + direction) % len(self.results)
        self.render_results()

    def expand_selected(self):
        """Expand selected result to show full details"""
        if not self.results or self.selected_index >= len(self.results):
            return

        result = self.results[self.selected_index]
        self.show_detail_dialog(result)

    def show_detail_dialog(self, result: Dict):
        """Show detailed view dialog"""
        # Create detail window
        detail = tk.Toplevel(self.root)
        detail.title("Details")
        detail.geometry("500x400")
        detail.transient(self.root)
        detail.attributes('-topmost', True)

        # Center on screen
        detail.update_idletasks()
        x = (detail.winfo_screenwidth() // 2) - (500 // 2)
        y = (detail.winfo_screenheight() // 2) - (400 // 2)
        detail.geometry(f"+{x}+{y}")

        # Header
        header = tk.Frame(detail, bg=self.primary_color, height=60)
        header.pack(fill=tk.X)
        header.pack_propagate(False)

        match_type = result['type']
        data = result['data']
        icon = self.get_type_icon(match_type)
        title = self.get_result_title(match_type, data)

        tk.Label(
            header,
            text=f"{icon} {title}",
            font=self.title_font,
            bg=self.primary_color,
            fg='white'
        ).pack(side=tk.LEFT, padx=20, pady=15)

        # Content
        content = tk.Text(
            detail,
            wrap=tk.WORD,
            font=self.normal_font,
            padx=20,
            pady=20
        )
        content.pack(fill=tk.BOTH, expand=True)

        # Format details
        details = self.format_details(match_type, data)
        content.insert('1.0', details)
        content.config(state=tk.DISABLED)

        # Close button
        close_frame = tk.Frame(detail, bg='white')
        close_frame.pack(fill=tk.X, padx=20, pady=10)

        tk.Button(
            close_frame,
            text="Close",
            command=detail.destroy,
            bg=self.primary_color,
            fg='white',
            relief=tk.FLAT,
            padx=20,
            pady=8
        ).pack()

        detail.bind('<Escape>', lambda e: detail.destroy())

    def format_details(self, match_type: str, data: Dict) -> str:
        """Format detailed information"""
        lines = []

        if match_type == 'contact':
            for key in ['name', 'email', 'role', 'last_contact', 'next_event', 'context']:
                if data.get(key):
                    lines.append(f"{key.replace('_', ' ').title()}: {data[key]}")

        elif match_type == 'abbreviation':
            for key in ['abbr', 'full', 'definition', 'category']:
                if data.get(key):
                    lines.append(f"{key.title()}: {data[key]}")

        elif match_type == 'project':
            for key in ['name', 'status', 'description']:
                if data.get(key):
                    lines.append(f"{key.title()}: {data[key]}")

        else:
            for key, value in data.items():
                if key != 'id' and value:
                    lines.append(f"{key.replace('_', ' ').title()}: {value}")

        return '\n\n'.join(lines) if lines else "No details available"

    def save_snippet(self):
        """Save snippet"""
        if self.current_data and self.on_save_snippet:
            text = self.current_data.get('selected_text', '')
            if text:
                if hasattr(self.on_save_snippet, 'save'):
                    self.on_save_snippet.save(text, 'snippet')
                else:
                    self.on_save_snippet(text)

                # Show confirmation
                self.show_toast("Snippet saved!")

    def show_toast(self, message: str):
        """Show toast notification"""
        toast = tk.Toplevel(self.root)
        toast.overrideredirect(True)
        toast.attributes('-topmost', True)

        label = tk.Label(
            toast,
            text=message,
            font=self.normal_font,
            bg='#4CAF50',
            fg='white',
            padx=20,
            pady=10
        )
        label.pack()

        # Position at bottom right
        toast.update_idletasks()
        x = toast.winfo_screenwidth() - toast.winfo_width() - 20
        y = toast.winfo_screenheight() - toast.winfo_height() - 20
        toast.geometry(f"+{x}+{y}")

        # Auto-close
        toast.after(2000, toast.destroy)

    def bind_keys(self):
        """Bind keyboard shortcuts"""
        self.root.bind('<Escape>', lambda e: self.hide())
        self.root.bind('<Up>', lambda e: self.navigate(-1))
        self.root.bind('<Down>', lambda e: self.navigate(1))
        self.root.bind('<Return>', lambda e: self.expand_selected())
        self.root.bind('<Control-s>', lambda e: self.save_snippet())
        self.root.bind('<Control-k>', lambda e: self.search_entry.focus_set())

    def hide(self):
        """Hide the overlay"""
        self.root.withdraw()

    def run(self):
        """Run the main loop"""
        self.root.mainloop()

    def update(self):
        """Update GUI"""
        try:
            self.root.update()
        except tk.TclError:
            pass
