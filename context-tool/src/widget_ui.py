"""Desktop widget UI for Context Tool using tkinter"""

import tkinter as tk
from tkinter import ttk, font as tkfont
from typing import Dict, List, Any, Optional, Callable
import json
import webbrowser


class ContextWidget:
    """
    Desktop widget showing context analysis results

    Features:
    - Two-pane layout: compact list + detailed view
    - Keyboard navigation (Up/Down arrows, Enter)
    - Truncated text display for long content
    - Action buttons (Search Web, Save Snippet, Copy)
    """

    def __init__(self, on_save_snippet: Optional[Callable] = None, start_hidden: bool = True):
        """
        Initialize the context widget

        Args:
            on_save_snippet: Callback function to save snippet
        """
        self.on_save_snippet = on_save_snippet
        self.current_data = None
        self.matches = []
        self.selected_index = 0

        # Create the main window
        self.root = tk.Tk()
        self.root.title("Context Tool")
        self.root.geometry("800x600")

        # Set window to stay on top
        self.root.attributes('-topmost', True)

        # Configure styles
        self.setup_styles()

        # Build the UI
        self.build_ui()

        # Bind keyboard shortcuts
        self.bind_keys()

        # Hide window initially unless caller requests visible start
        self.start_hidden = start_hidden
        if self.start_hidden:
            self.root.withdraw()

    def setup_styles(self):
        """Configure fonts and colors"""
        self.bg_color = "#f5f5f5"
        self.fg_color = "#333333"
        self.accent_color = "#667eea"
        self.highlight_color = "#e8eaf6"
        self.border_color = "#ddd"

        # Fonts
        self.title_font = tkfont.Font(family="Helvetica", size=12, weight="bold")
        self.normal_font = tkfont.Font(family="Helvetica", size=10)
        self.small_font = tkfont.Font(family="Helvetica", size=9)
        self.mono_font = tkfont.Font(family="Courier", size=9)

    def build_ui(self):
        """Build the two-pane UI"""
        # Main container
        self.root.configure(bg=self.bg_color)

        # Header: Selected text display
        self.header_frame = tk.Frame(self.root, bg="white", relief=tk.RAISED, bd=1)
        self.header_frame.pack(fill=tk.X, padx=10, pady=(10, 5))

        tk.Label(
            self.header_frame,
            text="Selected Text:",
            font=self.small_font,
            fg="#666",
            bg="white"
        ).pack(anchor=tk.W, padx=10, pady=(5, 0))

        self.selected_text_label = tk.Label(
            self.header_frame,
            text="",
            font=self.title_font,
            fg=self.fg_color,
            bg="white",
            wraplength=760,
            justify=tk.LEFT
        )
        self.selected_text_label.pack(anchor=tk.W, padx=10, pady=(0, 10))

        # Main content area: Two-pane layout
        content_frame = tk.Frame(self.root, bg=self.bg_color)
        content_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        # Left pane: Compact list of matches
        left_pane = tk.Frame(content_frame, bg="white", relief=tk.SUNKEN, bd=1)
        left_pane.pack(side=tk.LEFT, fill=tk.BOTH, expand=False, padx=(0, 5))
        left_pane.config(width=300)

        tk.Label(
            left_pane,
            text="Matches",
            font=self.title_font,
            bg="white",
            fg=self.fg_color
        ).pack(anchor=tk.W, padx=10, pady=10)

        # Scrollable list frame
        list_scroll_frame = tk.Frame(left_pane, bg="white")
        list_scroll_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=(0, 5))

        self.list_canvas = tk.Canvas(list_scroll_frame, bg="white", highlightthickness=0)
        list_scrollbar = ttk.Scrollbar(list_scroll_frame, orient=tk.VERTICAL, command=self.list_canvas.yview)
        self.list_frame = tk.Frame(self.list_canvas, bg="white")

        self.list_frame.bind(
            "<Configure>",
            lambda e: self.list_canvas.configure(scrollregion=self.list_canvas.bbox("all"))
        )

        self.list_canvas.create_window((0, 0), window=self.list_frame, anchor=tk.NW)
        self.list_canvas.configure(yscrollcommand=list_scrollbar.set)

        self.list_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        list_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # Right pane: Detailed view
        right_pane = tk.Frame(content_frame, bg="white", relief=tk.SUNKEN, bd=1)
        right_pane.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

        tk.Label(
            right_pane,
            text="Details",
            font=self.title_font,
            bg="white",
            fg=self.fg_color
        ).pack(anchor=tk.W, padx=10, pady=10)

        # Scrollable detail frame
        detail_scroll_frame = tk.Frame(right_pane, bg="white")
        detail_scroll_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=(0, 5))

        self.detail_canvas = tk.Canvas(detail_scroll_frame, bg="white", highlightthickness=0)
        detail_scrollbar = ttk.Scrollbar(detail_scroll_frame, orient=tk.VERTICAL, command=self.detail_canvas.yview)
        self.detail_frame = tk.Frame(self.detail_canvas, bg="white")

        self.detail_frame.bind(
            "<Configure>",
            lambda e: self.detail_canvas.configure(scrollregion=self.detail_canvas.bbox("all"))
        )

        self.detail_canvas.create_window((0, 0), window=self.detail_frame, anchor=tk.NW)
        self.detail_canvas.configure(yscrollcommand=detail_scrollbar.set)

        self.detail_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        detail_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # Footer: Action buttons
        self.footer_frame = tk.Frame(self.root, bg=self.bg_color)
        self.footer_frame.pack(fill=tk.X, padx=10, pady=(5, 10))

        # Action buttons
        button_frame = tk.Frame(self.footer_frame, bg=self.bg_color)
        button_frame.pack(side=tk.LEFT)

        self.search_web_btn = tk.Button(
            button_frame,
            text="🔍 Search Web",
            font=self.normal_font,
            bg=self.accent_color,
            fg="white",
            relief=tk.FLAT,
            padx=15,
            pady=8,
            cursor="hand2",
            command=self.search_web
        )
        self.search_web_btn.pack(side=tk.LEFT, padx=(0, 5))

        self.save_snippet_btn = tk.Button(
            button_frame,
            text="💾 Save Snippet",
            font=self.normal_font,
            bg=self.accent_color,
            fg="white",
            relief=tk.FLAT,
            padx=15,
            pady=8,
            cursor="hand2",
            command=self.save_snippet
        )
        self.save_snippet_btn.pack(side=tk.LEFT, padx=5)

        self.copy_btn = tk.Button(
            button_frame,
            text="📋 Copy",
            font=self.normal_font,
            bg=self.accent_color,
            fg="white",
            relief=tk.FLAT,
            padx=15,
            pady=8,
            cursor="hand2",
            command=self.copy_to_clipboard
        )
        self.copy_btn.pack(side=tk.LEFT, padx=5)

        # Close button
        close_btn = tk.Button(
            button_frame,
            text="✕ Close",
            font=self.normal_font,
            bg="#e0e0e0",
            fg=self.fg_color,
            relief=tk.FLAT,
            padx=15,
            pady=8,
            cursor="hand2",
            command=self.hide
        )
        close_btn.pack(side=tk.LEFT, padx=5)

        # Keyboard hint
        hint_label = tk.Label(
            self.footer_frame,
            text="↑↓ Navigate  •  Enter Select  •  Esc Close",
            font=self.small_font,
            fg="#999",
            bg=self.bg_color
        )
        hint_label.pack(side=tk.RIGHT)

    def bind_keys(self):
        """Bind keyboard shortcuts"""
        self.root.bind('<Up>', lambda e: self.navigate(-1))
        self.root.bind('<Down>', lambda e: self.navigate(1))
        self.root.bind('<Return>', lambda e: self.select_current())
        self.root.bind('<Escape>', lambda e: self.hide())
        self.root.bind('<Control-w>', lambda e: self.search_web())
        self.root.bind('<Control-s>', lambda e: self.save_snippet())
        self.root.bind('<Control-c>', lambda e: self.copy_to_clipboard())

    def truncate_text(self, text: str, max_length: int = 40) -> str:
        """Truncate text with ellipsis"""
        if len(text) <= max_length:
            return text
        return text[:max_length-3] + "..."

    def show(self, result: Dict[str, Any]):
        """
        Show the widget with analysis results

        Args:
            result: Analysis result from ContextAnalyzer
        """
        self.current_data = result
        self.matches = []
        self.selected_index = 0

        # Build list of matches
        selected_text = result.get('selected_text', '')

        # Add abbreviation match first (highest priority)
        if result.get('abbreviation'):
            self.matches.append({
                'type': 'abbreviation',
                'title': f"{result['abbreviation']['abbr']} (Abbreviation)",
                'subtitle': result['abbreviation']['full'],
                'data': result['abbreviation']
            })

        # Add exact matches
        for match in result.get('exact_matches', []):
            match_type = match['type']
            data = match['data']

            if match_type == 'contact':
                title = f"👤 {data.get('name', 'Unknown')}"
                subtitle = data.get('email', data.get('role', ''))
            elif match_type == 'snippet':
                title = "📝 Snippet"
                subtitle = self.truncate_text(data.get('text', ''), 35)
            elif match_type == 'project':
                title = f"📁 {data.get('name', 'Unknown')}"
                subtitle = data.get('status', '')
            else:
                title = match_type.title()
                subtitle = ""

            self.matches.append({
                'type': match_type,
                'title': title,
                'subtitle': subtitle,
                'data': data
            })

        # Add related items
        for item in result.get('related_items', []):
            item_type = item['type']
            data = item['data']
            relationship = item.get('relationship', '')

            if item_type == 'contact':
                title = f"🔗 {data.get('name', 'Unknown')} ({relationship})"
                subtitle = data.get('role', '')
            elif item_type == 'project':
                title = f"🔗 {data.get('name', 'Unknown')} ({relationship})"
                subtitle = data.get('status', '')
            else:
                title = f"🔗 {item_type.title()} ({relationship})"
                subtitle = ""

            self.matches.append({
                'type': item_type,
                'title': title,
                'subtitle': subtitle,
                'data': data,
                'relationship': relationship
            })

        # If no matches, add a placeholder
        if not self.matches:
            self.matches.append({
                'type': 'none',
                'title': 'No matches found',
                'subtitle': 'Try selecting different text',
                'data': {}
            })

        # Update header
        self.selected_text_label.config(text=f'"{self.truncate_text(selected_text, 80)}"')

        # Render the list
        self.render_list()

        # Render details for first item
        self.render_details()

        # Show the window
        self.root.deiconify()
        self.root.focus_force()

    def render_list(self):
        """Render the compact list of matches"""
        # Clear existing items
        for widget in self.list_frame.winfo_children():
            widget.destroy()

        # Render each match
        for i, match in enumerate(self.matches):
            item_frame = tk.Frame(
                self.list_frame,
                bg=self.highlight_color if i == self.selected_index else "white",
                relief=tk.FLAT,
                bd=1,
                cursor="hand2"
            )
            item_frame.pack(fill=tk.X, padx=5, pady=2)

            # Bind click event
            item_frame.bind('<Button-1>', lambda e, idx=i: self.select_item(idx))

            # Title
            title_label = tk.Label(
                item_frame,
                text=match['title'],
                font=self.normal_font,
                fg=self.fg_color,
                bg=self.highlight_color if i == self.selected_index else "white",
                anchor=tk.W
            )
            title_label.pack(fill=tk.X, padx=10, pady=(8, 2))
            title_label.bind('<Button-1>', lambda e, idx=i: self.select_item(idx))

            # Subtitle (if exists)
            if match['subtitle']:
                subtitle_label = tk.Label(
                    item_frame,
                    text=match['subtitle'],
                    font=self.small_font,
                    fg="#666",
                    bg=self.highlight_color if i == self.selected_index else "white",
                    anchor=tk.W
                )
                subtitle_label.pack(fill=tk.X, padx=10, pady=(0, 8))
                subtitle_label.bind('<Button-1>', lambda e, idx=i: self.select_item(idx))

    def render_details(self):
        """Render detailed view for selected match"""
        # Clear existing details
        for widget in self.detail_frame.winfo_children():
            widget.destroy()

        if not self.matches or self.selected_index >= len(self.matches):
            return

        match = self.matches[self.selected_index]
        match_type = match['type']
        data = match['data']

        # Render based on type
        if match_type == 'abbreviation':
            self.render_abbreviation_details(data)
        elif match_type == 'contact':
            self.render_contact_details(data)
        elif match_type == 'snippet':
            self.render_snippet_details(data)
        elif match_type == 'project':
            self.render_project_details(data)
        elif match_type == 'none':
            self.render_no_match()
        else:
            self.render_generic_details(data)

    def render_abbreviation_details(self, abbr: Dict):
        """Render abbreviation details"""
        # Main definition
        def_frame = tk.Frame(self.detail_frame, bg="#f0f4ff", relief=tk.FLAT, bd=0)
        def_frame.pack(fill=tk.X, padx=10, pady=10)

        tk.Label(
            def_frame,
            text=f"{abbr['abbr']} = {abbr['full']}",
            font=self.title_font,
            fg=self.accent_color,
            bg="#f0f4ff"
        ).pack(anchor=tk.W, padx=15, pady=(15, 5))

        if abbr.get('definition'):
            tk.Label(
                def_frame,
                text=abbr['definition'],
                font=self.normal_font,
                fg=self.fg_color,
                bg="#f0f4ff",
                wraplength=450,
                justify=tk.LEFT
            ).pack(anchor=tk.W, padx=15, pady=(5, 15))

        # Category
        if abbr.get('category'):
            self.add_detail_field("Category", abbr['category'])

        # Examples
        examples = json.loads(abbr.get('examples', '[]')) if isinstance(abbr.get('examples'), str) else abbr.get('examples', [])
        if examples:
            self.add_detail_field("Examples", ", ".join(examples))

        # Related
        related = json.loads(abbr.get('related', '[]')) if isinstance(abbr.get('related'), str) else abbr.get('related', [])
        if related:
            self.add_detail_field("Related", ", ".join(related))

        # Links
        links = json.loads(abbr.get('links', '[]')) if isinstance(abbr.get('links'), str) else abbr.get('links', [])
        if links:
            links_frame = tk.Frame(self.detail_frame, bg="white")
            links_frame.pack(fill=tk.X, padx=10, pady=5)

            tk.Label(
                links_frame,
                text="Links:",
                font=self.normal_font,
                fg="#666",
                bg="white"
            ).pack(anchor=tk.W, padx=5, pady=(5, 2))

            for link in links:
                link_label = tk.Label(
                    links_frame,
                    text=link,
                    font=self.small_font,
                    fg=self.accent_color,
                    bg="white",
                    cursor="hand2"
                )
                link_label.pack(anchor=tk.W, padx=5, pady=2)
                link_label.bind('<Button-1>', lambda e, url=link: webbrowser.open(url))

    def render_contact_details(self, contact: Dict):
        """Render contact details"""
        if contact.get('name'):
            self.add_detail_field("Name", contact['name'], is_title=True)
        if contact.get('email'):
            self.add_detail_field("Email", contact['email'])
        if contact.get('role'):
            self.add_detail_field("Role", contact['role'])
        if contact.get('context'):
            self.add_detail_field("Context", contact['context'])
        if contact.get('last_contact'):
            self.add_detail_field("Last Contact", contact['last_contact'])
        if contact.get('next_event'):
            self.add_detail_field("Next Event", contact['next_event'])

        # Tags
        tags = json.loads(contact.get('tags', '[]')) if isinstance(contact.get('tags'), str) else contact.get('tags', [])
        if tags:
            self.add_detail_field("Tags", ", ".join(tags))

    def render_snippet_details(self, snippet: Dict):
        """Render snippet details"""
        if snippet.get('text'):
            self.add_detail_field("Text", snippet['text'], is_title=True, wraplength=450)
        if snippet.get('saved_date'):
            self.add_detail_field("Saved Date", snippet['saved_date'])
        if snippet.get('source'):
            self.add_detail_field("Source", snippet['source'])

        # Tags
        tags = json.loads(snippet.get('tags', '[]')) if isinstance(snippet.get('tags'), str) else snippet.get('tags', [])
        if tags:
            self.add_detail_field("Tags", ", ".join(tags))

    def render_project_details(self, project: Dict):
        """Render project details"""
        if project.get('name'):
            self.add_detail_field("Name", project['name'], is_title=True)
        if project.get('status'):
            self.add_detail_field("Status", project['status'])
        if project.get('description'):
            self.add_detail_field("Description", project['description'], wraplength=450)

        # Tags
        tags = json.loads(project.get('tags', '[]')) if isinstance(project.get('tags'), str) else project.get('tags', [])
        if tags:
            self.add_detail_field("Tags", ", ".join(tags))

        # Metadata (e.g., team_lead)
        metadata = json.loads(project.get('metadata', '{}')) if isinstance(project.get('metadata'), str) else project.get('metadata', {})
        if metadata.get('team_lead'):
            self.add_detail_field("Team Lead", metadata['team_lead'])

    def render_generic_details(self, data: Dict):
        """Render generic details for unknown types"""
        for key, value in data.items():
            if key != 'id' and value:
                self.add_detail_field(key.replace('_', ' ').title(), str(value))

    def render_no_match(self):
        """Render message when no matches found"""
        tk.Label(
            self.detail_frame,
            text="No matches found",
            font=self.title_font,
            fg="#999",
            bg="white"
        ).pack(padx=10, pady=20)

    def add_detail_field(self, label: str, value: str, is_title: bool = False, wraplength: int = 450):
        """Add a field to the detail view"""
        field_frame = tk.Frame(self.detail_frame, bg="white")
        field_frame.pack(fill=tk.X, padx=10, pady=5)

        if is_title:
            tk.Label(
                field_frame,
                text=value,
                font=self.title_font,
                fg=self.fg_color,
                bg="white",
                wraplength=wraplength,
                justify=tk.LEFT
            ).pack(anchor=tk.W, padx=5, pady=5)
        else:
            tk.Label(
                field_frame,
                text=f"{label}:",
                font=self.normal_font,
                fg="#666",
                bg="white"
            ).pack(anchor=tk.W, padx=5, pady=(5, 2))

            tk.Label(
                field_frame,
                text=value,
                font=self.normal_font,
                fg=self.fg_color,
                bg="white",
                wraplength=wraplength,
                justify=tk.LEFT
            ).pack(anchor=tk.W, padx=5, pady=(0, 5))

    def navigate(self, direction: int):
        """Navigate list with up/down keys"""
        if not self.matches:
            return

        self.selected_index = (self.selected_index + direction) % len(self.matches)
        self.render_list()
        self.render_details()

    def select_item(self, index: int):
        """Select an item from the list"""
        self.selected_index = index
        self.render_list()
        self.render_details()

    def select_current(self):
        """Handle Enter key - could expand or perform action"""
        # For now, just refresh details
        self.render_details()

    def search_web(self):
        """Search selected text on the web"""
        if self.current_data:
            query = self.current_data.get('selected_text', '')
            if query:
                url = f"https://www.google.com/search?q={query.replace(' ', '+')}"
                webbrowser.open(url)

    def save_snippet(self):
        """Save current text as snippet (with choice dialog)"""
        if self.current_data and self.on_save_snippet:
            text = self.current_data.get('selected_text', '')
            if text:
                # Check if on_save_snippet is the smart saver (has get_save_choices method)
                if hasattr(self.on_save_snippet, 'get_save_choices'):
                    # Get save choices
                    choices = self.on_save_snippet.get_save_choices(text)

                    # If only snippet choice (no special pattern), save directly without dialog
                    if len(choices) == 1 and choices[0]['type'] == 'snippet':
                        self._perform_save(text, 'snippet')
                    else:
                        # Multiple choices or special pattern detected - show dialog
                        self._show_save_choice_dialog(text)
                else:
                    # Simple callback
                    self.on_save_snippet(text)
                    self.show_message("Snippet saved!")

    def _show_save_choice_dialog(self, text: str):
        """
        Show dialog to choose save type

        Args:
            text: Text to save
        """
        # Get save choices from saver
        choices = self.on_save_snippet.get_save_choices(text)

        # Create dialog window
        dialog = tk.Toplevel(self.root)
        dialog.title("Save Options")
        dialog.geometry("500x400")
        dialog.transient(self.root)
        dialog.grab_set()

        # Center dialog
        dialog.update_idletasks()
        x = self.root.winfo_x() + (self.root.winfo_width() // 2) - (dialog.winfo_width() // 2)
        y = self.root.winfo_y() + (self.root.winfo_height() // 2) - (dialog.winfo_height() // 2)
        dialog.geometry(f"+{x}+{y}")

        # Header
        header_frame = tk.Frame(dialog, bg="white", relief=tk.RAISED, bd=1)
        header_frame.pack(fill=tk.X, padx=10, pady=10)

        tk.Label(
            header_frame,
            text="How do you want to save this?",
            font=self.title_font,
            bg="white",
            fg=self.fg_color
        ).pack(padx=15, pady=10)

        tk.Label(
            header_frame,
            text=f'"{self.truncate_text(text, 60)}"',
            font=self.normal_font,
            bg="white",
            fg="#666",
            wraplength=450
        ).pack(padx=15, pady=(0, 10))

        # Choices frame
        choices_frame = tk.Frame(dialog, bg="white")
        choices_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        selected_choice = tk.StringVar(value=choices[0]['type'])

        for i, choice in enumerate(choices):
            # Create choice card
            choice_frame = tk.Frame(choices_frame, bg="white", relief=tk.RAISED, bd=1)
            choice_frame.pack(fill=tk.X, pady=5)

            # Radio button
            rb = tk.Radiobutton(
                choice_frame,
                text=choice['label'],
                variable=selected_choice,
                value=choice['type'],
                font=self.normal_font,
                bg="white",
                fg=self.fg_color,
                activebackground="white",
                selectcolor=self.highlight_color,
                cursor="hand2"
            )
            rb.pack(anchor=tk.W, padx=10, pady=(10, 2))

            # Reason text
            reason_text = f"Confidence: {int(choice['confidence'] * 100)}% - {choice['reason']}"
            tk.Label(
                choice_frame,
                text=reason_text,
                font=self.small_font,
                bg="white",
                fg="#666",
                wraplength=450
            ).pack(anchor=tk.W, padx=30, pady=(0, 10))

        # Buttons frame
        button_frame = tk.Frame(dialog, bg="white")
        button_frame.pack(fill=tk.X, padx=10, pady=10)

        def on_save():
            choice_type = selected_choice.get()
            dialog.destroy()
            self._perform_save(text, choice_type)

        def on_cancel():
            dialog.destroy()

        # Save button
        save_btn = tk.Button(
            button_frame,
            text="💾 Save",
            font=self.normal_font,
            bg=self.accent_color,
            fg="white",
            relief=tk.FLAT,
            padx=20,
            pady=10,
            cursor="hand2",
            command=on_save
        )
        save_btn.pack(side=tk.LEFT, padx=5)

        # Cancel button
        cancel_btn = tk.Button(
            button_frame,
            text="✕ Cancel",
            font=self.normal_font,
            bg="#e0e0e0",
            fg=self.fg_color,
            relief=tk.FLAT,
            padx=20,
            pady=10,
            cursor="hand2",
            command=on_cancel
        )
        cancel_btn.pack(side=tk.LEFT, padx=5)

        # Bind Enter key
        dialog.bind('<Return>', lambda e: on_save())
        dialog.bind('<Escape>', lambda e: on_cancel())

    def _perform_save(self, text: str, save_type: str):
        """
        Perform the actual save operation

        Args:
            text: Text to save
            save_type: Type of entity to save as
        """
        if hasattr(self.on_save_snippet, 'save'):
            # Smart saver with type parameter
            result = self.on_save_snippet.save(text, save_type)
            if result:
                self.show_message(f"✓ Saved as {save_type}!")
        else:
            # Simple callback
            self.on_save_snippet(text)
            self.show_message("Snippet saved!")

    def copy_to_clipboard(self):
        """Copy selected text to clipboard"""
        if self.current_data:
            text = self.current_data.get('selected_text', '')
            if text:
                self.root.clipboard_clear()
                self.root.clipboard_append(text)
                self.show_message("Copied to clipboard!")

    def show_message(self, message: str):
        """Show a temporary message"""
        msg_label = tk.Label(
            self.footer_frame,
            text=message,
            font=self.normal_font,
            fg="green",
            bg=self.bg_color
        )
        msg_label.pack(side=tk.LEFT, padx=20)

        # Auto-hide after 2 seconds
        self.root.after(2000, msg_label.destroy)

    def hide(self):
        """Hide the widget"""
        self.root.withdraw()

    def run(self):
        """Start the tkinter main loop"""
        self.root.mainloop()

    def update(self):
        """Process pending GUI events (for integration with async code)"""
        try:
            self.root.update()
        except tk.TclError:
            pass
