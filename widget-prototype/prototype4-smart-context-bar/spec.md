# Prototype 4: Smart Context Bar

## Overview

A compact horizontal bar that appears directly above or below selected text, showing inline context hints like IDE autocomplete or spell-check suggestions.

## Design Philosophy

**Inline, Fast, Non-Intrusive**: Inspired by IDE code completion, grammar checkers, and inline comments, this interface appears exactly where the user's attention is, providing context without requiring eye movement or focus change.

## Visual Design

### Compact Mode (Initial State)
```
This is some text about John Doe who works at...
                        └──────┐
                    ┌───────────────────────────┐
                    │ 👤 John Doe (Contact) [▼] │
                    └───────────────────────────┘
```

### Multi-Match Mode
```
The API documentation explains...
     └──────┐
  ┌──────────────────────────────────────┐
  │ 🟣 API (Abbreviation)          [1/3] │
  │ Tab ↹ • ↑↓ Navigate • → Expand      │
  └──────────────────────────────────────┘
```

### Expanded Popup Mode
```
The API documentation explains...
     └──────┐
  ┌───────────────────────────────────────┐
  │ 🟣 Abbreviation: API                  │
  ├───────────────────────────────────────┤
  │ API = Application Programming...      │
  │                                       │
  │ A standardized set of protocols...    │
  │                                       │
  │ Category: Technology                  │
  │ Examples: REST API, GraphQL API       │
  │                                       │
  │ [🔍 Search] [💾 Save] [📋 Copy]       │
  └───────────────────────────────────────┘
```

