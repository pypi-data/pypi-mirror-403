"""
TerraQT Client Tests

Comprehensive unit tests with mock data for all client components.
"""

import tempfile
from datetime import datetime
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import numpy as np
import pandas as pd
import pytest

from terraqt import (
    DEFAULT_MODEL_CONFIGS,
    SOLAR,
    WIND,
    ForecastCollection,
    ForecastResult,
    Location,
    LocationRegistry,
    ModelConfig,
    TerraQT,
    TerraQTClient,
    TerraQTConfig,
    TerraQTQueryBuilder,
)


# =============================================================================
# Fixtures and Mock Data
# =============================================================================


@pytest.fixture
def sample_forecast_data() -> pd.DataFrame:
    """Sample forecast DataFrame."""
    timestamps = pd.date_range("2026-01-22 00:00", periods=24, freq="h")
    return pd.DataFrame(
        {
            "dswrf": np.random.uniform(0, 800, 24),
            "tcc": np.random.uniform(0, 100, 24),
        },
        index=timestamps.strftime("%Y-%m-%d %H:%M:%S").tolist(),
    )


@pytest.fixture
def sample_wind_data() -> pd.DataFrame:
    """Sample wind forecast DataFrame."""
    timestamps = pd.date_range("2026-01-22 00:00", periods=24, freq="h")
    return pd.DataFrame(
        {"ws100m": np.random.uniform(0, 20, 24)},
        index=timestamps.strftime("%Y-%m-%d %H:%M:%S").tolist(),
    )


@pytest.fixture
def mock_api_response(sample_forecast_data: pd.DataFrame) -> dict:
    """Mock TerraQT API response."""
    df = sample_forecast_data
    return {
        "code": 200,
        "data": {
            "data": [{"values": df.values.tolist()}],
            "timestamp": df.index.tolist(),
            "mete_var": df.columns.tolist(),
            "time_fcst": "2026-01-22T00:00:00",
        },
    }


@pytest.fixture
def location_registry() -> LocationRegistry:
    """Pre-configured location registry."""
    registry = LocationRegistry()
    registry.register("s_1", lon=106.5, lat=37.5, weight=0.6, groups=SOLAR)
    registry.register("s_2", lon=105.5, lat=36.5, weight=0.4, groups=SOLAR)
    registry.register("w_1", lon=107.0, lat=38.0, weight=0.7, groups=WIND)
    registry.register("w_2", lon=106.0, lat=37.0, weight=0.3, groups=WIND)
    return registry


@pytest.fixture
def model_configs() -> dict[str, ModelConfig]:
    """Model configurations for testing."""
    return DEFAULT_MODEL_CONFIGS.copy()


# =============================================================================
# Model Tests
# =============================================================================


class TestLocation:
    """Tests for Location dataclass."""

    def test_create_location(self) -> None:
        loc = Location(name="test", lon=106.5, lat=37.5, weight=0.5)
        assert loc.name == "test"
        assert loc.lon == 106.5
        assert loc.lat == 37.5
        assert loc.weight == 0.5

    def test_location_default_weight(self) -> None:
        loc = Location(name="test", lon=106.5, lat=37.5)
        assert loc.weight == 1.0

    def test_location_to_dict(self) -> None:
        loc = Location(name="test", lon=106.5, lat=37.5, weight=0.5)
        d = loc.to_dict()
        assert d == {"name": "test", "lon": 106.5, "lat": 37.5, "weight": 0.5}

    def test_location_is_frozen(self) -> None:
        loc = Location(name="test", lon=106.5, lat=37.5)
        with pytest.raises(AttributeError):
            loc.name = "new_name"  # type: ignore[misc]

    def test_location_validates_longitude(self) -> None:
        with pytest.raises(ValueError, match="Longitude must be between"):
            Location(name="test", lon=200.0, lat=37.5)

    def test_location_validates_latitude(self) -> None:
        with pytest.raises(ValueError, match="Latitude must be between"):
            Location(name="test", lon=106.5, lat=100.0)

    def test_location_validates_weight(self) -> None:
        with pytest.raises(ValueError, match="Weight must be non-negative"):
            Location(name="test", lon=106.5, lat=37.5, weight=-1.0)


