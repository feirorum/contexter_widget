# Prototype 2: Hotkey-Activated Overlay

## Overview

A full-screen overlay interface that appears when triggered by a global hotkey, showing context analysis for the current clipboard or most recent selection.

## Design Philosophy

**Intentional, Focused, Powerful**: Inspired by Spotlight, Alfred, and Raycast, this interface gives users complete control over when to see context, with a beautiful full-screen experience optimized for scanning and exploring information.

## Visual Design

### Overlay Appearance
```
┌─────────────────────────────────────────────┐
│ [Dark semi-transparent backdrop 60% opacity]│
│                                             │
│   ┌─────────────────────────────────────┐  │
│   │  🔍 Context Tool                    │  │
│   ├─────────────────────────────────────┤  │
│   │  [ Search or paste text... ]   ⌘K  │  │
│   ├─────────────────────────────────────┤  │
│   │                                     │  │
│   │  "John Doe"  [Contact] [Score: 95%]│  │
│   │  ─────────────────────────────────  │  │
│   │  👤 John Doe                        │  │
│   │  ✉  john@example.com               │  │
│   │  📋 Senior Engineer                 │  │
│   │                                     │  │
│   │  ─────────────────────────────────  │  │
│   │                                     │  │
│   │  "API" - Abbreviation               │  │
│   │  Application Programming Interface  │  │
│   │                                     │  │
│   ├─────────────────────────────────────┤  │
│   │  💡 Press ↑↓ to navigate           │  │
│   │  ↵ to expand • ⌘S to save • ESC    │  │
│   └─────────────────────────────────────┘  │
│                                             │
└─────────────────────────────────────────────┘
```