### Visual Specifications
- Compact bar: 250px × 36px
- Expanded popup: 400px × auto (max 500px)
- Border radius: 6px
- Shadow: 0 4px 12px rgba(0,0,0,0.15)
- Background: White (#ffffff)
- Border: 1px solid #e0e0e0
- Connector line: 2px dotted #ccc

### Type Color Coding
- 🔵 Contact: #667eea
- 🟣 Abbreviation: #764ba2
- 🟠 Project: #fd7e14
- 🟢 Snippet: #28a745

## Interaction Flows

### Flow 1: Single Match → Quick View
1. User selects "John Doe"
2. Context bar appears above/below (150ms fade-in)
3. Shows: "👤 John Doe (Contact) [▼]"
4. User continues reading (no action needed)
5. After 5 seconds → Bar fades out
6. OR user presses ESC → Immediate close

**Passive flow - no interruption**

### Flow 2: Multiple Matches → Navigate
1. User selects "API"
2. Bar appears: "🟣 API (Abbreviation) [1/3]"
3. User presses Tab or ↓ → Cycles to "🔵 API Team (Contact) [2/3]"
4. User presses Tab again → "🟠 API Project [3/3]"
5. User presses Tab again → Back to [1/3]
6. User sees what they need, ESC to close

**Fast keyboard navigation**

### Flow 3: Expand for Details
1. User selects "John Doe"
2. Bar appears: "👤 John Doe (Contact) [▼]"
3. User presses → or clicks [▼] button
4. Popup expands with smooth animation (200ms)
5. Shows full contact details
6. User presses ← → Collapses back to bar
7. User presses ESC → Closes completely

**Progressive disclosure**

### Flow 4: Quick Action
1. User selects text
2. Bar appears with match
3. User presses Ctrl+S → Smart save
4. User presses Ctrl+W → Web search
5. User presses Ctrl+C → Copy match info
6. Action executes, bar shows confirmation toast
7. Bar auto-closes after 2 seconds

**Action without leaving text**

### Flow 5: No Match
1. User selects "randomtext123"
2. Bar appears: "ℹ️ No context found [Save as snippet]"
3. User can click to save
4. OR press ESC to dismiss
5. Bar fades out after 3 seconds

**Graceful handling**

## Component Structure

```
SmartContextBar
├── CompactBar
│   ├── TypeIcon
│   ├── MatchLabel
│   ├── NavigationIndicator (1/3)
│   └── ExpandButton (▼)
├── ExpandedPopup
│   ├── Header
│   │   ├── TypeBadge
│   │   ├── Title
│   │   └── CollapseButton (▲)
│   ├── ContentArea
│   │   └── DetailFields
│   └── ActionBar
│       ├── SearchButton
│       ├── SaveButton
│       └── CopyButton
└── ConnectorLine (to selection)
```

## Technical Specifications

### Positioning Algorithm

```python
def calculate_bar_position(selection_rect, window_bounds):
    """
    Calculate optimal position for context bar
    relative to selected text
    """
    bar_width = 250
    bar_height = 36

    # Try above first
    x = selection_rect.center_x - (bar_width / 2)
    y = selection_rect.top - bar_height - 10

    # Check if goes off-screen
    if y < window_bounds.top + 20:
        # Position below instead
        y = selection_rect.bottom + 10

    # Adjust horizontal if needed
    if x < window_bounds.left + 10:
        x = window_bounds.left + 10
    elif x + bar_width > window_bounds.right - 10:
        x = window_bounds.right - bar_width - 10

    # Keep connector pointing to selection center
    connector_x = selection_rect.center_x - x

    return {
        'x': x,
        'y': y,
        'connector_x': connector_x,
        'position': 'above' if y < selection_rect.top else 'below'
    }
```

### State Machine

```python
class ContextBarState(Enum):
    HIDDEN = 0
    COMPACT = 1
    EXPANDED = 2

class ContextBarController:
    def __init__(self):
        self.state = ContextBarState.HIDDEN
        self.matches = []
        self.current_index = 0

    def on_selection(self, text, matches):
        self.matches = matches
        self.current_index = 0
        self.transition_to(ContextBarState.COMPACT)

    def cycle_next(self):
        if self.state == ContextBarState.COMPACT:
            self.current_index = (self.current_index + 1) % len(self.matches)
            self.update_display()

    def expand(self):
        if self.state == ContextBarState.COMPACT:
            self.transition_to(ContextBarState.EXPANDED)

    def collapse(self):
        if self.state == ContextBarState.EXPANDED:
            self.transition_to(ContextBarState.COMPACT)

    def close(self):
        self.transition_to(ContextBarState.HIDDEN)
```

### Keyboard Handling

```python
def on_key_press(event):
    if state == ContextBarState.COMPACT:
        if event.key in ['Tab', 'Down']:
            cycle_next()
            return True  # Consume event
        elif event.key in ['Right', 'Enter']:
            expand()
            return True
        elif event.key == 'Escape':
            close()
            return True

    elif state == ContextBarState.EXPANDED:
        if event.key == 'Left':
            collapse()
            return True
        elif event.key == 'Escape':
            close()
            return True
        elif event.key == 's' and event.ctrl:
            save_current()
            return True

    return False  # Don't consume
```

## Configuration Options

```python
class SmartContextBarConfig:
    # Positioning
    preferred_position: str = 'above'  # 'above', 'below', 'auto'
    offset_from_selection: int = 10  # pixels

    # Appearance
    compact_width: int = 250
    compact_height: int = 36
    expanded_width: int = 400
    expanded_max_height: int = 500
    show_connector: bool = True

    # Behavior
    auto_show: bool = True
    auto_hide: bool = True
    auto_hide_delay: int = 5  # seconds
    persist_on_hover: bool = True
    expand_on_click: bool = True

    # Animation
    fade_in_duration: int = 150  # ms
    fade_out_duration: int = 100
    expand_duration: int = 200
    collapse_duration: int = 150

    # Keyboard
    enable_tab_navigation: bool = True
    enable_quick_actions: bool = True
```

## Edge Cases & Solutions

### Edge Case 1: Selection Near Screen Edge
```python
def handle_screen_edge(bar_rect, screen_rect):
    """Adjust position if bar would go off-screen"""
    if bar_rect.right > screen_rect.right:
        # Move left
        bar_rect.x -= (bar_rect.right - screen_rect.right)

    if bar_rect.bottom > screen_rect.bottom:
        # Position above instead
        bar_rect.y = selection_rect.top - bar_rect.height - 10

    return bar_rect
```

### Edge Case 2: Multi-Line Selection
```python
def get_optimal_anchor_point(selection_ranges):
    """
    For multi-line selections, choose best anchor
    - Use first line if selection is downward
    - Use last line if selection is upward
    - Default to middle of first line
    """
    first_line = selection_ranges[0]
    return first_line.center
```

### Edge Case 3: Selection in Scrollable Content
```python
def track_selection_scroll(selection_element):
    """
    Update bar position when content scrolls
    - Listen to scroll events
    - Recalculate position
    - If scrolled out of view, hide bar
    """
    if not is_in_viewport(selection_element):
        hide_bar()
    else:
        update_position()
```

### Edge Case 4: Rapid Selections
```python
def debounce_selection(text, delay=300):
    """
    Debounce rapid selections to avoid flashing
    - Cancel pending show if new selection within delay
    - Show only the last selection
    """
    if pending_show_timer:
        cancel_timer(pending_show_timer)

    pending_show_timer = schedule(
        lambda: show_bar(text),
        delay
    )
```

## Implementation Phases

### Phase 1: Basic Bar (MVP)
- [x] Detect text selection
- [x] Position bar above/below
- [x] Show single match
- [x] ESC to close
- [x] Auto-hide after delay

### Phase 2: Navigation
- [ ] Multiple matches support
- [ ] Tab/Arrow navigation
- [ ] Match counter (1/3)
- [ ] Cycle through matches

### Phase 3: Expansion
- [ ] Expand/collapse animation
- [ ] Detailed popup view
- [ ] Full content rendering
- [ ] Progressive disclosure

### Phase 4: Actions
- [ ] Quick action buttons
- [ ] Keyboard shortcuts
- [ ] Save, search, copy actions
- [ ] Confirmation toasts

### Phase 5: Polish
- [ ] Smooth positioning
- [ ] Edge case handling
- [ ] Connector line visual
- [ ] Accessibility features
- [ ] Theme support

## Platform Considerations

### Desktop (tkinter)
```python
# Challenge: Position relative to text selection
# Solution: Use pyautogui to get cursor position as proxy

import pyautogui

def get_selection_position():
    # Use cursor position as approximation
    x, y = pyautogui.position()
    return (x, y)
```

### Web (Browser Extension)
```javascript
// Ideal environment for this pattern
function getSelectionRect() {
    const selection = window.getSelection();
    const range = selection.getRangeAt(0);
    return range.getBoundingClientRect();
}
```

## Success Metrics

- **Speed**: Bar appears within 150ms of selection
- **Accuracy**: Positioned without obscuring selection >95% of time
- **Efficiency**: Users can navigate matches without losing focus
- **Satisfaction**: Users prefer inline context to separate window

## Challenges & Solutions

**Challenge 1**: Accurate positioning in native apps
- **Solution**: Use accessibility APIs or cursor position as proxy

**Challenge 2**: Bar might obscure nearby text
- **Solution**: Smart positioning algorithm, try above then below, adjust horizontally

**Challenge 3**: Conflicts with native tooltips/menus
- **Solution**: Delay appearance slightly (150ms), higher z-index

**Challenge 4**: Multi-window applications
- **Solution**: Track active window, position relative to that window

## Comparison to IDE Autocomplete

| Feature | IDE Autocomplete | Smart Context Bar |
|---------|------------------|-------------------|
| Trigger | Typing | Selection |
| Position | Below cursor | Above/below selection |
| Content | Code completions | Context information |
| Interaction | Enter to accept | View and actions |
| Duration | Until dismissed | Auto-hide |

## Accessibility

### Keyboard-Only Support
- All functions accessible via keyboard
- Clear visual focus indicators
- Screen reader announcements

### High Contrast Mode
- Respect system theme
- Sufficient color contrast ratios
- Clear borders and separators

### Screen Reader Support
```html
<div role="complementary" aria-label="Context information">
    <div role="region" aria-live="polite">
        Contact: John Doe
    </div>
</div>
```

## User Testing Questions

1. Does the bar appear where you expect it?
2. Does it ever cover text you're trying to read?
3. Is Tab navigation intuitive for cycling matches?
4. How often do you expand to see full details?
5. Is the auto-hide timing appropriate?
6. Would you prefer this over a separate window?
