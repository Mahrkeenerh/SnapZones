# Border Detection & Content Geometry Analysis

## Issue Summary

When working with X11 windows, applications often include invisible borders (shadows, client-side decorations) that cause issues with window management and capture:

1. **Visual artifacts**: Transparent/invisible borders around windows in screenshots
2. **Inconsistent behavior**: Different applications (GTK vs non-GTK) show different border types
3. **Window snapping issues**: Windows don't snap flush to screen edges, leaving gaps
4. **UI highlighting issues**: Mouse collision detection triggers on invisible border areas instead of content areas

## Root Cause Analysis

### The Problem
There are two types of window borders/decorations in X11:

1. **Server-Side Decorations (SSD)**: Traditional window manager borders and title bars
   - Detected via `_NET_FRAME_EXTENTS` property
   - Set by the window manager
   - Typically visible (title bar, resize borders)

2. **Client-Side Decorations (CSD)**: GTK applications with invisible borders/shadows
   - Detected via `_GTK_FRAME_EXTENTS` property
   - Set by the application itself
   - Often **invisible** (drop shadows, resize areas)

The fundamental issue is that window geometry includes these invisible borders, causing:
- Window snapshots to capture transparent border areas
- Window snapping to leave visible gaps at screen edges
- Mouse hit detection to trigger on invisible areas

### Initial Broken Frame Detection
When we first investigated the issue, frame extents detection was **broken** and only detected partial borders:

**Terminal Window (Initial Broken State):**
- Position: (-8, 218)
- Frame extents: left=8, right=0, top=0, bottom=0 ❌ (only left border detected)
- Result: Only left border was excluded, other borders remained

**Nemo File Browser (Initial Broken State):**
- Position: (42, 145) 
- Frame extents: left=0, right=0, top=37, bottom=0 ❌ (only top border detected)
- Result: Only title bar was excluded, side borders remained

### Fixed Frame Detection
After improving the frame extents detection algorithm:

**Terminal Window (Fixed State):**
- Position: (-26, 211) - positioned to show actual border size
- Frame extents: left=26, right=26, top=26, bottom=26 ✅ (all borders detected)
- Content area: (0, 237) with size 1296x649 (properly excludes all decorations)

**Nemo File Browser (Fixed State):**
- Position: (0, 119)
- Frame extents: left=0, right=0, top=37, bottom=0 ✅ (correctly detects only top border)
- Content area: (0, 156) with size 1177x554 (properly excludes title bar)

### What We Fixed
1. **Improved estimation logic**: Enhanced fallback detection when `_NET_FRAME_EXTENTS` is unavailable
2. **Uniform border detection**: When negative coordinates indicate left border, assume uniform borders on all sides
3. **Better window positioning**: Anchored windows to screen edges to reveal true border sizes
4. **Enhanced debugging**: Added comprehensive logging to track frame extents detection

### The Complete Solution

The proper fix requires checking **both** `_GTK_FRAME_EXTENTS` and `_NET_FRAME_EXTENTS` properties, with appropriate fallbacks:

**Final Working Implementation:**
```python
def get_window_frame_extents(self, window) -> Tuple[int, int, int, int]:
    """
    Get frame extents (window decorations) for a window

    Returns:
        Tuple of (left, right, top, bottom) border sizes in pixels
    """
    # 1. First try _GTK_FRAME_EXTENTS for GTK apps with client-side decorations
    #    This property describes invisible borders/shadows around GTK windows
    try:
        gtk_frame_extents = self.display.get_atom('_GTK_FRAME_EXTENTS')
        gtk_extents_prop = window.get_full_property(gtk_frame_extents, X.AnyPropertyType)

        if gtk_extents_prop and len(gtk_extents_prop.value) >= 4:
            left, right, top, bottom = gtk_extents_prop.value[:4]
            return (left, right, top, bottom)  # ✅ GTK invisible borders detected
    except Exception:
        pass

    # 2. Try _NET_FRAME_EXTENTS property (standard window manager decorations)
    try:
        net_frame_extents = self.display.get_atom('_NET_FRAME_EXTENTS')
        extents_prop = window.get_full_property(net_frame_extents, X.AnyPropertyType)

        if extents_prop and len(extents_prop.value) >= 4:
            left, right, top, bottom = extents_prop.value[:4]
            return (left, right, top, bottom)  # ✅ Standard decorations detected
    except Exception:
        pass

    # 3. Fallback: estimate from window geometry
    try:
        geom = window.get_geometry()

        # If window has negative coordinates, it has borders
        left_border = max(0, -geom.x) if geom.x < 0 else 0
        top_border = max(0, -geom.y) if geom.y < 0 else 0

        # If left border detected, assume uniform borders (common pattern)
        if left_border > 0:
            return (left_border, left_border, left_border, left_border)

        # If only top border, it's likely a title bar
        if top_border > 0:
            return (0, 0, top_border, 0)
    except Exception:
        pass

    return (0, 0, 0, 0)  # No borders detected
```

**Key Insight:** `_GTK_FRAME_EXTENTS` must be checked **before** `_NET_FRAME_EXTENTS` because GTK apps often set only the GTK property, and the NET property may return (0,0,0,0).

## Solution Implemented

### 1. Frame Extents Detection (SnapZones Implementation)
Implemented `get_window_frame_extents()` method that:
- **First** checks `_GTK_FRAME_EXTENTS` for GTK apps with invisible borders
- **Then** tries `_NET_FRAME_EXTENTS` for standard window manager decorations
- **Falls back** to estimating borders from negative window coordinates
- Returns (left, right, top, bottom) border sizes in pixels

**Example Output:**
```
Terminal window (GTK with CSD):
  _GTK_FRAME_EXTENTS: left=26, right=26, top=23, bottom=29

Nemo file browser (Traditional decorations):
  _NET_FRAME_EXTENTS: left=0, right=0, top=37, bottom=0
```

### 2. Window Snapping with Border Compensation
Modified `move_resize_window()` to compensate for invisible borders:

```python
# Get frame extents (including invisible GTK borders/shadows)
left, right, top, bottom = self.get_window_frame_extents(window)

# Adjust position to compensate for invisible borders
# If window has invisible borders, position it so VISIBLE content
# starts at the target x,y (not the invisible border)
adjusted_x = x - left
adjusted_y = y - top
adjusted_width = width + left + right
adjusted_height = height + top + bottom

# Convert negative coordinates to unsigned 32-bit for X11 protocol
def to_uint32(val):
    if val < 0:
        return (1 << 32) + val
    return val

# Send _NET_MOVERESIZE_WINDOW event with adjusted coordinates
event = protocol.event.ClientMessage(
    window=window,
    client_type=net_moveresize_window,
    data=(32, [flags, to_uint32(adjusted_x), to_uint32(adjusted_y),
               adjusted_width, adjusted_height])
)
```

**Result:** Windows now snap flush to screen edges with no visible gaps, even with invisible GTK borders.

### 3. Content-Only Capture (CaptiX Implementation)
For screenshot applications, use frame extents to:
- Calculate content area within the window drawable
- Use `window.get_image(content_x, content_y, content_width, content_height)`
- Capture only the content portion, excluding invisible borders

## Implementation Details

### Why _GTK_FRAME_EXTENTS is Critical

GTK applications with client-side decorations (CSD) create **invisible borders** for:
- Drop shadows (visual effect)
- Resize areas (interaction areas beyond visible window)
- Rounded corner anti-aliasing

These borders are **not visible** but are included in the window's reported geometry, causing:
- Screenshot captures to include transparent areas
- Window snapping to leave visible gaps
- Mouse hit testing to trigger outside visible window

### X11 Protocol Considerations

