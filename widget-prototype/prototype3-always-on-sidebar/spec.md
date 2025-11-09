# Prototype 3: Always-On Sidebar

## Overview

A persistent sidebar panel that docks to the edge of the screen, continuously displaying context information for the most recent selection or clipboard change.

## Design Philosophy

**Persistent, Glanceable, Unobtrusive**: Like Obsidian's side panels or IDE tool windows, this sidebar is always available for reference without requiring explicit activation. It becomes part of the workspace, providing continuous context awareness.

## Visual Design

### Collapsed State (Thin Strip)
```
┃
┃ C
┃ O
┃ N
┃ T
┃ E
┃ X
┃ T
┃
┃ 📋 3
┃ 👤 2
┃ 📁 1
┃
┃ ⚙
┃
```
- 40px wide vertical strip
- Docked to left or right edge
- Vertical text "CONTEXT"
- Badge counts for recent items
- Settings icon at bottom
- Semi-transparent when no recent activity

### Expanded State (Full Panel)
```
┌─────────────────────────────┐
│ Context Tool            [―][×]│
├─────────────────────────────┤
│ 📌 Pinned                   │
│                             │
│ [Contact: John Doe    ] [×] │
│                             │
├─────────────────────────────┤
│ 📋 Latest: "API"            │
├─────────────────────────────┤
│                             │
│ 🟣 Abbreviation             │
│ API = Application...        │
│ [Expand ▼]                  │
│                             │
│ 🔵 Contact                  │
│ 👤 John Doe                 │
│ ✉ john@example.com          │
│ [Expand ▼]                  │
│                             │
│ 🟠 Project                  │
│ 📁 Platform API             │
│ Status: Active              │
│ [Expand ▼]                  │
│                             │
├─────────────────────────────┤
│ 🕐 History                  │
│ "John Doe" - 2 min ago      │
│ "API" - 5 min ago           │
│                             │
└─────────────────────────────┘
```

### Dimensions
- Collapsed: 40px wide
- Expanded: 320px wide (configurable 250-400px)
- Full height of screen
- Smooth expand/collapse transition (250ms)

### Visual States
- **Active**: Full opacity, shows all content
- **Inactive**: 85% opacity, dims when not in focus
- **Hover**: Highlights on mouse over
- **Pinned Item**: Yellow left border indicator

## Interaction Flows

### Flow 1: Auto-Expand on Selection
1. User selects text "John Doe"
2. Sidebar auto-expands from collapsed state
3. Analysis results appear with smooth fade-in
4. After 10 seconds of no interaction → Auto-collapse (optional)
5. User can pin to keep expanded

### Flow 2: Manual Expand/Browse
1. Sidebar in collapsed state
2. User hovers over collapsed strip
3. Preview tooltip appears after 500ms
4. User clicks anywhere on strip → Expands
5. User browses pinned items and history
6. User clicks collapse button → Collapses back

### Flow 3: Pin Important Context
1. User selects text, sidebar shows results
2. User sees important contact "Jane Smith"
3. User clicks pin icon on the contact card
4. Contact moves to "Pinned" section at top
5. Pinned item persists across sessions
6. User can unpin later

### Flow 4: History Navigation
1. User scrolls to history section
2. Shows last 20 analyses with timestamps
3. User clicks on history item "API - 5 min ago"
4. Results area updates to show that analysis
5. User can re-pin items from history

### Flow 5: Continuous Reference
1. User working on document about "ProjectX"
2. Selects "ProjectX" → Sidebar shows project details
3. Pins project info for reference
4. Continues writing, glancing at sidebar
5. Selects person name → Adds contact to sidebar
6. Has both project + contact visible for reference

## Component Structure

```
SidebarWidget
├── CollapseHandle (drag to resize)
├── HeaderBar
│   ├── Title
│   ├── MinimizeButton
│   └── CloseButton
├── PinnedSection
│   └── PinnedItemCard[] (removable)
├── LatestSection
│   ├── SelectionPreview
│   └── ResultCard[]
│       ├── TypeBadge
│       ├── Summary
│       ├── ExpandButton
│       └── PinButton
├── HistorySection
│   └── HistoryItem[]
│       ├── Timestamp
│       ├── TextPreview
│       └── MatchCount
└── FooterBar
    ├── SettingsButton
    └── StatusIndicator
```

## Technical Specifications

### Window Management

```python
class SidebarWindow:
    def __init__(self):
        self.root = tk.Tk()
        self.width_collapsed = 40
        self.width_expanded = 320
        self.current_width = self.width_collapsed
        self.docked_side = 'right'  # 'left' or 'right'
        self.always_on_top = True

    def dock_to_edge(self):
        """Position window at screen edge"""
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()

        if self.docked_side == 'right':
            x = screen_width - self.current_width
        else:
            x = 0

        self.root.geometry(f'{self.current_width}x{screen_height}+{x}+0')

    def expand(self):
        """Animate expansion"""
        self.animate_width(self.width_collapsed, self.width_expanded)

    def collapse(self):
        """Animate collapse"""
        self.animate_width(self.width_expanded, self.width_collapsed)
```

### State Management

```python
class SidebarState:
    is_expanded: bool = False
    pinned_items: List[PinnedItem] = []
    latest_analysis: Optional[AnalysisResult] = None
    history: List[HistoryEntry] = []
    auto_collapse_enabled: bool = True
    auto_collapse_delay: int = 10  # seconds
```

### Pinned Items Persistence

