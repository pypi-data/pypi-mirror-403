"""
TerraQT Client - Data Models and Types

Core data structures with full type safety and immutability where appropriate.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import TYPE_CHECKING, Iterator

if TYPE_CHECKING:
    import pandas as pd


# =============================================================================
# Variable Set Constants (Customizable)
# =============================================================================
# These constants define the built-in variable sets. Users can define their own
# by using any string as a group name, as long as the ModelConfig supports it.

WIND = "wind"
SOLAR = "solar"


@dataclass(frozen=True, slots=True)
class Location:
    """
    Represents a geographic location with coordinates and weight.

    Attributes:
        name: Unique identifier for the location.
        lon: Longitude coordinate (-180 to 180).
        lat: Latitude coordinate (-90 to 90).
        weight: Weight for aggregation calculations (default: 1.0).

    Example:
        >>> loc = Location(name="station_1", lon=106.5, lat=37.5, weight=0.6)
        >>> loc.to_dict()
        {'name': 'station_1', 'lon': 106.5, 'lat': 37.5, 'weight': 0.6}
    """

    name: str
    lon: float
    lat: float
    weight: float = 1.0

    def __post_init__(self) -> None:
        """Validate coordinates."""
        if not -180 <= self.lon <= 180:
            raise ValueError(f"Longitude must be between -180 and 180, got {self.lon}")
        if not -90 <= self.lat <= 90:
            raise ValueError(f"Latitude must be between -90 and 90, got {self.lat}")
        if self.weight < 0:
            raise ValueError(f"Weight must be non-negative, got {self.weight}")

    def to_dict(self) -> dict[str, str | float]:
        """Convert to dictionary representation."""
        return {
            "name": self.name,
            "lon": self.lon,
            "lat": self.lat,
            "weight": self.weight,
        }


@dataclass(frozen=True, slots=True)
class ModelConfig:
    """
    Configuration for a forecast model.

    Attributes:
        name: Model identifier (e.g., "gfs_surface").
        variable_groups: Mapping of group names to variable tuples.
        model_type: Type of model (default: "forecast").

    Example:
        >>> config = ModelConfig(
        ...     name="gfs_surface",
        ...     variable_groups={
        ...         "wind": ("ws100m",),
        ...         "solar": ("dswrf", "tcc"),
        ...     }
        ... )
        >>> config.get_variables("solar")
        ('dswrf', 'tcc')
    """

    name: str
    variable_groups: dict[str, tuple[str, ...]] = field(default_factory=dict)
    model_type: str = "forecast"

    def get_variables(self, group: str) -> tuple[str, ...]:
        """
        Get meteorological variables for a given group.

        Args:
            group: The variable group name (e.g., "wind", "solar").

        Returns:
            Tuple of variable names for the group.

        Raises:
            ValueError: If group is not found in variable_groups.
        """
        if group not in self.variable_groups:
            raise ValueError(
                f"Unknown variable group '{group}'. "
                f"Available: {list(self.variable_groups.keys())}"
            )
        return self.variable_groups[group]


@dataclass(slots=True)
class ForecastResult:
    """
    Result of a forecast query.

    Attributes:
        data: DataFrame containing forecast data.
        forecast_time: Timestamp of the forecast.
        model: Name of the forecast model.
        location: Name of the location.
    """

    data: pd.DataFrame
    forecast_time: datetime
    model: str
    location: str

    @property
    def is_empty(self) -> bool:
        """Check if the result contains no data."""
        return self.data.empty

    @property
    def shape(self) -> tuple[int, int]:
        """Get the shape of the data (rows, columns)."""
        return self.data.shape  # type: ignore[return-value]

    @property
    def variables(self) -> list[str]:
        """Get list of variables in the data."""
        return list(self.data.columns)


@dataclass
class ForecastCollection:
    """
    Collection of forecast results organized by model and location.

    Provides dictionary-like access to forecast data with helper methods
    for iteration and querying.

    Example:
        >>> collection = ForecastCollection()
        >>> collection.add("gfs_surface", "loc_1", df)
        >>> collection.get("gfs_surface", "loc_1")
        <DataFrame>
    """

    _results: dict[str, dict[str, pd.DataFrame]] = field(default_factory=dict)

    def add(self, model: str, location: str, data: pd.DataFrame) -> None:
        """
        Add a forecast result to the collection.

        Args:
            model: Model name.
            location: Location name.
            data: Forecast DataFrame.
        """
        if model not in self._results:
            self._results[model] = {}
        self._results[model][location] = data

    def get(
        self, model: str, location: str | None = None
    ) -> dict[str, pd.DataFrame] | pd.DataFrame | None:
        """
        Get forecast data by model and optionally location.

        Args:
            model: Model name.
            location: Optional location name.

        Returns:
            DataFrame for specific location, dict of all locations for model,
            or None if not found.
        """
        if model not in self._results:
            return None
        if location is None:
            return self._results[model]
        return self._results[model].get(location)

    def models(self) -> list[str]:
        """Get list of models in the collection."""
        return list(self._results.keys())

    def locations(self, model: str) -> list[str]:
        """Get list of locations for a model."""
        return list(self._results.get(model, {}).keys())

    def items(self) -> Iterator[tuple[str, dict[str, pd.DataFrame]]]:
        """Iterate over (model, location_data_dict) pairs."""
        yield from self._results.items()

    def __bool__(self) -> bool:
        """Check if collection has any data."""
        return bool(self._results)

    def __len__(self) -> int:
        """Get total number of model-location combinations."""
        return sum(len(locs) for locs in self._results.values())

    def __contains__(self, model: str) -> bool:
        """Check if model exists in collection."""
        return model in self._results