class TestModelConfig:
    """Tests for ModelConfig dataclass."""

    def test_create_model_config(self) -> None:
        config = ModelConfig(
            name="test_model",
            variable_groups={
                WIND: ("ws100m",),
                SOLAR: ("dswrf", "tcc"),
            },
        )
        assert config.name == "test_model"
        assert config.variable_groups[WIND] == ("ws100m",)
        assert config.variable_groups[SOLAR] == ("dswrf", "tcc")
        assert config.model_type == "forecast"

    def test_get_variables_solar(self) -> None:
        config = ModelConfig(
            name="test",
            variable_groups={
                WIND: ("ws100m",),
                SOLAR: ("dswrf", "tcc"),
            },
        )
        assert config.get_variables(SOLAR) == ("dswrf", "tcc")

    def test_get_variables_wind(self) -> None:
        config = ModelConfig(
            name="test",
            variable_groups={
                WIND: ("ws100m",),
                SOLAR: ("dswrf", "tcc"),
            },
        )
        assert config.get_variables(WIND) == ("ws100m",)


class TestForecastResult:
    """Tests for ForecastResult dataclass."""

    def test_create_forecast_result(self, sample_forecast_data: pd.DataFrame) -> None:
        result = ForecastResult(
            data=sample_forecast_data,
            forecast_time=datetime(2026, 1, 22),
            model="gfs_surface",
            location="s_1",
        )
        assert result.model == "gfs_surface"
        assert result.location == "s_1"
        assert not result.is_empty
        assert result.shape == (24, 2)

    def test_empty_forecast_result(self) -> None:
        result = ForecastResult(
            data=pd.DataFrame(),
            forecast_time=datetime(2026, 1, 22),
            model="gfs_surface",
            location="s_1",
        )
        assert result.is_empty


class TestForecastCollection:
    """Tests for ForecastCollection."""

    def test_add_and_get(self, sample_forecast_data: pd.DataFrame) -> None:
        collection = ForecastCollection()
        collection.add("gfs_surface", "s_1", sample_forecast_data)

        result = collection.get("gfs_surface", "s_1")
        assert result is not None
        assert result.shape == sample_forecast_data.shape  # type: ignore[union-attr]

    def test_get_model_data(self, sample_forecast_data: pd.DataFrame) -> None:
        collection = ForecastCollection()
        collection.add("gfs_surface", "s_1", sample_forecast_data)
        collection.add("gfs_surface", "s_2", sample_forecast_data)

        model_data = collection.get("gfs_surface")
        assert isinstance(model_data, dict)
        assert "s_1" in model_data
        assert "s_2" in model_data

    def test_models_and_locations(self, sample_forecast_data: pd.DataFrame) -> None:
        collection = ForecastCollection()
        collection.add("gfs_surface", "s_1", sample_forecast_data)
        collection.add("aifs_surface", "s_1", sample_forecast_data)

        assert "gfs_surface" in collection.models()
        assert "aifs_surface" in collection.models()
        assert "s_1" in collection.locations("gfs_surface")

    def test_bool_empty(self) -> None:
        collection = ForecastCollection()
        assert not collection

    def test_bool_non_empty(self, sample_forecast_data: pd.DataFrame) -> None:
        collection = ForecastCollection()
        collection.add("gfs_surface", "s_1", sample_forecast_data)
        assert collection

    def test_contains(self, sample_forecast_data: pd.DataFrame) -> None:
        collection = ForecastCollection()
        collection.add("gfs_surface", "s_1", sample_forecast_data)
        assert "gfs_surface" in collection
        assert "aifs_surface" not in collection


# =============================================================================
# LocationRegistry Tests
# =============================================================================