When sending negative coordinates in `_NET_MOVERESIZE_WINDOW`:
```python
# X11 protocol uses unsigned 32-bit integers
# Negative values must be converted to two's complement representation
def to_uint32(val):
    if val < 0:
        return (1 << 32) + val  # Convert to unsigned representation
    return val

# Example: -26 → 4294967270 (0xFFFFFFE6)
```

This is necessary because:
- X11 ClientMessage events use 32-bit data fields
- Python-xlib validates values as unsigned
- Negative coordinates position windows off-screen edge to compensate for borders

## Results Achieved

### ✅ Fully Working (SnapZones v0.4.0)
1. **GTK invisible border detection**: `_GTK_FRAME_EXTENTS` successfully detected (26px left/right, 23px top, 29px bottom)
2. **Window snapping**: Windows snap flush to screen edges with **no visible gaps**
3. **Negative coordinate handling**: Proper unsigned 32-bit conversion for X11 protocol
4. **Mixed window support**: Works correctly for both GTK (CSD) and traditional (SSD) windows

### ⚠️ Remaining Tasks (CaptiX)
1. **Screenshot capture**: Apply same `_GTK_FRAME_EXTENTS` detection to CaptiX
2. **UI highlighting**: Update collision detection to use content geometry
3. **Preview mode**: Ensure preview shows actual content without borders

## Future Improvements

### 1. Update Window Detection at Source
Instead of post-processing, modify the core window detection to return content geometry by default:
```python
def get_window_at_position_content_aware(self, x: int, y: int) -> Optional[WindowInfo]:
    # Detect window normally
    window_info = self.get_window_at_position(x, y)
    # Return content geometry instead of full window geometry
    return self.get_window_content_geometry(window_info.window_id)
```

### 2. Improve Frame Extents Accuracy
- Test with different window managers (GNOME, KDE, i3, etc.)
- Handle edge cases where `_NET_FRAME_EXTENTS` is not available
- Fine-tune bottom border detection (potential off-by-one pixel issues)

### 3. UI Integration
- Update all mouse collision detection to use content geometry
- Ensure preview mode shows actual captured content
- Update selection rectangle to match content boundaries

## Key Technical Insights

1. **Two types of borders**: GTK apps use `_GTK_FRAME_EXTENTS` (invisible), traditional apps use `_NET_FRAME_EXTENTS` (visible)
2. **Order matters**: Always check `_GTK_FRAME_EXTENTS` first, as GTK apps may not set `_NET_FRAME_EXTENTS`
3. **Invisible borders are real**: GTK borders are transparent but consume geometry - must be compensated
4. **Negative positioning works**: Windows can be positioned off-screen edge to align visible content to screen coordinates
5. **Protocol requires unsigned**: X11 uses unsigned 32-bit integers, negative values need two's complement conversion

## Testing Commands

```bash
# SnapZones: Test window snapping with border compensation
python src/snap_zones/snapper.py --snap-active quarters

# SnapZones: Debug frame extents detection
python -c "
from snap_zones.window_manager import WindowManager
wm = WindowManager()
active = wm.get_active_window()
window = wm.display.create_resource_object('window', active.window_id)
frame = wm.get_window_frame_extents(window)
print(f'Frame extents: left={frame[0]}, right={frame[1]}, top={frame[2]}, bottom={frame[3]}')
"

# CaptiX: Examine window structure
python main.py --window-children 200,800

# CaptiX: Test content-only capture (TODO: implement _GTK_FRAME_EXTENTS)
python main.py --screenshot --window-pure-at 200,800
```

## Summary

The complete fix for invisible GTK borders requires:
1. Detecting `_GTK_FRAME_EXTENTS` property (checked first)
2. Falling back to `_NET_FRAME_EXTENTS` for traditional decorations
3. Compensating geometry by subtracting borders from position and adding to size
4. Converting negative coordinates to unsigned 32-bit for X11 protocol

**Status:** ✅ Fully implemented and tested in SnapZones v0.4.0