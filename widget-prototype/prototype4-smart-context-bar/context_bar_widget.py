"""Smart Context Bar Widget - Prototype 4 (Enhanced)

A modern compact bar with smooth animations, progress indicators, and rich actions.
"""

import tkinter as tk
from tkinter import font as tkfont
from typing import Dict, List, Any, Optional, Callable
import webbrowser
import signal
import sys


class ContextBarWidget:
    """Inline context bar appearing near selection"""

    def __init__(self, on_save_snippet: Optional[Callable] = None):
        self.on_save_snippet = on_save_snippet
        self.current_data = None
        self.matches = []
        self.current_index = 0
        self.is_expanded = False
        self.hide_timer_id = None  # Track timer for resetting

        # Create compact bar window
        self.bar_window = tk.Toplevel()
        self.bar_window.withdraw()
        self.bar_window.overrideredirect(True)
        self.bar_window.attributes('-topmost', True)

        # Compatibility: alias for widget_mode.py
        self.root = self.bar_window

        # Modern styling
        self.colors = {
            'bg': '#ffffff',
            'primary': '#667eea',
            'secondary': '#764ba2',
            'accent': '#43e97b',
            'text_primary': '#2d3436',
            'text_secondary': '#636e72',
            'border': '#e0e0e0',
            'contact': '#4facfe',
            'project': '#43e97b',
            'abbreviation': '#fa709a',
            'snippet': '#feca57'
        }
        self.bg_color = self.colors['bg']
        self.primary_color = self.colors['primary']
        self.bar_width = 420
        self.bar_height = 54
        self.auto_hide_duration = 8000  # 8 seconds
        self.hide_timer = None

        # Modern fonts - Segoe UI for cross-platform modern look
        self.normal_font = tkfont.Font(family="Segoe UI", size=11)
        self.small_font = tkfont.Font(family="Segoe UI", size=10)

        # Build bar
        self.build_bar()

        # Expanded popup (created on demand)
        self.popup_window = None

        # Bind keys
        self.bind_keys()

        # Setup signal handlers for clean Ctrl-C exit
        self.setup_signal_handlers()

    def build_bar(self):
        """Build compact context bar - Modern Material Design style"""
        # Outer shadow frame
        shadow_frame = tk.Frame(
            self.bar_window,
            bg='#d0d0d0'
        )
        shadow_frame.pack(fill=tk.BOTH, expand=True)

        # Main bar frame with modern flat design
        self.bar_frame = tk.Frame(
            shadow_frame,
            bg=self.bg_color,
            relief=tk.FLAT
        )
        self.bar_frame.pack(fill=tk.BOTH, expand=True, padx=2, pady=2)

        # Content frame with better spacing
        content = tk.Frame(self.bar_frame, bg=self.bg_color)
        content.pack(fill=tk.BOTH, expand=True, padx=14, pady=10)

        # Bind clicks to reset timer
        self.bar_frame.bind('<Button-1>', lambda e: self.reset_hide_timer())
        content.bind('<Button-1>', lambda e: self.reset_hide_timer())

        # Match label - Modern typography
        self.match_label = tk.Label(
            content,
            text="",
            font=self.normal_font,
            bg=self.bg_color,
            fg='#2d3436',
            anchor=tk.W
        )
        self.match_label.pack(side=tk.LEFT, fill=tk.X, expand=True)

        # Navigation indicator - Modern subtle styling
        self.nav_label = tk.Label(
            content,
            text="",
            font=self.small_font,
            bg=self.bg_color,
            fg='#636e72'
        )
        self.nav_label.pack(side=tk.RIGHT, padx=(8, 0))

        # Expand button - Modern button styling
        self.expand_btn = tk.Button(
            content,
            text="▼",
            font=self.small_font,
            bg=self.bg_color,
            fg=self.primary_color,
            relief=tk.FLAT,
            cursor='hand2',
            command=self.toggle_expand,
            padx=6,
            pady=2
        )
        self.expand_btn.pack(side=tk.RIGHT, padx=2)

        # Info button - Modern button styling
        info_btn = tk.Button(
            content,
            text="ℹ️",
            font=self.small_font,
            bg=self.bg_color,
            fg=self.primary_color,
            relief=tk.FLAT,
            cursor='hand2',
            command=self.show_info,
            padx=4,
            pady=2
        )
        info_btn.pack(side=tk.RIGHT, padx=4)

        # Close button - Modern button styling
        close_btn = tk.Button(
            content,
            text="✕",
            font=self.small_font,
            bg=self.bg_color,
            fg='#636e72',
            relief=tk.FLAT,
            cursor='hand2',
            command=self.hide,
            padx=4,
            pady=2
        )
        close_btn.pack(side=tk.RIGHT, padx=2)

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

        # Auto-hide after 8 seconds (reset on interaction)
        self.reset_hide_timer()

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
        """Cycle through matches - also resets hide timer"""
        if not self.matches or len(self.matches) <= 1:
            return

        self.current_index = (self.current_index + direction) % len(self.matches)
        self.update_bar_display()

        # Reset hide timer on user interaction
        self.reset_hide_timer()

        # Auto-expand when cycling to show more details
        if not self.is_expanded and len(self.matches) > 1:
            self.expand()

    def toggle_expand(self):
        """Toggle expanded view - also resets hide timer"""
        if self.is_expanded:
            self.collapse()
        else:
            self.expand()

        # Reset hide timer on user interaction
        self.reset_hide_timer()

    def expand(self):
        """Expand to show full details - updates when match changes"""
        if not self.matches:
            return

        # If already expanded, just refresh the content
        if self.is_expanded and self.popup_window:
            self._refresh_popup_content()
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

        # Bind mouse interaction to reset timer
        self.popup_window.bind('<Button-1>', lambda e: self.reset_hide_timer())
        self.popup_window.bind('<Key>', lambda e: self.reset_hide_timer())

        # Position near bar
        bar_x = self.bar_window.winfo_x()
        bar_y = self.bar_window.winfo_y()

        popup_width = 450
        popup_height = 320

        self.popup_window.geometry(f'{popup_width}x{popup_height}+{bar_x}+{bar_y + self.bar_height + 5}')

        # Shadow frame for modern depth effect
        shadow_frame = tk.Frame(self.popup_window, bg='#c8c8c8')
        shadow_frame.pack(fill=tk.BOTH, expand=True)

        # Content frame with modern flat design
        frame = tk.Frame(shadow_frame, bg='white', relief=tk.FLAT)
        frame.pack(fill=tk.BOTH, expand=True, padx=2, pady=2)

        # Header - Modern Material Design style
        header = tk.Frame(frame, bg=self.primary_color, height=58)
        header.pack(fill=tk.X)
        header.pack_propagate(False)

        tk.Label(
            header,
            text=f"{match['icon']} {match['label']}",
            font=tkfont.Font(family="Segoe UI", size=14, weight="bold"),
            bg=self.primary_color,
            fg='white'
        ).pack(side=tk.LEFT, padx=18, pady=14)

        tk.Button(
            header,
            text="▲",
            font=self.small_font,
            bg=self.primary_color,
            fg='white',
            relief=tk.FLAT,
            command=self.collapse,
            cursor='hand2',
            padx=10,
            pady=4
        ).pack(side=tk.RIGHT, padx=16)

        # Details - Modern spacing
        details_frame = tk.Frame(frame, bg='white', padx=18, pady=16)
        details_frame.pack(fill=tk.BOTH, expand=True)

        details_text = self.format_details(match['type'], match['data'])

        # Details label - Modern typography
        tk.Label(
            details_frame,
            text=details_text,
            font=self.normal_font,
            bg='white',
            fg='#2d3436',
            justify=tk.LEFT,
            anchor=tk.NW,
            wraplength=400
        ).pack(fill=tk.BOTH, expand=True)

        # Actions - Modern Material Design buttons
        actions = tk.Frame(frame, bg='#f8f9fa')
        actions.pack(fill=tk.X, padx=18, pady=12)

        # Modern button styling
        btn_style = {
            'font': self.normal_font,
            'bg': self.primary_color,
            'fg': 'white',
            'relief': tk.FLAT,
            'cursor': 'hand2',
            'padx': 14,
            'pady': 7
        }

        tk.Button(
            actions,
            text="💾 Save",
            command=self.save_snippet,
            **btn_style
        ).pack(side=tk.LEFT, padx=(0, 6))

        tk.Button(
            actions,
            text="🔍 Search",
            command=self.search_web,
            **btn_style
        ).pack(side=tk.LEFT, padx=6)

        tk.Button(
            actions,
            text="📋 Copy",
            command=self.copy_to_clipboard,
            **btn_style
        ).pack(side=tk.LEFT, padx=6)

        # Update button
        self.expand_btn.config(text="▲")

    def collapse(self):
        """Collapse back to bar"""
        self.is_expanded = False
        if self.popup_window:
            self.popup_window.destroy()
            self.popup_window = None
        self.expand_btn.config(text="▼")

    def _refresh_popup_content(self):
        """Refresh popup content when cycling through matches"""
        if not self.popup_window or not self.matches:
            return

        match = self.matches[self.current_index]

        # Clear existing content (find the frame with details)
        for widget in self.popup_window.winfo_children():
            if isinstance(widget, tk.Frame):
                # This is the shadow frame
                for child in widget.winfo_children():
                    if isinstance(child, tk.Frame):
                        # This is the content frame - update its children
                        self._update_popup_frame(child, match)
                        break
                break

    def _update_popup_frame(self, frame, match):
        """Update the popup frame with new match data"""
        # Clear existing widgets
        for widget in frame.winfo_children():
            widget.destroy()

        # Rebuild header
        header = tk.Frame(frame, bg=self.primary_color, height=58)
        header.pack(fill=tk.X)
        header.pack_propagate(False)

        tk.Label(
            header,
            text=f"{match['icon']} {match['label']}",
            font=tkfont.Font(family="Segoe UI", size=14, weight="bold"),
            bg=self.primary_color,
            fg='white'
        ).pack(side=tk.LEFT, padx=18, pady=14)

        tk.Button(
            header,
            text="▲",
            font=self.small_font,
            bg=self.primary_color,
            fg='white',
            relief=tk.FLAT,
            command=self.collapse,
            cursor='hand2',
            padx=10,
            pady=4
        ).pack(side=tk.RIGHT, padx=16)

        # Rebuild details
        details_frame = tk.Frame(frame, bg='white', padx=18, pady=16)
        details_frame.pack(fill=tk.BOTH, expand=True)

        details_text = self.format_details(match['type'], match['data'])

        tk.Label(
            details_frame,
            text=details_text,
            font=self.normal_font,
            bg='white',
            fg='#2d3436',
            justify=tk.LEFT,
            anchor=tk.NW,
            wraplength=400
        ).pack(fill=tk.BOTH, expand=True)

        # Rebuild actions
        actions = tk.Frame(frame, bg='#f8f9fa')
        actions.pack(fill=tk.X, padx=18, pady=12)

        btn_style = {
            'font': self.normal_font,
            'bg': self.primary_color,
            'fg': 'white',
            'relief': tk.FLAT,
            'cursor': 'hand2',
            'padx': 14,
            'pady': 7
        }

        tk.Button(
            actions,
            text="💾 Save",
            command=self.save_snippet,
            **btn_style
        ).pack(side=tk.LEFT, padx=(0, 6))

        tk.Button(
            actions,
            text="🔍 Search",
            command=self.search_web,
            **btn_style
        ).pack(side=tk.LEFT, padx=6)

        tk.Button(
            actions,
            text="📋 Copy",
            command=self.copy_to_clipboard,
            **btn_style
        ).pack(side=tk.LEFT, padx=6)

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

    def show_info(self):
        """Show information about this prototype"""
        info_text = """
💡 Smart Context Bar - Prototype 4

CONCEPT:
A compact bar appearing near selected text (like IDE hints),
showing context matches with minimal screen real estate.
Stays visible as long as you interact with it!

HOW TO USE:
• Bar appears automatically when you copy text
• Use ↑↓ arrows or scroll wheel to cycle through matches
• Cycling automatically expands to show full details
• Press →/Enter to expand, ← to collapse
• Bar auto-hides after 8 seconds of NO interaction
• ANY interaction (arrows, click, scroll) resets the 8s timer

KEYBOARD SHORTCUTS:
• ↑ - Previous match (resets timer, auto-expands)
• ↓/Tab - Next match (resets timer, auto-expands)
• →/Enter - Expand details (resets timer)
• ← - Collapse details
• Ctrl+S - Save snippet (resets timer)
• ESC - Hide bar immediately
• F1 - Show this help (resets timer)

MOUSE SUPPORT:
• Scroll wheel - Cycle through matches
• Click buttons - Perform actions
• Any click resets the 8-second hide timer

SPECIAL FEATURES:
• Smart auto-hide: only hides after 8s of inactivity
• Live content updates when cycling through matches
• Auto-expansion when navigating multiple matches
• Auto-positioning (avoids screen edges)
• Full keyboard and mouse navigation
• Minimal, unobtrusive design

BEST FOR:
• Users who prefer subtle, non-intrusive UIs
• Workflow integration without interruption
• Quick glances at context without focus stealing
• Keyboard-driven workflows
        """

        info_window = tk.Toplevel(self.bar_window)
        info_window.title("About This Prototype")
        info_window.geometry("580x700")
        info_window.transient(self.bar_window)
        info_window.attributes('-topmost', True)

        # Position below or above bar
        bar_x = self.bar_window.winfo_x()
        bar_y = self.bar_window.winfo_y()
        x = bar_x
        y = bar_y + self.bar_height + 10
        # If would go off screen, position above
        if y + 700 > self.bar_window.winfo_screenheight():
            y = bar_y - 710
        info_window.geometry(f"+{x}+{y}")

        # Reset hide timer when showing info
        self.reset_hide_timer()

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
        self.bar_window.bind('<Tab>', lambda e: self.cycle_match(1))
        self.bar_window.bind('<Down>', lambda e: self.cycle_match(1))
        self.bar_window.bind('<Up>', lambda e: self.cycle_match(-1))
        self.bar_window.bind('<Right>', lambda e: [self.expand(), self.reset_hide_timer()])
        self.bar_window.bind('<Return>', lambda e: [self.expand(), self.reset_hide_timer()])
        self.bar_window.bind('<Left>', lambda e: self.collapse())
        self.bar_window.bind('<Escape>', lambda e: self.hide())
        self.bar_window.bind('<Control-s>', lambda e: [self.save_snippet(), self.reset_hide_timer()])
        self.bar_window.bind('<F1>', lambda e: [self.show_info(), self.reset_hide_timer()])

        # Mouse wheel support for cycling
        self.bar_window.bind('<Button-4>', lambda e: self.cycle_match(-1))  # Scroll up
        self.bar_window.bind('<Button-5>', lambda e: self.cycle_match(1))   # Scroll down
        self.bar_window.bind('<MouseWheel>', lambda e: self.cycle_match(-1 if e.delta > 0 else 1))  # Windows/Mac

    def hide(self):
        """Hide the bar"""
        self.collapse()
        self.bar_window.withdraw()

        # Cancel any pending hide timer
        if self.hide_timer_id:
            self.bar_window.after_cancel(self.hide_timer_id)
            self.hide_timer_id = None

    def reset_hide_timer(self):
        """Reset the auto-hide timer (8 seconds from now)"""
        # Cancel existing timer
        if self.hide_timer_id:
            self.bar_window.after_cancel(self.hide_timer_id)

        # Start new timer
        self.hide_timer_id = self.bar_window.after(8000, self.hide)

    def run(self):
        """Run the main loop"""
        self.bar_window.mainloop()

    def update(self):
        """Update GUI"""
        try:
            self.bar_window.update()
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
            self.bar_window.quit()
            self.bar_window.destroy()
        except:
            pass
        sys.exit(0)
