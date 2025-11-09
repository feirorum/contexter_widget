# Prototype 1: Action Wheel

## Overview

A compact circular action wheel that appears near the cursor when text is selected, providing quick access to context information and actions.

## Design Philosophy

**Fast, Minimal, Contextual**: The action wheel prioritizes speed and minimal visual interruption. It appears exactly where the user needs it and disappears when not needed.

## Visual Design

### Initial State (Collapsed)
```
     [Save]
        |
[Search]-⊕-[Copy]
        |
    [Details]
```

- Small circular hub (30px diameter)
- 4 primary quick actions in cardinal directions
- Semi-transparent background (#667eea with 90% opacity)
- Positioned 20px offset from cursor to avoid covering selection

### Detected Items Ring
```
      [Contact]
         /
   [Save]-⊕-[Copy]
       / | \
[Abbr] | [Project]
    [Search]
```

- Detected items appear as small segments around the outer ring
- Top 3-5 items based on confidence score
- Color-coded badges:
  - Contact: Blue (#667eea)
  - Abbreviation: Purple (#764ba2)
  - Project: Orange (#fd7e14)
  - Snippet: Green (#28a745)
- Icons + truncated labels

### Expanded State
```
┌─────────────────────────────┐
│ "John Doe"           [Type] │
├─────────────────────────────┤
│ 👤 John Doe                 │
│ ✉  john@example.com         │
│ 📋 Senior Engineer          │
│                             │
│ Last contact: 2024-03-15    │
│                             │
│ [View Details] [Edit]       │
└─────────────────────────────┘
```

- Expands to 400x300px popup
- Shows detailed information for selected item
- Smooth transition animation (200ms)

## Interaction Flows

### Flow 1: Selection → Quick Action
1. User selects text "John Doe"
2. Action wheel appears near cursor (fade-in 150ms)
3. Top match highlighted in outer ring: "👤 John"
4. User clicks "Save" button → Snippet saved
5. Toast confirmation → Wheel fades out

**Time to action: ~1 second**

### Flow 2: Selection → Navigate → Expand
1. User selects text "API"
2. Action wheel appears with detected items:
   - "API" (Abbreviation) - highlighted
   - "John Doe" (Contact)
   - "Platform API" (Project)
3. User presses ↓ arrow key → Cycles to "John Doe"
4. User presses → arrow key → Expands to full details popup
5. User presses ESC → Closes and returns to action wheel
6. User presses ESC again → Closes action wheel

**Keyboard shortcuts:**
- ↑/↓: Cycle through detected items
- →: Expand to details
- ←: Collapse back to wheel
- ESC: Close current level (details → wheel → close)
- Enter: Execute default action (open details)
- S: Quick save
- W: Quick web search
- C: Quick copy

### Flow 3: Mouse-Only Interaction
1. User selects text
2. Action wheel appears
3. User hovers over outer ring segment → Preview tooltip appears
4. User clicks segment → Expands to full details
5. User clicks outside wheel → Closes

## Component Structure

```
ActionWheelWidget
├── WheelHub (center button area)
│   ├── SaveButton
│   ├── SearchButton
│   ├── CopyButton
│   └── DetailsButton
├── DetectedItemsRing (outer segments)
│   ├── ItemSegment (contact)
│   ├── ItemSegment (abbreviation)
│   └── ItemSegment (project)
└── DetailsPopup (expandable)
    ├── HeaderBar
    ├── ContentArea
    └── ActionBar
```

## Technical Specifications

### Positioning Algorithm
```python
def calculate_wheel_position(selection_rect, cursor_pos):
    # Prefer: below and to the right of selection
    x = selection_rect.right + 20
    y = selection_rect.bottom + 20

    # Adjust if would go off-screen
    if x + WHEEL_WIDTH > screen.width:
        x = selection_rect.left - WHEEL_WIDTH - 20
    if y + WHEEL_HEIGHT > screen.height:
        y = selection_rect.top - WHEEL_HEIGHT - 20

    return (x, y)
```

### Keyboard Navigation State Machine
```
States:
- WHEEL_VISIBLE: Wheel shown, no item selected
- ITEM_SELECTED: Item highlighted in ring
- DETAILS_EXPANDED: Popup showing details

Transitions:
WHEEL_VISIBLE + ↓/↑ → ITEM_SELECTED (first item)
ITEM_SELECTED + ↓/↑ → ITEM_SELECTED (next/prev)
ITEM_SELECTED + → → DETAILS_EXPANDED
DETAILS_EXPANDED + ← → ITEM_SELECTED
ITEM_SELECTED + ESC → WHEEL_VISIBLE
WHEEL_VISIBLE + ESC → CLOSED
```

### Animation Timings
- Fade in: 150ms ease-out
- Fade out: 100ms ease-in
- Expand to details: 200ms ease-out
- Collapse to wheel: 150ms ease-in
- Item highlight: 50ms

## Configuration Options

```python
class ActionWheelConfig:
    # Appearance
    wheel_size: int = 200  # diameter in pixels
    hub_size: int = 30
    segment_count: int = 5
    opacity: float = 0.9

    # Behavior
    show_delay: int = 0  # ms after selection
    auto_hide_delay: int = 0  # 0 = manual close only
    follow_cursor: bool = False  # Re-position on cursor move

    # Keyboard
    enable_keyboard: bool = True
    quick_action_keys: dict = {
        's': 'save',
        'w': 'search_web',
        'c': 'copy'
    }
```

## Implementation Phases

### Phase 1: Basic Wheel (MVP)
- [x] Circular UI with center hub
- [x] 4 quick action buttons
- [x] Basic positioning logic
- [x] Click handlers for actions
- [x] ESC to close

### Phase 2: Detected Items Ring
- [ ] Outer ring segments for detected items
- [ ] Color-coded badges by type
- [ ] Mouse hover previews
- [ ] Click to select item

### Phase 3: Keyboard Navigation
- [ ] Arrow key navigation
- [ ] State machine implementation
- [ ] Quick action hotkeys
- [ ] Visual feedback for selection

### Phase 4: Details Expansion
- [ ] Popup window for details
- [ ] Smooth expand/collapse animation
- [ ] Content rendering by type
- [ ] Back navigation

### Phase 5: Polish
- [ ] Smooth animations
- [ ] Accessibility features
- [ ] Configurable options
- [ ] Edge case handling

## Success Metrics

- **Speed**: Action wheel appears within 150ms of selection
- **Efficiency**: Most common actions achievable in 1-2 interactions
- **Discoverability**: Users can figure out keyboard shortcuts within 3 uses
- **Satisfaction**: Users prefer it over current two-pane widget

## Challenges & Solutions

**Challenge 1**: Positioning near cursor might cover important content
- **Solution**: Smart positioning algorithm that avoids covering selection and uses free screen space

**Challenge 2**: Radial UI unfamiliar to users
- **Solution**: Provide keyboard shortcuts as alternative and show hints on first use

**Challenge 3**: Limited space for displaying information
- **Solution**: Focus on top 3-5 items only, use expansion for full details

**Challenge 4**: Cross-platform cursor tracking
- **Solution**: Use platform-specific APIs with fallback to mouse event tracking

## User Testing Questions

1. How quickly can you find the information you need?
2. Is the action wheel positioned well or does it get in the way?
3. Do you prefer keyboard or mouse interaction?
4. What additional actions would you like quick access to?
5. Is the radial layout intuitive or confusing?