### Layout Specifications
- Centered dialog: 800px wide × 600px tall
- Semi-transparent dark backdrop (#000000 60% opacity)
- Dialog background: White with subtle shadow
- Border radius: 12px
- Padding: 24px
- Glass-morphism effect (optional): Blur backdrop

### Color Scheme
- Primary: #667eea (purple-blue gradient)
- Background: #ffffff
- Text: #333333
- Muted text: #666666
- Border: #e0e0e0
- Hover: #f5f7fa

## Interaction Flows

### Flow 1: Hotkey Trigger → Quick View
1. User copies text "John Doe" to clipboard
2. User presses Ctrl+Space (or configured hotkey)
3. Overlay appears with fade-in (200ms)
4. Shows analysis of clipboard content
5. User reviews information
6. User presses ESC → Overlay fades out

**Time to information: ~0.5 seconds**

### Flow 2: Manual Search
1. User presses Ctrl+Space
2. Overlay appears with empty search box focused
3. User types "API"
4. Results update in real-time as user types
5. User sees abbreviation match
6. User presses ↓ to navigate to next result
7. User presses Enter to expand details
8. Expanded view slides in from right
9. User presses ESC to go back
10. User presses ESC again to close overlay

### Flow 3: History Navigation
1. User opens overlay (Ctrl+Space)
2. User presses Ctrl+H to show history
3. List of recent analyses appears
4. User uses ↑↓ to navigate
5. User presses Enter to load a past analysis
6. Results display
7. User can search/filter history by typing

### Flow 4: Quick Actions
1. User opens overlay with content
2. User sees matched contact
3. User presses Ctrl+S → Save snippet dialog
4. User presses Ctrl+W → Opens web search in browser
5. User presses Ctrl+C → Copies match to clipboard
6. User presses Ctrl+E → Opens edit dialog for contact

## Component Structure

```
HotkeyOverlayWidget
├── Backdrop (full-screen semi-transparent)
├── DialogContainer (centered 800×600)
│   ├── HeaderBar
│   │   ├── Title
│   │   ├── SearchBox
│   │   └── CloseButton
│   ├── ResultsArea
│   │   ├── ResultCard (contact)
│   │   ├── ResultCard (abbreviation)
│   │   ├── ResultCard (project)
│   │   └── NoResultsMessage
│   ├── DetailsSidepanel (slides in on expand)
│   │   ├── DetailHeader
│   │   ├── DetailContent
│   │   └── DetailActions
│   └── FooterBar (keyboard shortcuts)
└── HistoryPanel (slides in from left)
```

## Technical Specifications

### Global Hotkey Registration

```python
import keyboard  # or pynput

class GlobalHotkeyManager:
    def __init__(self, hotkey='ctrl+space'):
        self.hotkey = hotkey
        self.callback = None

    def register(self, callback):
        """Register global hotkey"""
        self.callback = callback
        keyboard.add_hotkey(self.hotkey, self._on_trigger)

    def _on_trigger(self):
        """Called when hotkey pressed"""
        if self.callback:
            self.callback()

    def unregister(self):
        """Clean up"""
        keyboard.remove_hotkey(self.hotkey)
```

### Search & Analysis State

```python
class OverlayState:
    mode: str  # 'clipboard', 'search', 'history'
    current_text: str
    results: List[Match]
    selected_index: int
    history: List[HistoryEntry]
    details_visible: bool
    expanded_item: Optional[Match]
```

### Keyboard Shortcuts

| Shortcut | Action |
|----------|--------|
| Ctrl+Space | Open overlay |
| ESC | Close overlay / Go back |
| ↑/↓ | Navigate results |
| Enter | Expand selected result |
| Ctrl+S | Save snippet |
| Ctrl+W | Search web |
| Ctrl+C | Copy to clipboard |
| Ctrl+E | Edit item |
| Ctrl+H | Show history |
| Ctrl+K | Focus search box |
| Ctrl+, | Open settings |

### Animation Specifications

```css
/* Overlay fade-in */
@keyframes overlayFadeIn {
    from {
        opacity: 0;
    }
    to {
        opacity: 1;
    }
}

/* Dialog scale-in */
@keyframes dialogScaleIn {
    from {
        transform: scale(0.9);
        opacity: 0;
    }
    to {
        transform: scale(1);
        opacity: 1;
    }
}

/* Detail panel slide-in */
@keyframes detailSlideIn {
    from {
        transform: translateX(100%);
    }
    to {
        transform: translateX(0);
    }
}
```

- Overlay fade: 200ms ease-out
- Dialog scale: 250ms ease-out-back
- Details slide: 300ms ease-out
- Results update: 150ms fade-in

## Configuration Options

```python
class HotkeyOverlayConfig:
    # Hotkey
    global_hotkey: str = 'ctrl+space'

    # Appearance
    dialog_width: int = 800
    dialog_height: int = 600
    backdrop_opacity: float = 0.6
    blur_backdrop: bool = True

    # Behavior
    mode: str = 'clipboard'  # 'clipboard', 'search', 'auto'
    show_history: bool = True
    history_limit: int = 50
    auto_focus_search: bool = True

    # Search
    search_debounce_ms: int = 300
    min_search_length: int = 2
    show_empty_state: bool = True
```

## History Feature

### History Entry Structure
```python
@dataclass
class HistoryEntry:
    timestamp: datetime
    text: str
    matches: List[Match]
    source: str  # 'clipboard', 'search', 'selection'
```

### History Panel UI
```
┌────────────────────┐
│ Recent Analyses    │
├────────────────────┤
│ 🕐 2 min ago       │
│ "John Doe"         │
│ → Contact match    │
├────────────────────┤
│ 🕐 5 min ago       │
│ "API"              │
│ → Abbreviation     │
├────────────────────┤
│ 🕐 10 min ago      │
│ "ProjectX"         │
│ → Project          │
└────────────────────┘
```

## Implementation Phases

### Phase 1: Basic Overlay (MVP)
- [x] Global hotkey registration
- [x] Full-screen overlay with backdrop
- [x] Centered dialog
- [x] Show clipboard analysis
- [x] ESC to close

### Phase 2: Search Interface
- [ ] Search box with real-time analysis
- [ ] Results display with cards
- [ ] Keyboard navigation (↑↓)
- [ ] No results state

### Phase 3: Details Expansion
- [ ] Expandable details panel
- [ ] Slide-in animation
- [ ] Navigate back to results
- [ ] Full detail rendering

### Phase 4: History
- [ ] Store analysis history
- [ ] History panel UI
- [ ] Search/filter history
- [ ] Load past analyses

### Phase 5: Polish
- [ ] All keyboard shortcuts
- [ ] Quick actions (save, search, copy)
- [ ] Smooth animations
- [ ] Settings panel
- [ ] Themes (light/dark)

## Success Metrics

- **Trigger speed**: Overlay appears within 200ms of hotkey press
- **Usability**: Users can navigate entirely with keyboard
- **Discoverability**: Keyboard shortcuts visible and memorable
- **Performance**: History with 50+ items loads instantly

## Challenges & Solutions

**Challenge 1**: Global hotkey conflicts with other apps
- **Solution**: Allow customizable hotkey, check for conflicts, show warning

**Challenge 2**: Clipboard monitoring while overlay is hidden
- **Solution**: Background service monitors clipboard, caches recent analysis

**Challenge 3**: Large result sets slow to render
- **Solution**: Virtual scrolling, limit initial render to top 20 results

**Challenge 4**: History storage and privacy
- **Solution**: Local storage only, configurable history limit, clear history option

## Comparison to Current Widget

| Feature | Current Widget | Hotkey Overlay |
|---------|----------------|----------------|
| Trigger | Automatic | Manual |
| Control | Passive | Active |
| Screen Space | Persistent | Temporary |
| Information Density | High | Very High |
| Distraction | Medium | Low |
| Speed | Instant | Hotkey press |

## User Testing Questions

1. Is the hotkey easy to remember and use?
2. Do you prefer automatic or manual triggering?
3. Is the overlay size appropriate?
4. Are the keyboard shortcuts intuitive?
5. Would you use the history feature?
6. Does the overlay feel too intrusive or just right?
