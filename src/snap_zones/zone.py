"""Zone data structures and management for SnapZones"""

import json
import os
from typing import List, Optional, Dict, Tuple
from dataclasses import dataclass, asdict


@dataclass
class Zone:
    """Represents a window snap zone"""

    x: int
    y: int
    width: int
    height: int
    name: str = ""
    color: str = "#3498db"  # Default blue color

    def __post_init__(self):
        """Validate zone dimensions"""
        if self.width <= 0 or self.height <= 0:
            raise ValueError(f"Zone dimensions must be positive: width={self.width}, height={self.height}")

    @property
    def x2(self) -> int:
        """Right edge of zone"""
        return self.x + self.width

    @property
    def y2(self) -> int:
        """Bottom edge of zone"""
        return self.y + self.height

    @property
    def center(self) -> Tuple[int, int]:
        """Center point of zone"""
        return (self.x + self.width // 2, self.y + self.height // 2)

    @property
    def area(self) -> int:
        """Area of zone in pixels"""
        return self.width * self.height

    def contains_point(self, x: int, y: int) -> bool:
        """Check if a point is inside this zone"""
        return (self.x <= x < self.x2 and
                self.y <= y < self.y2)

    def overlaps(self, other: 'Zone') -> bool:
        """Check if this zone overlaps with another zone"""
        return not (self.x2 <= other.x or other.x2 <= self.x or
                   self.y2 <= other.y or other.y2 <= self.y)

    def overlap_area(self, other: 'Zone') -> int:
        """Calculate the overlapping area with another zone"""
        if not self.overlaps(other):
            return 0

        overlap_x = max(0, min(self.x2, other.x2) - max(self.x, other.x))
        overlap_y = max(0, min(self.y2, other.y2) - max(self.y, other.y))
        return overlap_x * overlap_y

    def to_dict(self) -> Dict:
        """Convert zone to dictionary for JSON serialization"""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict) -> 'Zone':
        """Create zone from dictionary"""
        return cls(**data)

    def __repr__(self) -> str:
        name_str = f" '{self.name}'" if self.name else ""
        return f"Zone{name_str}({self.x}, {self.y}, {self.width}, {self.height})"


class ZoneManager:
    """Manages collections of zones with persistence"""

    def __init__(self, config_dir: Optional[str] = None):
        """
        Initialize zone manager

        Args:
            config_dir: Directory to store zone configurations.
                       Defaults to ~/.config/snapzones
        """
        if config_dir is None:
            config_dir = os.path.expanduser("~/.config/snapzones")

        self.config_dir = config_dir
        self.zones_file = os.path.join(config_dir, "zones.json")
        self.zones: List[Zone] = []

        # Create config directory if it doesn't exist
        os.makedirs(config_dir, exist_ok=True)

    def add_zone(self, zone: Zone) -> None:
        """Add a zone to the collection"""
        self.zones.append(zone)

    def remove_zone(self, index: int) -> bool:
        """
        Remove a zone by index

        Returns:
            True if zone was removed, False if index invalid
        """
        if 0 <= index < len(self.zones):
            self.zones.pop(index)
            return True
        return False

    def remove_zone_at_point(self, x: int, y: int) -> bool:
        """
        Remove the first zone containing the given point

        Returns:
            True if a zone was removed, False otherwise
        """
        for i, zone in enumerate(self.zones):
            if zone.contains_point(x, y):
                self.zones.pop(i)
                return True
        return False

    def get_zone_at_point(self, x: int, y: int) -> Optional[Zone]:
        """
        Get the zone at a specific point

        If multiple zones overlap at the point, returns the one with smallest area
        (most specific zone)
        """
        matching_zones = [z for z in self.zones if z.contains_point(x, y)]

        if not matching_zones:
            return None

        # Return zone with smallest area (most specific)
        return min(matching_zones, key=lambda z: z.area)

    def get_all_zones_at_point(self, x: int, y: int) -> List[Zone]:
        """Get all zones containing a specific point, sorted by area (smallest first)"""
        matching_zones = [z for z in self.zones if z.contains_point(x, y)]
        return sorted(matching_zones, key=lambda z: z.area)

    def get_overlapping_zones(self, zone: Zone) -> List[Zone]:
        """Get all zones that overlap with the given zone"""
        return [z for z in self.zones if z.overlaps(zone) and z is not zone]

    def clear_all(self) -> None:
        """Remove all zones"""
        self.zones.clear()

    def save_to_file(self, filepath: Optional[str] = None) -> bool:
        """
        Save zones to JSON file

        Args:
            filepath: Path to save to. If None, uses default zones.json

        Returns:
            True if successful, False otherwise
        """
        if filepath is None:
            filepath = self.zones_file

        try:
            data = {
                "version": "1.0",
                "zones": [zone.to_dict() for zone in self.zones]
            }

            with open(filepath, 'w') as f:
                json.dump(data, f, indent=2)

            return True

        except Exception as e:
            print(f"Error saving zones: {e}")
            return False

    def load_from_file(self, filepath: Optional[str] = None) -> bool:
        """
        Load zones from JSON file

        Args:
            filepath: Path to load from. If None, uses default zones.json

        Returns:
            True if successful, False otherwise
        """
        if filepath is None:
            filepath = self.zones_file

        if not os.path.exists(filepath):
            return False

        try:
            with open(filepath, 'r') as f:
                data = json.load(f)

            # Clear existing zones
            self.zones.clear()

            # Load zones from file
            for zone_data in data.get("zones", []):
                zone = Zone.from_dict(zone_data)
                self.zones.append(zone)

            return True

        except Exception as e:
            print(f"Error loading zones: {e}")
            return False

    def __len__(self) -> int:
        """Return number of zones"""
        return len(self.zones)

    def __iter__(self):
        """Iterate over zones"""
        return iter(self.zones)

    def __getitem__(self, index: int) -> Zone:
        """Get zone by index"""
        return self.zones[index]


