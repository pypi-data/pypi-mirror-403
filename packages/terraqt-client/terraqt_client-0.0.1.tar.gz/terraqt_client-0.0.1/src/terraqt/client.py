"""
TerraQT Client - API Client

Async HTTP client with retry logic, rate limiting, and comprehensive error handling.
"""

from __future__ import annotations

import asyncio
import logging
from datetime import datetime
from typing import TYPE_CHECKING, Any

import aiohttp
import pandas as pd

from terraqt.models import ForecastCollection, ForecastResult, Location

if TYPE_CHECKING:
    from terraqt.config import TerraQTConfig
    from terraqt.locations import LocationRegistry
    from terraqt.models import ModelConfig


logger = logging.getLogger(__name__)


class TerraQTClientError(Exception):
    """Base exception for TerraQT client errors."""

    pass


class TerraQTAPIError(TerraQTClientError):
    """Exception for API-related errors."""

    def __init__(self, message: str, status_code: int | None = None) -> None:
        self.status_code = status_code
        super().__init__(message)


class TerraQTTimeoutError(TerraQTClientError):
    """Exception for timeout errors."""

    pass


class TerraQTClient:
    """
    Async client for TerraQT weather forecast API.

    Features:
    - Connection pooling with configurable concurrency
    - Automatic retry with exponential backoff
    - Comprehensive error handling
    - Context manager support

    Example:
        >>> async with TerraQTClient(api_token="your_token") as client:
        ...     df, time = await client.fetch_forecast(
        ...         model="gfs_surface",
        ...         lon=106.5,
        ...         lat=37.5,
        ...         variables=["ws100m", "tcc"]
        ...     )
    """

    DEFAULT_BASE_URL = "https://api-pro-openet.terraqt.com/v1"
    DEFAULT_TIMEOUT = aiohttp.ClientTimeout(total=120, connect=10, sock_read=60)
    DEFAULT_MAX_CONCURRENCY = 10

    def __init__(
        self,
        api_token: str,
        base_url: str = DEFAULT_BASE_URL,
        timeout: aiohttp.ClientTimeout | None = None,
        max_concurrency: int = DEFAULT_MAX_CONCURRENCY,
        retry_attempts: int = 3,
        retry_backoff: float = 1.0,
    ) -> None:
        """
        Initialize the TerraQT client.

        Args:
            api_token: Authentication token for the API.
            base_url: Base URL for the API.
            timeout: Custom timeout configuration.
            max_concurrency: Maximum concurrent requests.
            retry_attempts: Number of retry attempts on failure.
            retry_backoff: Base backoff time for retries.
        """
        self._api_token = api_token
        self._base_url = base_url.rstrip("/")
        self._timeout = timeout or self.DEFAULT_TIMEOUT
        self._max_concurrency = max_concurrency
        self._retry_attempts = retry_attempts
        self._retry_backoff = retry_backoff
        self._semaphore: asyncio.Semaphore | None = None
        self._session: aiohttp.ClientSession | None = None

    @classmethod
    def from_config(cls, config: TerraQTConfig) -> TerraQTClient:
        """
        Create client from configuration object.

        Args:
            config: TerraQTConfig instance.

        Returns:
            Configured TerraQTClient.
        """
        timeout = aiohttp.ClientTimeout(
            total=config.timeout_total,
            connect=config.timeout_connect,
            sock_read=config.timeout_read,
        )
        return cls(
            api_token=config.api_token,
            base_url=config.api_base_url,
            timeout=timeout,
            max_concurrency=config.max_concurrency,
            retry_attempts=config.retry_attempts,
            retry_backoff=config.retry_backoff,
        )

    async def __aenter__(self) -> TerraQTClient:
        """Enter async context manager."""
        self._session = aiohttp.ClientSession()
        self._semaphore = asyncio.Semaphore(self._max_concurrency)
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: object,
    ) -> None:
        """Exit async context manager."""
        if self._session:
            await self._session.close()
            self._session = None
        self._semaphore = None

    def _get_headers(self) -> dict[str, str]:
        """Get request headers with authentication."""
        return {
            "Content-Type": "application/json",
            "token": self._api_token,
        }

    async def _ensure_session(self) -> aiohttp.ClientSession:
        """Ensure a session exists, creating one if necessary."""
        if self._session is None:
            self._session = aiohttp.ClientSession()
        if self._semaphore is None:
            self._semaphore = asyncio.Semaphore(self._max_concurrency)
        return self._session

    async def _request_with_retry(
        self,
        method: str,
        url: str,
        **kwargs: object,
    ) -> dict[str, object]:
        """
        Make HTTP request with retry logic.

        Args:
            method: HTTP method.
            url: Request URL.
            **kwargs: Additional request arguments.

        Returns:
            JSON response data.

        Raises:
            TerraQTAPIError: On API errors after retries.
            TerraQTTimeoutError: On timeout after retries.
        """
        session = await self._ensure_session()
        last_exception: Exception | None = None

        for attempt in range(self._retry_attempts):
            try:
                async with self._semaphore:  # type: ignore[union-attr]
                    async with session.request(
                        method,
                        url,
                        headers=self._get_headers(),
                        timeout=self._timeout,
                        **kwargs,
                    ) as response:
                        response.raise_for_status()
                        return await response.json()  # type: ignore[no-any-return]

            except aiohttp.ClientResponseError as e:
                last_exception = TerraQTAPIError(f"API error: {e.message}", status_code=e.status)
                # Don't retry on 4xx errors (client errors)
                if 400 <= e.status < 500:
                    raise last_exception

            except aiohttp.ClientConnectionError as e:
                last_exception = TerraQTAPIError(f"Connection error: {e}")

            except asyncio.TimeoutError:
                last_exception = TerraQTTimeoutError(f"Request timed out: {url}")

            # Exponential backoff
            if attempt < self._retry_attempts - 1:
                backoff = self._retry_backoff * (2**attempt)
                logger.warning(f"Request failed, retrying in {backoff}s (attempt {attempt + 1})")
                await asyncio.sleep(backoff)

        raise last_exception or TerraQTClientError("Unknown error")

    async def fetch_forecast(
        self,
        model: str,
        lon: float | list[float],
        lat: float | list[float],
        variables: list[str] | tuple[str, ...],
    ) -> tuple[pd.DataFrame, datetime]:
        """
        Fetch forecast data for specific coordinates.

        Args:
            model: Name of the forecast model.
            lon: Longitude (single value or list).
            lat: Latitude (single value or list).
            variables: List of meteorological variables to fetch.

        Returns:
            Tuple of (DataFrame with forecast data, forecast timestamp).

        Raises:
            TerraQTAPIError: On API errors.
            TerraQTTimeoutError: On timeout.
        """
        url = f"{self._base_url}/{model}/point"
        payload = {"lon": lon, "lat": lat, "mete_vars": list(variables)}

        logger.info(f"Fetching TerraQT: model={model} lon={lon} lat={lat}")

        resp_json = await self._request_with_retry("POST", url, json=payload)

        data: dict[str, Any] | None = resp_json.get("data")
        if data is None:
            raise TerraQTAPIError(f"API returned null data for model={model}")

        inner_data: list[dict[str, Any]] | None = data.get("data")
        if not inner_data or len(inner_data) == 0:
            raise TerraQTAPIError(f"API returned empty data for model={model}")

        values = inner_data[0].get("values")
        timestamp = data.get("timestamp")

        df = pd.DataFrame(values, index=timestamp)
        df.columns = pd.Index(data.get("mete_var", []))
        time_fcst = pd.to_datetime(data["time_fcst"])

        logger.debug(f"Successfully fetched {model} data: {df.shape}")
        return df, time_fcst

    async def fetch_forecast_for_location(
        self,
        model: str,
        location: Location,
        variables: list[str] | tuple[str, ...],
    ) -> ForecastResult:
        """
        Fetch forecast data for a Location object.

        Args:
            model: Name of the forecast model.
            location: Location object with coordinates.
            variables: List of meteorological variables.

        Returns:
            ForecastResult with data and metadata.
        """
        df, time_fcst = await self.fetch_forecast(
            model=model,
            lon=location.lon,
            lat=location.lat,
            variables=variables,
        )
        return ForecastResult(
            data=df,
            forecast_time=time_fcst,
            model=model,
            location=location.name,
        )

    async def fetch_multi_location(
        self,
        models: list[str],
        locations: list[Location],
        variables: list[str] | tuple[str, ...],
        continue_on_error: bool = True,
    ) -> ForecastCollection:
        """
        Fetch forecast data for multiple models and locations concurrently.

        Args:
            models: List of model names.
            locations: List of Location objects.
            variables: List of meteorological variables.
            continue_on_error: If True, continue on individual failures.

        Returns:
            ForecastCollection with all successful results.
        """
        collection = ForecastCollection()
        tasks: list[asyncio.Task[tuple[pd.DataFrame, datetime]]] = []
        task_keys: list[tuple[str, str]] = []

        for model in models:
            for location in locations:
                task = asyncio.create_task(
                    self.fetch_forecast(
                        model=model,
                        lon=location.lon,
                        lat=location.lat,
                        variables=variables,
                    )
                )
                tasks.append(task)
                task_keys.append((model, location.name))

        results = await asyncio.gather(*tasks, return_exceptions=True)

        for (model, loc_name), result in zip(task_keys, results, strict=True):
            if isinstance(result, BaseException):
                logger.error(f"Error: model={model} location={loc_name} - {result}")
                if not continue_on_error:
                    raise result  # type: ignore[misc]
                continue

            df, _ = result
            collection.add(model, loc_name, df)
            logger.info(f"Success: model={model} location={loc_name} shape={df.shape}")

        return collection