```python
@dataclass
class PinnedItem:
    id: str
    type: str  # 'contact', 'project', 'snippet', 'abbreviation'
    data: dict
    pinned_at: datetime
    custom_label: Optional[str] = None

# Save to JSON file
def save_pinned_items(items: List[PinnedItem]):
    with open('~/.context-tool/pinned.json', 'w') as f:
        json.dump([asdict(item) for item in items], f)

# Load from JSON file
def load_pinned_items() -> List[PinnedItem]:
    try:
        with open('~/.context-tool/pinned.json', 'r') as f:
            data = json.load(f)
            return [PinnedItem(**item) for item in data]
    except FileNotFoundError:
        return []
```

## Configuration Options

```python
class SidebarConfig:
    # Position
    docked_side: str = 'right'  # 'left' or 'right'
    width_collapsed: int = 40
    width_expanded: int = 320
    min_width: int = 250
    max_width: int = 500

    # Behavior
    auto_expand: bool = True
    auto_collapse: bool = True
    auto_collapse_delay: int = 10
    always_on_top: bool = True
    start_expanded: bool = False

    # Appearance
    opacity_active: float = 1.0
    opacity_inactive: float = 0.85
    opacity_collapsed: float = 0.7
    theme: str = 'light'  # 'light' or 'dark'

    # Content
    max_history_items: int = 20
    max_pinned_items: int = 10
    show_timestamps: bool = True
    compact_mode: bool = False
```

## Pinned Items Features

### Visual Indicators
- Yellow left border (4px)
- Pin icon in top-right
- Draggable to reorder
- Click X to unpin

### Pinned Item Actions
```
┌─────────────────────────┐
│ 👤 John Doe        [📌][×]│
├─────────────────────────┤
│ ✉ john@example.com      │
│ 📋 Senior Engineer      │
│                         │
│ [🔍 Search] [✏ Edit]    │
└─────────────────────────┘
```

### Context Menu (Right-click)
- Rename label
- Copy to clipboard
- Open in detail view
- Export to file
- Unpin

## Keyboard Shortcuts

| Shortcut | Action |
|----------|--------|
| Ctrl+Alt+S | Toggle sidebar |
| Ctrl+[ | Collapse sidebar |
| Ctrl+] | Expand sidebar |
| Ctrl+P | Pin current item |
| Ctrl+H | Jump to history |
| Alt+↑/↓ | Navigate items |
| Enter | Expand selected |
| Delete | Unpin selected |

## Multi-Monitor Support

```python
def get_active_monitor():
    """Detect which monitor is active"""
    cursor_pos = get_cursor_position()
    for monitor in get_monitors():
        if monitor.contains(cursor_pos):
            return monitor
    return primary_monitor

def dock_to_active_monitor():
    """Dock sidebar to the monitor where cursor is"""
    monitor = get_active_monitor()
    # Position sidebar on that monitor's edge
```

## Implementation Phases

### Phase 1: Basic Sidebar (MVP)
- [x] Dockable window at screen edge
- [x] Expand/collapse animation
- [x] Show latest analysis results
- [x] Always-on-top mode

### Phase 2: Pinning
- [ ] Pin button on items
- [ ] Pinned section at top
- [ ] Persist pinned items
- [ ] Unpin functionality

### Phase 3: History
- [ ] History section
- [ ] Store recent analyses
- [ ] Click to load past results
- [ ] Clear history option

### Phase 4: Auto Behavior
- [ ] Auto-expand on selection
- [ ] Auto-collapse after delay
- [ ] Smart opacity changes
- [ ] Hover expand preview

### Phase 5: Polish
- [ ] Draggable resize handle
- [ ] Context menus
- [ ] Keyboard shortcuts
- [ ] Multi-monitor support
- [ ] Dark theme
- [ ] Compact mode

## Responsive Behavior

### Small Screens (< 1366px width)
- Default to collapsed state
- Disable auto-expand
- Suggest using hotkey overlay instead

### Large Screens (> 1920px width)
- Wider default width (380px)
- Show more history items
- Enable compact mode option

### Multi-Monitor
- Detect active monitor
- Dock to monitor with cursor
- Remember per-monitor preferences

## Success Metrics

- **Glanceability**: Users can get info without switching focus
- **Persistence**: Pinned items remain useful across sessions
- **Performance**: Sidebar doesn't impact system performance
- **Unobtrusiveness**: Users don't feel it's in the way

## Challenges & Solutions

**Challenge 1**: Sidebar takes screen space from main work
- **Solution**: Make collapse very easy, auto-collapse option, configurable width

**Challenge 2**: Performance with always-on rendering
- **Solution**: Only render visible items, pause updates when collapsed

**Challenge 3**: Conflicts with other sidebars (IDE, browser devtools)
- **Solution**: Configurable docking side, toggle hotkey for quick hide

**Challenge 4**: Small laptop screens
- **Solution**: Detect screen size, suggest alternative prototypes

## Comparison to Web Demo

The web demo (app.js) already has an always-on interface. This prototype differs by:

| Feature | Web Demo | Always-On Sidebar |
|---------|----------|-------------------|
| Context | Browser | Desktop-wide |
| Positioning | Fixed in page | Screen edge |
| Collapse | No | Yes |
| Pinning | No | Yes |
| History | No | Yes |
| Screen Real Estate | Page-only | Global |

## User Testing Questions

1. Does the sidebar feel helpful or distracting?
2. How often do you use pinned items?
3. Is the auto-collapse feature useful or annoying?
4. Would you prefer left or right docking?
5. Is the expanded width appropriate for your screen?
6. Do you use the history feature?