class TestLocationRegistry:
    """Tests for LocationRegistry."""

    def test_register_location(self) -> None:
        registry = LocationRegistry()
        registry.register("test", lon=106.5, lat=37.5, weight=0.5)

        assert "test" in registry
        assert len(registry) == 1

    def test_register_with_type(self) -> None:
        registry = LocationRegistry()
        registry.register("s_1", lon=106.5, lat=37.5, groups=SOLAR)
        registry.register("w_1", lon=107.0, lat=38.0, groups=WIND)

        assert registry.get_locations(SOLAR) == ["s_1"]
        assert registry.get_locations(WIND) == ["w_1"]

    def test_register_duplicate_raises(self) -> None:
        registry = LocationRegistry()
        registry.register("test", lon=106.5, lat=37.5)

        with pytest.raises(ValueError, match="already registered"):
            registry.register("test", lon=107.0, lat=38.0)

    def test_get_location(self) -> None:
        registry = LocationRegistry()
        registry.register("test", lon=106.5, lat=37.5, weight=0.5)

        loc = registry["test"]
        assert loc.lon == 106.5
        assert loc.lat == 37.5

    def test_get_missing_location(self) -> None:
        registry = LocationRegistry()
        with pytest.raises(KeyError):
            _ = registry["missing"]

    def test_get_coordinates(self) -> None:
        registry = LocationRegistry()
        registry.register("test", lon=106.5, lat=37.5)

        lon, lat = registry.get_coordinates("test")
        assert lon == 106.5
        assert lat == 37.5

    def test_get_weight(self) -> None:
        registry = LocationRegistry()
        registry.register("test", lon=106.5, lat=37.5, weight=0.75)

        assert registry.get_weight("test") == 0.75

    def test_method_chaining(self) -> None:
        registry = (
            LocationRegistry()
            .register("s_1", lon=106.5, lat=37.5)
            .register("s_2", lon=105.5, lat=36.5)
        )
        assert len(registry) == 2

    def test_load_from_csv(self) -> None:
        # Create temporary CSV
        with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f:
            f.write("lon,lat,weight\n")
            f.write("106.5,37.5,0.6\n")
            f.write("105.5,36.5,0.4\n")
            csv_path = f.name

        try:
            registry = LocationRegistry()
            registry.load_from_csv(csv_path, prefix="loc", groups=SOLAR)

            assert len(registry) == 2
            assert registry.get_locations(SOLAR) == ["loc0", "loc1"]
        finally:
            Path(csv_path).unlink()

    def test_to_dict(self) -> None:
        registry = LocationRegistry()
        registry.register("test", lon=106.5, lat=37.5, weight=0.5)

        d = registry.to_dict()
        assert "test" in d
        assert d["test"]["lon"] == 106.5

    def test_unregister(self) -> None:
        registry = LocationRegistry()
        registry.register("test", lon=106.5, lat=37.5, groups=SOLAR)

        assert registry.unregister("test")
        assert "test" not in registry
        assert "test" not in registry.get_locations(SOLAR)
        assert not registry.unregister("nonexistent")

    def test_clear(self) -> None:
        registry = LocationRegistry()
        registry.register("s_1", lon=106.5, lat=37.5, groups=SOLAR)
        registry.register("w_1", lon=107.0, lat=38.0, groups=WIND)

        registry.clear()
        assert len(registry) == 0
        assert len(registry.get_locations(SOLAR)) == 0
        assert len(registry.get_locations(WIND)) == 0


# =============================================================================
# TerraQTClient Tests
# =============================================================================


class TestTerraQTClient:
    """Tests for TerraQTClient."""

    @pytest.mark.asyncio
    async def test_fetch_forecast_success(
        self, mock_api_response: dict, sample_forecast_data: pd.DataFrame
    ) -> None:
        """Test successful forecast fetch."""
        with patch("aiohttp.ClientSession") as mock_session_class:
            mock_response = AsyncMock()
            mock_response.raise_for_status = MagicMock()
            mock_response.json = AsyncMock(return_value=mock_api_response)
            mock_response.__aenter__ = AsyncMock(return_value=mock_response)
            mock_response.__aexit__ = AsyncMock(return_value=None)

            mock_session = MagicMock()
            mock_session.request = MagicMock(return_value=mock_response)
            mock_session.close = AsyncMock()
            mock_session_class.return_value = mock_session

            client = TerraQTClient(api_token="test_token")
            client._session = mock_session

            df, forecast_time = await client.fetch_forecast(
                model="gfs_surface",
                lon=106.5,
                lat=37.5,
                variables=["dswrf", "tcc"],
            )

            assert df.shape == sample_forecast_data.shape
            assert list(df.columns) == ["dswrf", "tcc"]

    @pytest.mark.asyncio
    async def test_client_context_manager(self) -> None:
        """Test client as async context manager."""
        async with TerraQTClient(api_token="test_token") as client:
            assert client._session is not None
        assert client._session is None

    def test_client_headers(self) -> None:
        """Test that headers are correctly set."""
        client = TerraQTClient(api_token="test_token")
        headers = client._get_headers()

        assert headers["Content-Type"] == "application/json"
        assert headers["token"] == "test_token"

    def test_client_from_config(self) -> None:
        """Test creating client from config."""
        config = TerraQTConfig(api_token="test_token", max_concurrency=20)
        client = TerraQTClient.from_config(config)

        assert client._max_concurrency == 20


# =============================================================================
# TerraQTQueryBuilder Tests
# =============================================================================


