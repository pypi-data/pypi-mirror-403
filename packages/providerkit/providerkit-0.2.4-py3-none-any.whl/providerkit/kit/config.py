"""Configuration management mixin for providers."""

from __future__ import annotations

import os
from typing import Any, cast

FIELDS_CONFIG_BASE = {
    'config_status_str': {
        'label': 'Config status',
        'description': 'Config status',
        'format': 'str',
    },
    'config_prefix': {'label': 'Config prefix', 'description': 'Config prefix', 'format': 'str'},
    'config_keys': {'label': 'Config keys', 'description': 'Config keys', 'format': 'list'},
    'missing_config_keys': {
        'label': 'Missing config keys',
        'description': 'Missing config keys',
        'format': 'list',
    },
    'is_config_ready': {
        'label': 'Is config ready',
        'description': 'Is config ready',
        'format': 'bool',
    },
}


class ConfigMixin:
    """Mixin for managing provider configuration."""

    config_keys: list[str] = []
    config_prefix: str = ''
    config_authorized: list[str] = [
        'check_config_keys',
        'get_config_keys',
        'get_missing_config_keys',
    ]

    def _init_config(self, config: dict[str, Any] | None = None) -> None:
        if not hasattr(self, '_config'):
            self._config: dict[str, Any] = {}
        if config is not None:
            filtered = self._filter_config(config)
            self._config = filtered
            self.clear_config_cache()

    def _filter_config(self, config: dict[str, Any]) -> dict[str, Any]:
        if not self.config_keys:
            return dict(config)
        return {key: config[key] for key in self.config_keys if key in config}

    def _get_config_or_env(self, key: str, default: Any = None) -> Any:
        config = getattr(self, '_config', {})
        value = config.get(key)
        if value is not None:
            return value

        provider_name = getattr(self, 'name', '').upper().replace('-', '_')
        key_upper = key.upper()

        if self.config_prefix:
            env_key_with_prefix = f'{self.config_prefix}_{provider_name}_{key_upper}'
            value = os.getenv(env_key_with_prefix)
            if value is not None:
                return value

        env_key_provider = f'{provider_name}_{key_upper}'
        value = os.getenv(env_key_provider)
        if value is not None:
            return value

        value = os.getenv(key_upper)
        if value is not None:
            return value

        config_defaults = getattr(self, 'config_defaults', {})
        if key in config_defaults:
            return config_defaults[key]


        return default

    def configure(self, config: dict[str, Any], *, replace: bool = False) -> Any:
        """Update provider configuration."""
        if not hasattr(self, '_config'):
            self._config = {}
        filtered = self._filter_config(config)
        if replace:
            self._config = filtered
        else:
            self._config.update(filtered)
        self.clear_config_cache()
        return self

    def get_config_keys(self) -> list[str]:
        """Get configuration keys."""
        return getattr(self, 'config_keys', [])

    @property
    def config(self) -> dict[str, Any]:
        """Access configuration values."""
        if not hasattr(self, '_config'):
            self._config = {}
        return self._config

    def check_config_keys(self, config: dict[str, Any] | None = None) -> dict[str, bool]:
        """Check if all required configuration keys are present."""
        config_defaults = getattr(self, 'config_defaults', {})

        if config is not None:
            result: dict[str, bool] = {}
            for key in self.config_keys:
                present = key in config
                if not present:
                    present = key in config_defaults
                if not present:
                    value = self._get_config_or_env(key)
                    present = value is not None
                result[key] = present
            return result

        if hasattr(self, '_config_keys_cache'):
            cached = getattr(self, '_config_keys_cache', {})
            return cast('dict[str, bool]', cached)

        config_to_check = getattr(self, '_config', {})
        cached_result: dict[str, bool] = {}
        for key in self.config_keys:
            present = key in config_to_check
            if not present:
                present = key in config_defaults
            if not present:
                value = self._get_config_or_env(key)
                present = value is not None
            cached_result[key] = present
        self._config_keys_cache = cached_result
        return cached_result

    def clear_config_cache(self) -> None:
        """Clear cached config keys check results."""
        if hasattr(self, '_config_keys_cache'):
            delattr(self, '_config_keys_cache')

    def is_config_ready(self, config: dict[str, Any] | None = None) -> bool:
        """Check if all required configuration keys are present."""
        status = self.check_config_keys(config)
        return all(status.values())

    def get_missing_config_keys(self, config: dict[str, Any] | None = None) -> list[str]:
        """Get list of missing configuration keys."""
        status = self.check_config_keys(config)
        return [key for key, present in status.items() if not present]

    @property
    def missing_config_keys(self) -> list[str]:
        """Get list of missing configuration keys."""
        return self.get_missing_config_keys()

    @property
    def config_status_str(self) -> str:
        """Get status of configuration keys."""
        if self.is_config_ready():
            return '✓'
        missing_keys = self.get_missing_config_keys()
        if not missing_keys:
            return 'N/A'
        mk = len(self.config_keys) - len(missing_keys)
        return f'{mk}/{len(self.config_keys)}'