class TerraQTQueryBuilder:
    """
    Fluent builder for constructing TerraQT queries.

    Example:
        >>> result = await (
        ...     TerraQTQueryBuilder(client, registry, model_configs)
        ...     .models(["gfs_surface", "aifs_surface"])
        ...     .locations_by_group(SOLAR)
        ...     .execute()
        ... )
    """

    def __init__(
        self,
        client: TerraQTClient,
        location_registry: LocationRegistry,
        model_configs: dict[str, ModelConfig],
    ) -> None:
        """
        Initialize the query builder.

        Args:
            client: TerraQT API client.
            location_registry: Location registry.
            model_configs: Available model configurations.
        """
        self._client = client
        self._registry = location_registry
        self._model_configs = model_configs
        self._models: list[str] = []
        self._locations: list[str] = []
        self._variable_group: str | None = None
        self._variables: list[str] | tuple[str, ...] | None = None

    def models(self, model_names: list[str]) -> TerraQTQueryBuilder:
        """Set models to query."""
        self._models = model_names
        return self

    def locations(self, location_names: list[str]) -> TerraQTQueryBuilder:
        """Set specific locations to query."""
        self._locations = location_names
        return self

    def locations_by_group(self, group: str) -> TerraQTQueryBuilder:
        """
        Use all registered locations of a given group.

        This also sets the variable_group to match, so the correct variables
        are fetched from the model config.

        Args:
            group: The group name to use.

        Returns:
            Self for method chaining.
        """
        self._locations = self._registry.get_locations(group)
        self._variable_group = group
        return self

    def variable_group(self, name: str) -> TerraQTQueryBuilder:
        """Set the variable group (determines which variables to fetch from model config)."""
        self._variable_group = name
        return self

    def variables(self, vars: list[str] | tuple[str, ...]) -> TerraQTQueryBuilder:
        """
        Set raw variables to fetch directly.

        This overrides variable_group - if both are specified, raw variables take precedence.

        Args:
            vars: List of variable names to fetch (e.g., ['ws100m', 'tcc']).

        Returns:
            Self for method chaining.
        """
        self._variables = vars
        return self

    async def execute(self) -> ForecastCollection:
        """
        Execute the query and return results.

        Returns:
            ForecastCollection with query results.

        Raises:
            ValueError: If query is not fully configured.
        """
        if not self._models:
            raise ValueError("No models specified")
        if not self._locations:
            raise ValueError("No locations specified")
        if not self._variables and not self._variable_group:
            raise ValueError("No variables or variable set specified")

        collection = ForecastCollection()
        tasks: list[asyncio.Task[tuple[pd.DataFrame, datetime]]] = []
        task_keys: list[tuple[str, str]] = []

        for model_name in self._models:
            # Use raw variables if specified, otherwise get from model config
            if self._variables:
                variables = self._variables
            else:
                model_config = self._model_configs.get(model_name)
                if not model_config:
                    logger.warning(f"Model config not found: {model_name}")
                    continue
                variables = model_config.get_variables(self._variable_group)  # type: ignore[arg-type]

            for loc_name in self._locations:
                location = self._registry.get(loc_name)
                if not location:
                    logger.warning(f"Location not found: {loc_name}")
                    continue

                task = asyncio.create_task(
                    self._client.fetch_forecast(
                        model=model_name,
                        lon=location.lon,
                        lat=location.lat,
                        variables=variables,
                    )
                )
                tasks.append(task)
                task_keys.append((model_name, loc_name))

        results = await asyncio.gather(*tasks, return_exceptions=True)

        for (model, loc_name), result in zip(task_keys, results, strict=True):
            if isinstance(result, BaseException):
                logger.error(f"Error: model={model} location={loc_name} - {result}")
                continue

            df, _ = result
            collection.add(model, loc_name, df)
            logger.info(f"Success: model={model} location={loc_name} shape={df.shape}")

        return collection