class TestTerraQTQueryBuilder:
    """Tests for TerraQTQueryBuilder."""

    @pytest.mark.asyncio
    async def test_query_builder_execute(
        self,
        location_registry: LocationRegistry,
        model_configs: dict[str, ModelConfig],
        sample_forecast_data: pd.DataFrame,
    ) -> None:
        """Test query builder execution."""
        mock_client = AsyncMock(spec=TerraQTClient)
        mock_client.fetch_forecast = AsyncMock(
            return_value=(sample_forecast_data, datetime(2026, 1, 22))
        )

        builder = TerraQTQueryBuilder(mock_client, location_registry, model_configs)

        collection = await (
            builder.models(["gfs_surface"]).locations_by_group(SOLAR).execute()
        )

        assert collection
        assert "gfs_surface" in collection.models()

    @pytest.mark.asyncio
    async def test_query_builder_no_models(
        self, location_registry: LocationRegistry, model_configs: dict[str, ModelConfig]
    ) -> None:
        """Test query builder with no models raises error."""
        mock_client = AsyncMock(spec=TerraQTClient)
        builder = TerraQTQueryBuilder(mock_client, location_registry, model_configs)

        with pytest.raises(ValueError, match="No models specified"):
            await builder.locations_by_group(SOLAR).execute()

    @pytest.mark.asyncio
    async def test_query_builder_no_locations(
        self, location_registry: LocationRegistry, model_configs: dict[str, ModelConfig]
    ) -> None:
        """Test query builder with no locations raises error."""
        mock_client = AsyncMock(spec=TerraQTClient)
        builder = TerraQTQueryBuilder(mock_client, location_registry, model_configs)

        with pytest.raises(ValueError, match="No locations specified"):
            await builder.models(["gfs_surface"]).variable_group(SOLAR).execute()

    @pytest.mark.asyncio
    async def test_query_builder_no_query_type(
        self, location_registry: LocationRegistry, model_configs: dict[str, ModelConfig]
    ) -> None:
        """Test query builder with no query type raises error."""
        mock_client = AsyncMock(spec=TerraQTClient)
        builder = TerraQTQueryBuilder(mock_client, location_registry, model_configs)

        with pytest.raises(ValueError, match="No variables or variable set specified"):
            await builder.models(["gfs_surface"]).locations(["s_1", "s_2"]).execute()

    def test_query_builder_method_chaining(
        self, location_registry: LocationRegistry, model_configs: dict[str, ModelConfig]
    ) -> None:
        """Test that builder methods return self for chaining."""
        mock_client = MagicMock(spec=TerraQTClient)
        builder = TerraQTQueryBuilder(mock_client, location_registry, model_configs)

        result = builder.models(["gfs_surface"])
        assert result is builder

        result = builder.locations_by_group(SOLAR)
        assert result is builder


# =============================================================================
# TerraQT Integration Tests
# =============================================================================


class TestTerraQTIntegration:
    """Integration tests for TerraQT main class."""

    def test_terraqt_initialization(self) -> None:
        """Test TerraQT initialization."""
        tqt = TerraQT(api_token="test_token")
        assert tqt.config.api_token == "test_token"
        assert tqt.locations is not None

    def test_terraqt_requires_token_or_config(self) -> None:
        """Test TerraQT requires either token or config."""
        with pytest.raises(ValueError, match="Either api_token or config"):
            TerraQT()

    def test_terraqt_with_config(self) -> None:
        """Test TerraQT with config object."""
        config = TerraQTConfig(api_token="test_token", max_concurrency=20)
        tqt = TerraQT(config=config)
        assert tqt.config.max_concurrency == 20

    def test_terraqt_client_factory(self) -> None:
        """Test client factory method."""
        tqt = TerraQT(api_token="test_token")
        client = tqt.client()
        assert isinstance(client, TerraQTClient)

    def test_terraqt_query_factory(self) -> None:
        """Test query factory method."""
        tqt = TerraQT(api_token="test_token")
        client = MagicMock(spec=TerraQTClient)
        builder = tqt.query(client)
        assert isinstance(builder, TerraQTQueryBuilder)

    @pytest.mark.asyncio
    async def test_full_pipeline_mock(self, sample_forecast_data: pd.DataFrame) -> None:
        """Test full pipeline with mocked data."""
        tqt = TerraQT(api_token="test_token")

        # Setup locations
        tqt.locations.register(
            "s_1", lon=106.5, lat=37.5, weight=0.6, groups=SOLAR
        )
        tqt.locations.register(
            "s_2", lon=105.5, lat=36.5, weight=0.4, groups=SOLAR
        )

        # Mock client fetch
        with patch.object(TerraQTClient, "fetch_forecast") as mock_fetch:
            mock_fetch.return_value = (sample_forecast_data, datetime(2026, 1, 22))

            async with tqt.client() as client:
                collection = await (
                    tqt.query(client)
                    .models(["gfs_surface"])
                    .locations_by_group(SOLAR)
                    .execute()
                )

            assert "gfs_surface" in collection.models()


# =============================================================================
# Run tests
# =============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
