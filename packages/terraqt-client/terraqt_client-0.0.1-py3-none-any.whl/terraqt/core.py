"""
TerraQT Client - Core Module

Unified interface for all client functionality.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from terraqt.client import TerraQTClient, TerraQTQueryBuilder
from terraqt.config import TerraQTConfig
from terraqt.locations import LocationRegistry

if TYPE_CHECKING:
    pass


class TerraQT:
    """
    Main entry point for the TerraQT Client.

    Provides a unified interface for all client functionality with
    convenient factory methods for creating components.

    Example:
        >>> from terraqt import TerraQT, SOLAR
        >>> tqt = TerraQT(api_token="your_token")
        >>>
        >>> # Configure locations
        >>> tqt.locations.register("s1", lon=106.5, lat=37.5, groups=SOLAR)
        >>>
        >>> # Fetch data
        >>> async with tqt.client() as client:
        ...     data = await tqt.query(client).models(["gfs_surface"]).locations_by_group(SOLAR).execute()
    """

    def __init__(
        self,
        api_token: str | None = None,
        config: TerraQTConfig | None = None,
        **kwargs: object,
    ) -> None:
        """
        Initialize the TerraQT Client.

        Args:
            api_token: API authentication token.
            config: Optional pre-built configuration.
            **kwargs: Additional configuration options passed to TerraQTConfig.

        Raises:
            ValueError: If neither api_token nor config is provided.
        """
        if config:
            self._config = config
        elif api_token:
            self._config = TerraQTConfig(api_token=api_token, **kwargs)  # type: ignore[arg-type]
        else:
            raise ValueError("Either api_token or config must be provided")

        self._locations = LocationRegistry()

    @classmethod
    def from_env(cls, prefix: str = "TERRAQT_") -> TerraQT:
        """
        Create TerraQT instance from environment variables.

        Args:
            prefix: Environment variable prefix.

        Returns:
            Configured TerraQT instance.
        """
        config = TerraQTConfig.from_env(prefix)
        return cls(config=config)

    @property
    def config(self) -> TerraQTConfig:
        """Get the client configuration."""
        return self._config

    @property
    def locations(self) -> LocationRegistry:
        """Get the location registry."""
        return self._locations

    def client(self) -> TerraQTClient:
        """
        Create a new TerraQT API client.

        Returns:
            TerraQTClient instance (use as async context manager).
        """
        return TerraQTClient.from_config(self._config)

    def query(self, client: TerraQTClient) -> TerraQTQueryBuilder:
        """
        Create a query builder for fetching data.

        Args:
            client: Active TerraQTClient instance.

        Returns:
            TerraQTQueryBuilder for constructing queries.
        """
        return TerraQTQueryBuilder(
            client=client,
            location_registry=self._locations,
            model_configs=self._config.model_configs,
        )
