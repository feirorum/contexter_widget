"""Hotkey Overlay Widget - Prototype 2 (Enhanced)

A modern full-screen overlay with command palette design, featuring search,
filtering, and advanced result management.
"""

import tkinter as tk
from tkinter import ttk, font as tkfont
from typing import Dict, List, Any, Optional, Callable
import json
import webbrowser


class HotkeyOverlayWidget:
    """
    Enhanced command-palette style overlay with modern UI and powerful filtering
    """

    def __init__(self, on_save_snippet: Optional[Callable] = None):
        self.on_save_snippet = on_save_snippet
        self.current_data = None
        self.results = []
        self.filtered_results = []
        self.selected_index = 0
        self.active_filter = "all"  # all, contact, project, abbreviation, snippet
        self.sort_mode = "relevance"  # relevance, name, date
        self.dark_mode = False

        # Create main window (NOT fullscreen - that's too intrusive)
        self.root = tk.Tk()
        self.root.withdraw()
        self.root.title("Context Tool - Quick View")

        # Configure as a centered dialog, not fullscreen
        self.root.attributes('-topmost', True)
        self.root.configure(bg='#000000')

        # Modern color schemes
        self.light_colors = {
            'bg': '#f8f9fa',
            'card_bg': '#ffffff',
            'primary': '#667eea',
            'secondary': '#764ba2',
            'accent': '#f093fb',
            'text_primary': '#2d3436',
            'text_secondary': '#636e72',
            'border': '#e0e0e0',
            'hover': '#f1f3f5',
            'contact': '#4facfe',
            'project': '#43e97b',
            'abbreviation': '#fa709a',
            'snippet': '#feca57'
        }

        self.dark_colors = {
            'bg': '#1e1e2e',
            'card_bg': '#2b2b3c',
            'primary': '#89b4fa',
            'secondary': '#b4befe',
            'accent': '#f5c2e7',
            'text_primary': '#cdd6f4',
            'text_secondary': '#a6adc8',
            'border': '#45475a',
            'hover': '#313244',
            'contact': '#89dceb',
            'project': '#a6e3a1',
            'abbreviation': '#f5c2e7',
            'snippet': '#f9e2af'
        }

        self.colors = self.light_colors

        # Fonts
        self.title_font = tkfont.Font(family="Helvetica", size=18, weight="bold")
        self.normal_font = tkfont.Font(family="Helvetica", size=11)
        self.small_font = tkfont.Font(family="Helvetica", size=9)
        self.search_font = tkfont.Font(family="Helvetica", size=13)

        # Build UI
        self.build_overlay()

        # Bind keys
        self.bind_keys()

    def build_overlay(self):
        """Build the enhanced overlay UI"""
        # Main dialog (no backdrop - simpler design)
        self.dialog_width = 850
        self.dialog_height = 650

        self.dialog = tk.Frame(
            self.root,
            bg=self.colors['card_bg'],
            relief=tk.RAISED,
            bd=0,
            highlightthickness=2,
            highlightbackground=self.colors['primary']
        )
        self.dialog.pack(fill=tk.BOTH, expand=True)

        # Header with gradient
        header = tk.Frame(self.dialog, bg=self.colors['primary'], height=80)
        header.pack(fill=tk.X)
        header.pack_propagate(False)

        # Title and stats
        title_frame = tk.Frame(header, bg=self.colors['primary'])
        title_frame.pack(fill=tk.X, padx=25, pady=15)

        tk.Label(
            title_frame,
            text="🔍 Context Results",
            font=self.title_font,
            bg=self.colors['primary'],
            fg='white'
        ).pack(side=tk.LEFT)

        # Info button
        info_btn = tk.Button(
            title_frame,
            text="ℹ️",
            font=self.normal_font,
            bg=self.colors['secondary'],
            fg='white',
            relief=tk.FLAT,
            cursor='hand2',
            command=self.show_info,
            padx=8,
            pady=4
        )
        info_btn.pack(side=tk.LEFT, padx=10)

        # Stats and dark mode toggle
        controls_frame = tk.Frame(title_frame, bg=self.colors['primary'])
        controls_frame.pack(side=tk.RIGHT)

        self.stats_label = tk.Label(
            controls_frame,
            text="0 results",
            font=self.small_font,
            bg=self.colors['primary'],
            fg='white'
        )
        self.stats_label.pack(side=tk.LEFT, padx=10)

        # Dark mode toggle
        tk.Button(
            controls_frame,
            text="🌙" if not self.dark_mode else "☀️",
            font=self.normal_font,
            bg=self.colors['secondary'],
            fg='white',
            relief=tk.FLAT,
            cursor='hand2',
            command=self.toggle_dark_mode,
            padx=8,
            pady=4
        ).pack(side=tk.LEFT, padx=5)

        # Close button
        tk.Button(
            controls_frame,
            text="✕",
            font=self.title_font,
            bg=self.colors['primary'],
            fg='white',
            relief=tk.FLAT,
            cursor='hand2',
            command=self.hide,
            padx=10
        ).pack(side=tk.LEFT, padx=5)

        # Quick filter box (simpler than full search)
        search_frame = tk.Frame(self.dialog, bg=self.colors['card_bg'], height=60)
        search_frame.pack(fill=tk.X, padx=25, pady=(15, 0))
        search_frame.pack_propagate(False)

        tk.Label(
            search_frame,
            text="Quick Filter:",
            font=self.normal_font,
            bg=self.colors['card_bg'],
            fg=self.colors['text_secondary']
        ).pack(side=tk.LEFT, padx=(0, 10))

        search_container = tk.Frame(search_frame, bg=self.colors['border'], bd=1, relief=tk.SOLID)
        search_container.pack(fill=tk.BOTH, expand=True, side=tk.LEFT)

        search_inner = tk.Frame(search_container, bg=self.colors['card_bg'])
        search_inner.pack(fill=tk.BOTH, expand=True, padx=1, pady=1)

        tk.Label(
            search_inner,
            text="🔍",
            font=self.normal_font,
            bg=self.colors['card_bg'],
            fg=self.colors['text_secondary']
        ).pack(side=tk.LEFT, padx=(10, 5))

        self.search_var = tk.StringVar()
        self.search_var.trace('w', lambda *args: self.on_search_change())

        self.search_entry = tk.Entry(
            search_inner,
            textvariable=self.search_var,
            font=self.normal_font,
            relief=tk.FLAT,
            bg=self.colors['card_bg'],
            fg=self.colors['text_primary'],
            bd=0
        )
        self.search_entry.pack(fill=tk.BOTH, expand=True, side=tk.LEFT, ipady=6)

        # Filter chips
        filter_frame = tk.Frame(self.dialog, bg=self.colors['card_bg'], height=50)
        filter_frame.pack(fill=tk.X, padx=25, pady=(10, 0))
        filter_frame.pack_propagate(False)

        tk.Label(
            filter_frame,
            text="Filter:",
            font=self.small_font,
            bg=self.colors['card_bg'],
            fg=self.colors['text_secondary']
        ).pack(side=tk.LEFT, padx=(0, 10))

        self.filter_buttons = {}
        filters = [
            ("All", "all"),
            ("👤 Contacts", "contact"),
            ("📁 Projects", "project"),
            ("🟣 Abbreviations", "abbreviation"),
            ("📝 Snippets", "snippet")
        ]

        for label, filter_id in filters:
            btn = tk.Button(
                filter_frame,
                text=label,
                font=self.small_font,
                bg=self.colors['primary'] if filter_id == "all" else self.colors['bg'],
                fg='white' if filter_id == "all" else self.colors['text_primary'],
                relief=tk.FLAT,
                cursor='hand2',
                command=lambda f=filter_id: self.set_filter(f),
                padx=12,
                pady=6
            )
            btn.pack(side=tk.LEFT, padx=2)
            self.filter_buttons[filter_id] = btn

        # Sort options
        tk.Label(
            filter_frame,
            text="Sort:",
            font=self.small_font,
            bg=self.colors['card_bg'],
            fg=self.colors['text_secondary']
        ).pack(side=tk.LEFT, padx=(20, 10))

        self.sort_var = tk.StringVar(value="relevance")
        sort_menu = ttk.Combobox(
            filter_frame,
            textvariable=self.sort_var,
            values=["Relevance", "Name", "Date"],
            state="readonly",
            width=12,
            font=self.small_font
        )
        sort_menu.pack(side=tk.LEFT)
        sort_menu.bind('<<ComboboxSelected>>', lambda e: self.on_sort_change())

        # Results area
        results_frame = tk.Frame(self.dialog, bg=self.colors['card_bg'])
        results_frame.pack(fill=tk.BOTH, expand=True, padx=25, pady=15)

        # Scrollable canvas
        self.results_canvas = tk.Canvas(
            results_frame,
            bg=self.colors['card_bg'],
            highlightthickness=0
        )
        scrollbar = ttk.Scrollbar(
            results_frame,
            orient=tk.VERTICAL,
            command=self.results_canvas.yview
        )

        self.results_content = tk.Frame(self.results_canvas, bg=self.colors['card_bg'])
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
        footer = tk.Frame(self.dialog, bg=self.colors['bg'], height=45)
        footer.pack(fill=tk.X)
        footer.pack_propagate(False)

        hints = tk.Label(
            footer,
            text="💡 ↑↓ Navigate  •  ↵ Expand  •  Ctrl+S Save  •  Ctrl+E Export  •  ESC Close",
            font=self.small_font,
            bg=self.colors['bg'],
            fg=self.colors['text_secondary']
        )
        hints.pack(pady=12)

    def toggle_dark_mode(self):
        """Toggle between light and dark mode"""
        self.dark_mode = not self.dark_mode
        self.colors = self.dark_colors if self.dark_mode else self.light_colors
        # Rebuild UI with new colors
        self.rebuild_ui()

    def rebuild_ui(self):
        """Rebuild UI elements with current color scheme"""
        # For simplicity, just update the main visible components
        self.dialog.configure(bg=self.colors['card_bg'], highlightbackground=self.colors['primary'])
        self.results_canvas.configure(bg=self.colors['card_bg'])
        self.results_content.configure(bg=self.colors['card_bg'])
        self.render_results()

    def show(self, result: Dict[str, Any]):
        """Show overlay with analysis results"""
        self.current_data = result
        self.results = []
        self.selected_index = 0
        self.search_var.set("")

        # Build results list
        if result.get('abbreviation'):
            self.results.append({
                'type': 'abbreviation',
                'data': result['abbreviation'],
                'timestamp': result.get('timestamp', '')
            })

        for match in result.get('exact_matches', []):
            self.results.append({
                'type': match['type'],
                'data': match['data'],
                'timestamp': result.get('timestamp', '')
            })

        for item in result.get('related_items', []):
            self.results.append({
                'type': item['type'],
                'data': item['data'],
                'timestamp': result.get('timestamp', '')
            })

        self.filtered_results = self.results.copy()

        # Update stats
        self.update_stats()

        # Render results
        self.render_results()

        # Position window centered on screen
        self.root.update_idletasks()
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        x = (screen_width - self.dialog_width) // 2
        y = (screen_height - self.dialog_height) // 2
        self.root.geometry(f'{self.dialog_width}x{self.dialog_height}+{x}+{y}')

        # Show window
        self.root.deiconify()
        self.root.focus_force()

    def on_search_change(self):
        """Handle search input changes (fuzzy search)"""
        query = self.search_var.get().lower()

        if not query:
            self.filtered_results = self.results.copy()
        else:
            self.filtered_results = []
            for result in self.results:
                # Search across all fields
                data = result['data']
                searchable_text = json.dumps(data).lower()

                # Simple fuzzy matching - check if all query chars appear in order
                if self.fuzzy_match(query, searchable_text):
                    self.filtered_results.append(result)

        # Apply active filter
        if self.active_filter != "all":
            self.filtered_results = [r for r in self.filtered_results if r['type'] == self.active_filter]

        self.selected_index = 0
        self.update_stats()
        self.render_results()

    def fuzzy_match(self, query: str, text: str) -> bool:
        """Simple fuzzy matching - all query characters must appear in order"""
        query_idx = 0
        for char in text:
            if query_idx < len(query) and char == query[query_idx]:
                query_idx += 1
        return query_idx == len(query)

    def set_filter(self, filter_id: str):
        """Set active filter"""
        self.active_filter = filter_id

        # Update button styles
        for fid, btn in self.filter_buttons.items():
            if fid == filter_id:
                btn.config(bg=self.colors['primary'], fg='white')
            else:
                btn.config(bg=self.colors['bg'], fg=self.colors['text_primary'])

        # Re-filter results
        self.on_search_change()

    def on_sort_change(self):
        """Handle sort mode change"""
        sort_text = self.sort_var.get().lower()
        self.sort_mode = sort_text

        # Sort filtered results
        if sort_text == "name":
            self.filtered_results.sort(key=lambda x: self.get_result_title(x['type'], x['data']))
        elif sort_text == "date":
            self.filtered_results.sort(key=lambda x: x.get('timestamp', ''), reverse=True)
        # relevance is default order

        self.render_results()

    def update_stats(self):
        """Update results statistics"""
        count = len(self.filtered_results)
        self.stats_label.config(text=f"{count} result{'s' if count != 1 else ''}")

    def render_results(self):
        """Render results cards with modern design"""
        # Clear existing
        for widget in self.results_content.winfo_children():
            widget.destroy()

        if not self.filtered_results:
            # No results message
            no_results_frame = tk.Frame(self.results_content, bg=self.colors['card_bg'])
            no_results_frame.pack(pady=80)

            tk.Label(
                no_results_frame,
                text="🔍",
                font=tkfont.Font(size=48),
                bg=self.colors['card_bg'],
                fg=self.colors['text_secondary']
            ).pack()

            tk.Label(
                no_results_frame,
                text="No results found",
                font=self.title_font,
                fg=self.colors['text_secondary'],
                bg=self.colors['card_bg']
            ).pack(pady=10)

            tk.Label(
                no_results_frame,
                text="Try adjusting your search or filters",
                font=self.normal_font,
                fg=self.colors['text_secondary'],
                bg=self.colors['card_bg']
            ).pack()
            return

        # Selected text header
        if self.current_data:
            selected_text = self.current_data.get('selected_text', '')
            header_frame = tk.Frame(
                self.results_content,
                bg=self.colors['bg'],
                relief=tk.FLAT,
                bd=1,
                highlightthickness=1,
                highlightbackground=self.colors['border']
            )
            header_frame.pack(fill=tk.X, pady=(0, 15))

            tk.Label(
                header_frame,
                text=f'Selected: "{selected_text[:80]}{"..." if len(selected_text) > 80 else ""}"',
                font=self.normal_font,
                bg=self.colors['bg'],
                fg=self.colors['text_primary'],
                anchor=tk.W,
                padx=15,
                pady=12
            ).pack(fill=tk.X)

        # Render each result
        for i, result in enumerate(self.filtered_results):
            self.render_result_card(result, i)

    def render_result_card(self, result: Dict, index: int):
        """Render a modern result card"""
        is_selected = (index == self.selected_index)

        # Card frame with modern styling
        card = tk.Frame(
            self.results_content,
            bg=self.colors['primary'] + '20' if is_selected else self.colors['card_bg'],
            relief=tk.FLAT,
            bd=0,
            highlightthickness=2,
            highlightbackground=self.colors['primary'] if is_selected else self.colors['border']
        )
        card.pack(fill=tk.X, pady=6)

        # Card content
        card_inner = tk.Frame(card, bg=card['bg'])
        card_inner.pack(fill=tk.X, padx=15, pady=12)

        # Type and title
        match_type = result['type']
        data = result['data']

        # Icon and label
        icon = self.get_type_icon(match_type)
        title = self.get_result_title(match_type, data)
        type_color = self.colors.get(match_type, self.colors['text_primary'])

        # Header row
        header_frame = tk.Frame(card_inner, bg=card['bg'])
        header_frame.pack(fill=tk.X)

        # Icon
        tk.Label(
            header_frame,
            text=icon,
            font=tkfont.Font(size=16),
            bg=card['bg'],
            fg=type_color
        ).pack(side=tk.LEFT, padx=(0, 10))

        # Title
        tk.Label(
            header_frame,
            text=title,
            font=tkfont.Font(family="Helvetica", size=12, weight="bold"),
            bg=card['bg'],
            fg=self.colors['text_primary'],
            anchor=tk.W
        ).pack(side=tk.LEFT, fill=tk.X, expand=True)

        # Type badge
        badge = tk.Label(
            header_frame,
            text=match_type.upper(),
            font=tkfont.Font(family="Helvetica", size=8, weight="bold"),
            bg=type_color,
            fg='white',
            padx=8,
            pady=3
        )
        badge.pack(side=tk.RIGHT)

        # Preview content
        preview = self.get_result_preview(match_type, data)
        if preview:
            tk.Label(
                card_inner,
                text=preview,
                font=self.normal_font,
                bg=card['bg'],
                fg=self.colors['text_secondary'],
                anchor=tk.W,
                justify=tk.LEFT,
                wraplength=800
            ).pack(anchor=tk.W, pady=(8, 0))

        # Action buttons row
        actions_frame = tk.Frame(card_inner, bg=card['bg'])
        actions_frame.pack(fill=tk.X, pady=(10, 0))

        # Quick action buttons
        tk.Button(
            actions_frame,
            text="📋 Copy",
            font=self.small_font,
            bg=self.colors['bg'],
            fg=self.colors['text_primary'],
            relief=tk.FLAT,
            cursor='hand2',
            command=lambda: self.quick_copy(data),
            padx=10,
            pady=4
        ).pack(side=tk.LEFT, padx=(0, 5))

        tk.Button(
            actions_frame,
            text="🔍 Details",
            font=self.small_font,
            bg=self.colors['bg'],
            fg=self.colors['text_primary'],
            relief=tk.FLAT,
            cursor='hand2',
            command=lambda: self.show_detail_dialog(result),
            padx=10,
            pady=4
        ).pack(side=tk.LEFT, padx=5)

        # Bind click
        card.bind('<Button-1>', lambda e, idx=index: self.select_result(idx))
        for child in self.get_all_children(card):
            child.bind('<Button-1>', lambda e, idx=index: self.select_result(idx))

    def get_all_children(self, widget):
        """Recursively get all child widgets"""
        children = []
        for child in widget.winfo_children():
            children.append(child)
            children.extend(self.get_all_children(child))
        return children

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
            return data.get('name', 'Unknown Contact')
        elif match_type == 'abbreviation':
            return f"{data.get('abbr', '')} = {data.get('full', '')}"
        elif match_type == 'project':
            return data.get('name', 'Unknown Project')
        elif match_type == 'snippet':
            return data.get('title', 'Snippet')
        return match_type.title()

    def get_result_preview(self, match_type: str, data: Dict) -> str:
        """Get preview text for result"""
        if match_type == 'contact':
            parts = []
            if data.get('email'):
                parts.append(f"✉ {data['email']}")
            if data.get('role'):
                parts.append(f"👔 {data['role']}")
            if data.get('last_contact'):
                parts.append(f"📅 {data['last_contact']}")
            return ' • '.join(parts)

        elif match_type == 'abbreviation':
            return data.get('definition', '')[:150]

        elif match_type == 'project':
            parts = []
            if data.get('status'):
                parts.append(f"Status: {data['status']}")
            if data.get('description'):
                parts.append(data['description'][:100])
            return ' • '.join(parts)

        elif match_type == 'snippet':
            return data.get('text', '')[:150]

        return ''

    def select_result(self, index: int):
        """Select a result"""
        if 0 <= index < len(self.filtered_results):
            self.selected_index = index
            self.render_results()

    def navigate(self, direction: int):
        """Navigate results with arrow keys"""
        if not self.filtered_results:
            return

        self.selected_index = (self.selected_index + direction) % len(self.filtered_results)
        self.render_results()

        # Scroll to selected
        # TODO: Implement smooth scrolling to selected card

    def expand_selected(self):
        """Expand selected result to show full details"""
        if not self.filtered_results or self.selected_index >= len(self.filtered_results):
            return

        result = self.filtered_results[self.selected_index]
        self.show_detail_dialog(result)

    def show_detail_dialog(self, result: Dict):
        """Show detailed view dialog"""
        detail = tk.Toplevel(self.root)
        detail.title("Details")
        detail.geometry("550x450")
        detail.transient(self.root)
        detail.attributes('-topmost', True)

        # Center on screen
        detail.update_idletasks()
        x = (detail.winfo_screenwidth() // 2) - (550 // 2)
        y = (detail.winfo_screenheight() // 2) - (450 // 2)
        detail.geometry(f"+{x}+{y}")

        match_type = result['type']
        data = result['data']
        icon = self.get_type_icon(match_type)
        title = self.get_result_title(match_type, data)
        type_color = self.colors.get(match_type, self.colors['text_primary'])

        # Header
        header = tk.Frame(detail, bg=type_color, height=70)
        header.pack(fill=tk.X)
        header.pack_propagate(False)

        tk.Label(
            header,
            text=f"{icon} {title}",
            font=tkfont.Font(family="Helvetica", size=16, weight="bold"),
            bg=type_color,
            fg='white'
        ).pack(side=tk.LEFT, padx=25, pady=20)

        # Content with tabs
        content_frame = tk.Frame(detail, bg='white')
        content_frame.pack(fill=tk.BOTH, expand=True)

        # Tabs
        notebook = ttk.Notebook(content_frame)
        notebook.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)

        # Details tab
        details_tab = tk.Frame(notebook, bg='white')
        notebook.add(details_tab, text="Details")

        detail_text = tk.Text(
            details_tab,
            wrap=tk.WORD,
            font=self.normal_font,
            padx=20,
            pady=20,
            bg='#f8f9fa',
            relief=tk.FLAT
        )
        detail_text.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        details = self.format_details(match_type, data)
        detail_text.insert('1.0', details)
        detail_text.config(state=tk.DISABLED)

        # JSON tab
        json_tab = tk.Frame(notebook, bg='white')
        notebook.add(json_tab, text="JSON")

        json_text = tk.Text(
            json_tab,
            wrap=tk.WORD,
            font=tkfont.Font(family="Courier", size=10),
            padx=20,
            pady=20,
            bg='#f8f9fa',
            relief=tk.FLAT
        )
        json_text.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        json_str = json.dumps(data, indent=2)
        json_text.insert('1.0', json_str)
        json_text.config(state=tk.DISABLED)

        # Action buttons
        actions_frame = tk.Frame(detail, bg='white')
        actions_frame.pack(fill=tk.X, padx=20, pady=15)

        tk.Button(
            actions_frame,
            text="📋 Copy JSON",
            command=lambda: self.copy_json(data),
            bg=type_color,
            fg='white',
            relief=tk.FLAT,
            padx=15,
            pady=8,
            font=self.normal_font,
            cursor='hand2'
        ).pack(side=tk.LEFT, padx=5)

        tk.Button(
            actions_frame,
            text="Close",
            command=detail.destroy,
            bg=self.colors['bg'],
            fg=self.colors['text_primary'],
            relief=tk.FLAT,
            padx=20,
            pady=8,
            font=self.normal_font,
            cursor='hand2'
        ).pack(side=tk.RIGHT)

        detail.bind('<Escape>', lambda e: detail.destroy())

    def format_details(self, match_type: str, data: Dict) -> str:
        """Format detailed information"""
        lines = []

        if match_type == 'contact':
            for key in ['name', 'email', 'role', 'phone', 'company', 'last_contact', 'next_event', 'context']:
                if data.get(key):
                    lines.append(f"{key.replace('_', ' ').title()}: {data[key]}")

        elif match_type == 'abbreviation':
            for key in ['abbr', 'full', 'definition', 'category', 'context']:
                if data.get(key):
                    lines.append(f"{key.title()}: {data[key]}")

        elif match_type == 'project':
            for key in ['name', 'status', 'description', 'start_date', 'end_date']:
                if data.get(key):
                    lines.append(f"{key.replace('_', ' ').title()}: {data[key]}")

        else:
            for key, value in data.items():
                if key != 'id' and value:
                    lines.append(f"{key.replace('_', ' ').title()}: {value}")

        return '\n\n'.join(lines) if lines else "No details available"

    def quick_copy(self, data: Dict):
        """Quick copy to clipboard"""
        # Copy the most relevant field
        text = ""
        if 'name' in data:
            text = data['name']
        elif 'full' in data:
            text = data['full']
        elif 'text' in data:
            text = data['text']
        else:
            text = str(data)

        self.root.clipboard_clear()
        self.root.clipboard_append(text)
        self.show_toast("📋 Copied!")

    def copy_json(self, data: Dict):
        """Copy as JSON"""
        json_str = json.dumps(data, indent=2)
        self.root.clipboard_clear()
        self.root.clipboard_append(json_str)
        self.show_toast("📋 JSON copied!")

    def save_snippet(self):
        """Save snippet"""
        if self.current_data and self.on_save_snippet:
            text = self.current_data.get('selected_text', '')
            if text:
                if hasattr(self.on_save_snippet, 'save'):
                    self.on_save_snippet.save(text, 'snippet')
                else:
                    self.on_save_snippet(text)

                self.show_toast("💾 Snippet saved!")

    def export_results(self):
        """Export all results to JSON"""
        if not self.filtered_results:
            self.show_toast("⚠️ No results to export")
            return

        export_data = {
            'query': self.current_data.get('selected_text', ''),
            'results_count': len(self.filtered_results),
            'results': self.filtered_results
        }

        json_str = json.dumps(export_data, indent=2)
        self.root.clipboard_clear()
        self.root.clipboard_append(json_str)
        self.show_toast("📤 Results exported to clipboard!")

    def show_toast(self, message: str):
        """Show toast notification"""
        toast = tk.Toplevel(self.root)
        toast.overrideredirect(True)
        toast.attributes('-topmost', True)

        label = tk.Label(
            toast,
            text=message,
            font=self.normal_font,
            bg='#43e97b',
            fg='white',
            padx=25,
            pady=12
        )
        label.pack()

        # Position at top center
        toast.update_idletasks()
        x = (toast.winfo_screenwidth() - toast.winfo_width()) // 2
        y = 50
        toast.geometry(f"+{x}+{y}")

        # Auto-close
        toast.after(2000, toast.destroy)

    def show_info(self):
        """Show information about this prototype"""
        info_text = """
📊 Quick Results View - Prototype 2

CONCEPT:
A centered dialog showing all context matches with advanced
filtering and sorting capabilities.

HOW TO USE:
• Results appear automatically when you copy text
• Use Quick Filter to search within current results
• Click filter chips to show only specific types
• Sort by relevance, name, or date

KEYBOARD SHORTCUTS:
• ↑↓ - Navigate through results
• Enter - Show full details
• Ctrl+S - Save current text as snippet
• Ctrl+E - Export all results to clipboard (JSON)
• Ctrl+D - Toggle dark mode
• ESC - Close window

SPECIAL FEATURES:
• Dark mode support
• Fuzzy search filtering
• Type-specific badges and colors
• Quick copy buttons on each card
• Tabbed detail view (Details/JSON)
        """

        info_window = tk.Toplevel(self.root)
        info_window.title("About This Prototype")
        info_window.geometry("500x550")
        info_window.transient(self.root)
        info_window.attributes('-topmost', True)

        # Center on screen
        info_window.update_idletasks()
        x = (info_window.winfo_screenwidth() - 500) // 2
        y = (info_window.winfo_screenheight() - 550) // 2
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
        self.root.bind('<Escape>', lambda e: self.hide())
        self.root.bind('<Up>', lambda e: self.navigate(-1))
        self.root.bind('<Down>', lambda e: self.navigate(1))
        self.root.bind('<Return>', lambda e: self.expand_selected())
        self.root.bind('<Control-s>', lambda e: self.save_snippet())
        self.root.bind('<Control-k>', lambda e: self.search_entry.focus_set())
        self.root.bind('<Control-e>', lambda e: self.export_results())
        self.root.bind('<Control-d>', lambda e: self.toggle_dark_mode())
        self.root.bind('<F1>', lambda e: self.show_info())

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
