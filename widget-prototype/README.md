# Widget UX Prototypes

This directory contains experimental widget UX prototypes for the Context Tool, exploring different interaction patterns and visual designs.

## Overview

We've prototyped 4 diverse widget concepts to explore optimal UX for context-aware information display:

1. **Action Wheel** - Radial menu appearing near selection
2. **Hotkey Overlay** - Full-screen overlay triggered by hotkey
3. **Always-On Sidebar** - Persistent panel docked to screen edge
4. **Smart Context Bar** - Inline bar appearing above/below selection

## Running Prototypes

Each prototype can be run using the `--prototype` flag:

```bash
# Prototype 1: Action Wheel
python main.py --widget --prototype 1

# Prototype 2: Hotkey Overlay
python main.py --widget --prototype 2

# Prototype 3: Always-On Sidebar
python main.py --widget --prototype 3

# Prototype 4: Smart Context Bar
python main.py --widget --prototype 4

# Default widget (original)
python main.py --widget
```

## Directory Structure

```
widget-prototype/
├── BRAINSTORMING.md          # Concept brainstorming and evaluation
├── README.md                 # This file
├── prototype1-action-wheel/
│   ├── spec.md              # Detailed specification
│   └── action_wheel_widget.py
├── prototype2-hotkey-overlay/
│   ├── spec.md
│   └── hotkey_overlay_widget.py
├── prototype3-always-on-sidebar/
│   ├── spec.md
│   └── sidebar_widget.py
└── prototype4-smart-context-bar/
    ├── spec.md
    └── context_bar_widget.py
```

## Prototype Comparison

| Prototype | Trigger | Visual | Best For |
|-----------|---------|--------|----------|
| Action Wheel | Selection | Compact radial | Power users, quick actions |
| Hotkey Overlay | Manual hotkey | Full-screen | Focused lookups, research |
| Always-On Sidebar | Auto + manual | Persistent panel | Continuous reference |
| Smart Context Bar | Selection | Inline hint | Text workflows, minimal disruption |

## Implementation Status

### Prototype 1: Action Wheel
- [x] Basic circular UI
- [x] Quick action buttons
- [x] Positioning near cursor
- [x] Keyboard navigation (↑↓→←)
- [x] ESC to close
- [ ] Animated expansion to details

### Prototype 2: Hotkey Overlay
- [x] Global hotkey registration
- [x] Full-screen overlay
- [x] Search interface
- [x] Keyboard navigation
- [ ] History panel
- [ ] Details expansion

### Prototype 3: Always-On Sidebar
- [x] Dockable sidebar window
- [x] Expand/collapse animation
- [x] Display results
- [ ] Pin functionality
- [ ] History section
- [ ] Auto-collapse

### Prototype 4: Smart Context Bar
- [x] Inline positioning
- [x] Compact bar display
- [x] Tab navigation through matches
- [x] Expand to details
- [ ] Connector line visual
- [ ] Edge case handling

## Design Goals

All prototypes share these design goals:

1. **Fast**: Information appears within 150-200ms
2. **Keyboard-friendly**: Full keyboard navigation support
3. **Unobtrusive**: Minimal disruption to workflow
4. **Informative**: Clear, scannable information display
5. **Actionable**: Quick access to common actions

## Unique Features

### Action Wheel
- Radial UI pattern (innovative)
- Cursor-relative positioning
- Quick action hub with item ring

### Hotkey Overlay
- User-controlled visibility
- Full-screen information density
- History and search capabilities

### Always-On Sidebar
- Persistent reference
- Pinned items across sessions
- Glanceable at any time

### Smart Context Bar
- Inline positioning (like IDE hints)
- Tab-based navigation
- Progressive disclosure

## Technical Notes

### Shared Components

All prototypes share:
- Database connection
- Context analyzer
- Pattern matcher
- Smart saver

### Platform Support

- **Desktop**: tkinter-based implementations
- **Future**: Browser extension versions for prototypes 2 and 4

### Dependencies

```bash
pip install pyperclip  # Clipboard monitoring
pip install keyboard   # Global hotkeys (prototype 2)
pip install pyautogui  # Cursor positioning (prototype 1, 4)
```

## Evaluation Criteria

When testing prototypes, consider:

1. **Speed**: How fast can you get information?
2. **Learnability**: How quickly can you learn the interface?
3. **Efficiency**: How many actions to complete common tasks?
4. **Satisfaction**: Do you enjoy using it?
5. **Context Fit**: Does it fit your workflow?

## Feedback

Please test each prototype and provide feedback on:

- Which prototype do you prefer overall?
- What do you like/dislike about each?
- Any bugs or usability issues?
- Feature requests or improvements?

## Next Steps

1. Implement remaining features for each prototype
2. Gather user feedback and testing data
3. Identify the most promising approach(es)
4. Refine and polish selected prototype(s)
5. Consider hybrid approaches combining best features

## License

Part of the Context Tool project.
