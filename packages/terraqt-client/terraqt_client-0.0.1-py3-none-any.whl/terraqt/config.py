"""
TerraQT Client - Configuration Management

Centralized configuration with validation and sensible defaults.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from terraqt.models import ModelConfig

from terraqt.models import SOLAR, WIND
from terraqt.models import ModelConfig as MC


def _default_model_configs() -> dict[str, MC]:
    """Create default model configurations."""
    return {
        "aifs_surface": MC(
            name="aifs_surface",
            variable_groups={
                WIND: ("ws100m",),
                SOLAR: ("ssrd", "tcc"),
            },
            model_type="forecast",
        ),
        "gfs_surface": MC(
            name="gfs_surface",
            variable_groups={
                WIND: ("ws100m",),
                SOLAR: ("dswrf", "tcc"),
            },
            model_type="forecast",
        ),
        "cfs_h6_surface": MC(
            name="cfs_h6_surface",
            variable_groups={
                WIND: ("ws10m",),
                SOLAR: ("dswrf", "tcc"),
            },
            model_type="forecast",
        ),
    }


DEFAULT_MODEL_CONFIGS: dict[str, MC] = _default_model_configs()


@dataclass
class TerraQTConfig:
    """
    Main configuration container for TerraQT Client.

    Centralizes all configuration including API settings,
    model configurations, and optional database settings.

    Example:
        >>> config = TerraQTConfig(api_token="your_token")
        >>> config.register_model(custom_model_config)
        >>> config.available_models()
        ['aifs_surface', 'gfs_surface', 'cfs_h6_surface', 'custom']
    """

    api_token: str
    api_base_url: str = "https://api-pro-openet.terraqt.com/v1"
    model_configs: dict[str, MC] = field(default_factory=_default_model_configs)
    timeout_total: float = 120.0
    timeout_connect: float = 10.0
    timeout_read: float = 60.0
    max_concurrency: int = 10
    retry_attempts: int = 3
    retry_backoff: float = 1.0

    @classmethod
    def from_env(cls, prefix: str = "TERRAQT_") -> TerraQTConfig:
        """
        Create configuration from environment variables.

        Args:
            prefix: Environment variable prefix (default: "TERRAQT_").

        Returns:
            Configured TerraQTConfig instance.

        Raises:
            ValueError: If required environment variables are missing.
        """
        import os

        api_token = os.environ.get(f"{prefix}API_TOKEN")
        if not api_token:
            raise ValueError(f"Missing required environment variable: {prefix}API_TOKEN")

        return cls(
            api_token=api_token,
            api_base_url=os.environ.get(f"{prefix}API_BASE_URL", cls.api_base_url),
            timeout_total=float(os.environ.get(f"{prefix}TIMEOUT_TOTAL", "120.0")),
            max_concurrency=int(os.environ.get(f"{prefix}MAX_CONCURRENCY", "10")),
        )

    def get_model_config(self, model_name: str) -> MC | None:
        """Get configuration for a specific model."""
        return self.model_configs.get(model_name)

    def register_model(self, config: MC) -> None:
        """
        Register a new model configuration.

        Args:
            config: Model configuration to register.
        """
        self.model_configs[config.name] = config

    def available_models(self) -> list[str]:
        """Get list of available model names."""
        return list(self.model_configs.keys())
