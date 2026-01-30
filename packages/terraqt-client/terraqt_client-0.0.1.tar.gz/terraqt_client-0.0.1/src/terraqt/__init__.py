"""
TerraQT Client - Weather Forecast Data Client

A professional, type-safe client for querying TerraQT weather forecast data sources.

Example:
    >>> import asyncio
    >>> from terraqt import TerraQT, SOLAR
    >>>
    >>> async def main():
    ...     tqt = TerraQT(api_token="your_token")
    ...     tqt.locations.register("loc1", lon=106.5, lat=37.5, groups=SOLAR)
    ...     async with tqt.client() as client:
    ...         data = await tqt.query(client).models(["gfs_surface"]).locations_by_group(SOLAR).execute()
    ...
    >>> asyncio.run(main())
"""

from terraqt._version import __version__, __version_info__
from terraqt.client import (
    TerraQTAPIError,
    TerraQTClient,
    TerraQTClientError,
    TerraQTQueryBuilder,
    TerraQTTimeoutError,
)
from terraqt.config import DEFAULT_MODEL_CONFIGS, TerraQTConfig
from terraqt.locations import LocationRegistry, create_default_registry
from terraqt.models import (
    SOLAR,
    WIND,
    ForecastCollection,
    ForecastResult,
    Location,
    ModelConfig,
)
from terraqt.core import TerraQT

__all__ = [
    # Version
    "__version__",
    "__version_info__",
    # Main class
    "TerraQT",
    # Models
    "Location",
    "ModelConfig",
    "SOLAR",
    "WIND",
    "ForecastResult",
    "ForecastCollection",
    # Locations
    "LocationRegistry",
    "create_default_registry",
    # Client
    "TerraQTClient",
    "TerraQTQueryBuilder",
    "TerraQTClientError",
    "TerraQTAPIError",
    "TerraQTTimeoutError",
    # Config
    "TerraQTConfig",
    "DEFAULT_MODEL_CONFIGS",
]
