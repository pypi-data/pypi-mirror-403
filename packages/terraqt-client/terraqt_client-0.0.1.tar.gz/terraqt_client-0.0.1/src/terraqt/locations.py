"""
TerraQT Client - Location Configuration Management

Type-safe location registry with CSV loading and categorization support.
"""

from __future__ import annotations

from collections.abc import Sequence
from pathlib import Path
from typing import TYPE_CHECKING, Iterator

import pandas as pd

from terraqt.models import SOLAR, WIND, Location

if TYPE_CHECKING:
    pass


class LocationRegistry:
    """
    Registry for managing location configurations.

    Thread-safe registry supporting loading from CSV files, manual registration,
    and location categorization by groups. Each location can belong to multiple groups.

    Example:
        >>> from terraqt.models import SOLAR, WIND
        >>> registry = LocationRegistry()
        >>> registry.register("station_1", lon=106.5, lat=37.5, weight=0.6, groups=SOLAR)
        >>> registry.register("station_2", lon=107.0, lat=38.0, groups=[SOLAR, WIND])  # multiple groups
        >>> registry.get_locations(SOLAR)
        ['station_1', 'station_2']
    """

    __slots__ = ("_locations", "_location_groups")

    def __init__(self) -> None:
        """Initialize an empty location registry."""
        self._locations: dict[str, Location] = {}
        self._location_groups: dict[str, list[str]] = {}

    def register(
        self,
        name: str,
        lon: float,
        lat: float,
        weight: float = 1.0,
        groups: str | Sequence[str] | None = None,
    ) -> LocationRegistry:
        """
        Register a single location.

        Args:
            name: Unique identifier for the location.
            lon: Longitude coordinate.
            lat: Latitude coordinate.
            weight: Weight for averaging calculations.
            groups: Optional group(s) for categorization. Can be a single group
                    string or a sequence of group strings.

        Returns:
            Self for method chaining.

        Raises:
            ValueError: If location with same name already exists.
        """
        if name in self._locations:
            raise ValueError(f"Location '{name}' already registered")

        self._locations[name] = Location(name=name, lon=lon, lat=lat, weight=weight)

        if groups is not None:
            # Normalize to list
            group_list = [groups] if isinstance(groups, str) else list(groups)
            for group in group_list:
                if group not in self._location_groups:
                    self._location_groups[group] = []
                self._location_groups[group].append(name)

        return self

    def register_batch(
        self,
        locations: list[dict[str, float | str]],
        groups: str | Sequence[str] | None = None,
    ) -> LocationRegistry:
        """
        Register multiple locations at once.

        Args:
            locations: List of location dictionaries with keys: name, lon, lat, weight (optional).
            groups: Group(s) to assign to all locations.

        Returns:
            Self for method chaining.
        """
        for loc in locations:
            self.register(
                name=str(loc["name"]),
                lon=float(loc["lon"]),
                lat=float(loc["lat"]),
                weight=float(loc.get("weight", 1.0)),
                groups=groups,
            )
        return self

    def load_from_csv(
        self,
        filepath: str | Path,
        prefix: str = "",
        groups: str | Sequence[str] | None = None,
        name_column: str | None = None,
    ) -> LocationRegistry:
        """
        Load locations from a CSV file.

        Expected CSV columns: lon, lat, weight (optional), name (optional).

        Args:
            filepath: Path to CSV file.
            prefix: Prefix for generated location names (used if no name column).
            groups: Group(s) to assign to all loaded locations.
            name_column: Column to use for location names (auto-detected if None).

        Returns:
            Self for method chaining.
        """
        df = pd.read_csv(filepath)

        for idx, row in df.iterrows():
            # Determine name
            if name_column and name_column in df.columns:
                name = str(row[name_column])
            elif "name" in df.columns:
                name = str(row["name"])
            else:
                name = f"{prefix}{idx}"

            weight = float(row.get("weight", 1.0)) if "weight" in df.columns else 1.0

            self.register(
                name=name,
                lon=float(row["lon"]),
                lat=float(row["lat"]),
                weight=weight,
                groups=groups,
            )

        return self

    def unregister(self, name: str) -> bool:
        """
        Remove a location from the registry.

        Args:
            name: Location name to remove.

        Returns:
            True if location was removed, False if not found.
        """
        if name not in self._locations:
            return False

        del self._locations[name]

        for group in self._location_groups.values():
            if name in group:
                group.remove(name)

        return True

    def get(self, name: str) -> Location | None:
        """Get a location by name, returns None if not found."""
        return self._locations.get(name)

    def __getitem__(self, name: str) -> Location:
        """Get a location by name, raises KeyError if not found."""
        if name not in self._locations:
            raise KeyError(f"Location '{name}' not found in registry")
        return self._locations[name]

    def __contains__(self, name: str) -> bool:
        """Check if location exists in registry."""
        return name in self._locations

    def __iter__(self) -> Iterator[str]:
        """Iterate over location names."""
        return iter(self._locations)

    def __len__(self) -> int:
        """Get number of registered locations."""
        return len(self._locations)

    def get_locations(self, group: str) -> list[str]:
        """
        Get list of location names for a given group.

        Args:
            group: The group name to filter by.

        Returns:
            List of location names in the given group.
        """
        return self._location_groups.get(group, []).copy()

    def get_groups(self) -> list[str]:
        """
        Get list of all registered group names.

        Returns:
            List of group names that have locations registered.
        """
        return list(self._location_groups.keys())

    def all_locations(self) -> list[str]:
        """Get list of all location names."""
        return list(self._locations.keys())

    def get_coordinates(self, name: str) -> tuple[float, float]:
        """
        Get (lon, lat) tuple for a location.

        Args:
            name: Location name.

        Returns:
            Tuple of (longitude, latitude).
        """
        loc = self[name]
        return (loc.lon, loc.lat)

    def get_weight(self, name: str) -> float:
        """
        Get weight for a location.

        Args:
            name: Location name.

        Returns:
            Location weight.
        """
        return self[name].weight

    def get_location_objects(self, group: str) -> list[Location]:
        """
        Get all Location objects for a given group.

        Args:
            group: The group name to filter by.

        Returns:
            List of Location objects.
        """
        names = self._location_groups.get(group, [])
        return [self._locations[name] for name in names]

    def to_dict(self) -> dict[str, dict[str, str | float]]:
        """Export all locations as a dictionary."""
        return {name: loc.to_dict() for name, loc in self._locations.items()}

    def clear(self) -> None:
        """Remove all registered locations."""
        self._locations.clear()
        self._location_groups.clear()


def create_default_registry(data_dir: str | Path = "data") -> LocationRegistry:
    """
    Create a location registry with default solar and wind locations.

    Args:
        data_dir: Directory containing location CSV files.

    Returns:
        Configured LocationRegistry instance.
    """
    data_path = Path(data_dir)
    registry = LocationRegistry()

    # Load solar locations
    solar_csv = data_path / "agg_solar_location.csv"
    if solar_csv.exists():
        registry.load_from_csv(solar_csv, prefix="s", groups=SOLAR)

    # Load wind locations
    wind_csv = data_path / "agg_wind_location.csv"
    if wind_csv.exists():
        registry.load_from_csv(wind_csv, prefix="w", groups=WIND)

    return registry