def create_preset_layout(preset_name: str, screen_width: int, screen_height: int) -> List[Zone]:
    """
    Create a preset zone layout

    Args:
        preset_name: Name of preset ('halves', 'thirds', 'quarters', 'grid3x3')
        screen_width: Width of screen
        screen_height: Height of screen

    Returns:
        List of zones for the preset
    """
    zones = []

    if preset_name == "halves":
        # Two vertical halves
        zones.append(Zone(0, 0, screen_width // 2, screen_height, "Left Half", "#3498db"))
        zones.append(Zone(screen_width // 2, 0, screen_width // 2, screen_height, "Right Half", "#e74c3c"))

    elif preset_name == "thirds":
        # Three vertical thirds
        third_width = screen_width // 3
        zones.append(Zone(0, 0, third_width, screen_height, "Left Third", "#3498db"))
        zones.append(Zone(third_width, 0, third_width, screen_height, "Center Third", "#2ecc71"))
        zones.append(Zone(third_width * 2, 0, screen_width - (third_width * 2),
                         screen_height, "Right Third", "#e74c3c"))

    elif preset_name == "quarters":
        # Four quadrants
        half_w = screen_width // 2
        half_h = screen_height // 2
        zones.append(Zone(0, 0, half_w, half_h, "Top Left", "#3498db"))
        zones.append(Zone(half_w, 0, half_w, half_h, "Top Right", "#e74c3c"))
        zones.append(Zone(0, half_h, half_w, half_h, "Bottom Left", "#2ecc71"))
        zones.append(Zone(half_w, half_h, half_w, half_h, "Bottom Right", "#f39c12"))

    elif preset_name == "grid3x3":
        # 3x3 grid
        cell_w = screen_width // 3
        cell_h = screen_height // 3
        colors = ["#3498db", "#e74c3c", "#2ecc71", "#f39c12", "#9b59b6",
                 "#1abc9c", "#34495e", "#e67e22", "#95a5a6"]

        for row in range(3):
            for col in range(3):
                x = col * cell_w
                y = row * cell_h
                w = cell_w if col < 2 else screen_width - (cell_w * 2)
                h = cell_h if row < 2 else screen_height - (cell_h * 2)
                zones.append(Zone(x, y, w, h, f"Cell {row},{col}", colors[row * 3 + col]))

    else:
        raise ValueError(f"Unknown preset: {preset_name}")

    return zones


def main():
    """Command-line interface for testing zone operations"""
    import argparse

    parser = argparse.ArgumentParser(description='SnapZones Zone Manager')
    parser.add_argument('--create-preset', choices=['halves', 'thirds', 'quarters', 'grid3x3'],
                       help='Create a preset layout')
    parser.add_argument('--screen-width', type=int, default=1920, help='Screen width (default: 1920)')
    parser.add_argument('--screen-height', type=int, default=1080, help='Screen height (default: 1080)')
    parser.add_argument('--save', metavar='FILE', help='Save zones to file')
    parser.add_argument('--load', metavar='FILE', help='Load zones from file')
    parser.add_argument('--list', action='store_true', help='List all zones')
    parser.add_argument('--test-point', nargs=2, type=int, metavar=('X', 'Y'),
                       help='Test which zone contains point')

    args = parser.parse_args()

    zm = ZoneManager()

    # Load zones if specified
    if args.load:
        if zm.load_from_file(args.load):
            print(f"Loaded {len(zm)} zones from {args.load}")
        else:
            print(f"Failed to load zones from {args.load}")
            return

    # Create preset if specified
    if args.create_preset:
        zones = create_preset_layout(args.create_preset, args.screen_width, args.screen_height)
        for zone in zones:
            zm.add_zone(zone)
        print(f"Created {args.create_preset} layout with {len(zones)} zones")

    # List zones
    if args.list or args.create_preset:
        print("\nZones:")
        print("-" * 80)
        for i, zone in enumerate(zm):
            print(f"{i + 1}. {zone}")
        print(f"\nTotal: {len(zm)} zones")

    # Test point
    if args.test_point:
        x, y = args.test_point
        zone = zm.get_zone_at_point(x, y)
        if zone:
            print(f"\nPoint ({x}, {y}) is in: {zone}")
        else:
            print(f"\nPoint ({x}, {y}) is not in any zone")

        # Show all overlapping zones
        all_zones = zm.get_all_zones_at_point(x, y)
        if len(all_zones) > 1:
            print(f"All zones at point (smallest to largest):")
            for z in all_zones:
                print(f"  - {z} (area: {z.area})")

    # Save zones if specified
    if args.save:
        if zm.save_to_file(args.save):
            print(f"\nSaved {len(zm)} zones to {args.save}")
        else:
            print(f"\nFailed to save zones to {args.save}")


if __name__ == '__main__':
    main()
