"""Base classes for provider management."""

from __future__ import annotations

import sys
from typing import Any

from .config import ConfigMixin
from .cost import CostMixin
from .package import PackageMixin
from .response import ResponseMixin
from .service import ServiceMixin
from .urls import UrlsMixin

FIELDS_PROVIDER_BASE = {
    'name': {'label': 'Name', 'description': 'Provider name', 'format': 'str'},
    'display_name': {
        'label': 'Display Name',
        'description': 'Provider display name',
        'format': 'str',
    },
    'description': {'label': 'Description', 'description': 'Provider description', 'format': 'str'},
    'priority': {'label': 'Priority', 'description': 'Provider priority', 'format': 'int'},
}


class ProviderBase(PackageMixin, UrlsMixin, ConfigMixin, ServiceMixin, CostMixin, ResponseMixin):
    """Base class for providers with basic identification information."""

    name: str
    display_name: str
    description: str | None
    mandatory_base_fields: list[str] = ['name', 'display_name']
    path: str | None = None
    abstract: bool = False
    priority: int = 0  # 0 - highest, 5 - lowest
    provider_key: str = 'label'
    fields_associations: dict = {}
    fields_services: dict = {}

    def __init_subclass__(cls, **kwargs):
        """Automatically import required packages when subclass is defined."""
        super().__init_subclass__(**kwargs)
        if hasattr(cls, 'required_packages') and cls.required_packages:
            frame = sys._getframe(1)
            module_globals = frame.f_globals
            PackageMixin.safe_import_packages(cls.required_packages, module_globals)

    def __init__(self, **kwargs: str | None) -> None:
        """Initialize a provider with required identification."""
        for field in self.mandatory_base_fields:
            setattr(self, field, kwargs.pop(field, getattr(self, field)))
            if not getattr(self, field):
                raise ValueError(f'{field} is required and cannot be empty')

        config = kwargs.pop('config', None)
        if config is not None:
            if isinstance(config, dict):
                self._init_config(config)
            else:
                self._init_config(None)

        for field, value in kwargs.items():
            setattr(self, field, value)

        self._service_results_cache: dict[str, dict[str, Any]] = {}

    def _get_nested_value(  # noqa: C901
        self, data: dict[str, Any], path: str | list[str] | tuple[str, ...], default: Any = None
    ) -> Any:
        if isinstance(path, (list, tuple)):
            for p in path:
                value = self._get_nested_value(data, p, None)
                if value is not None:
                    return value
            return default

        if not path:
            return default
        keys = path.split('.')
        val: Any = data
        for k in keys:
            if isinstance(val, dict):
                val = val.get(k)
            elif isinstance(val, list):
                try:
                    index = int(k)
                    if 0 <= index < len(val):
                        val = val[index]
                    else:
                        return default
                except (ValueError, TypeError):
                    return default
            else:
                return default
            if val is None:
                return default
        return val

    def _normalize_recursive(  # noqa: C901
        self,
        data: dict[str, Any] | Any,
        field: str,
        source: str | list[str] | tuple[str, ...] | None,
    ) -> Any:
        if source is None:
            return None
        if isinstance(source, (tuple, list)):
            for path in source:
                value = self._normalize_recursive(data, field, path)
                if value is not None:
                    return value
            return None
        if callable(source):
            return source(data)
        if isinstance(source, str):
            if '.' in source:
                parts = source.split('.')
                current = data
                for part in parts:
                    if isinstance(current, list):
                        try:
                            index = int(part)
                            if 0 <= index < len(current):
                                current = current[index]
                            else:
                                return None
                        except ValueError:
                            return None
                    elif isinstance(current, dict):
                        current = current.get(part)
                    else:
                        current = getattr(current, part, None)
                    if current is None:
                        return None
                return current() if callable(current) else current
            if isinstance(data, dict):
                return data.get(source)
            value = getattr(data, source, None)
            if callable(value):
                return value()
            return value
        return source

    def get_insert_data_value(self, data: Any, normalized: dict[str, Any], field: str, field_cfg: dict[str, Any]) -> Any:
        value = getattr(self, field, None)
        if hasattr(self, f'get_insert_normalized_{field}') and callable(getattr(self, f'get_insert_normalized_{field}')):
            value = getattr(self, f'get_insert_normalized_{field}')(data, normalized, field_cfg)
        return value

    def insert_data_as_list(self, data: Any, normalized: list[dict[str, Any]], config: dict[str, Any] | None = None) -> list[dict[str, Any]]:
        cfg = config.get('fields', {}) if isinstance(config, dict) and 'fields' in config else config
        if cfg is None:
            return normalized
        for item in normalized:
            item_keys = item.keys()
            for field, field_cfg in cfg.items():
                if field in item_keys and item[field] is None:
                    item[field] = self.get_insert_data_value(data, item, field, field_cfg)
        return normalized

    def insert_data_as_dict(self, data: Any, normalized: dict[str, Any], config: dict[str, Any] | None = None) -> dict[str, Any]:
        cfg = config.get('fields', {}) if isinstance(config, dict) and 'fields' in config else config
        if cfg is None:
            return normalized
        item_keys = normalized.keys()
        for field, field_cfg in cfg.items():
            if field in item_keys and normalized[field] is None:
                normalized[field] = self.get_insert_data_value(data, normalized, field, field_cfg)
        return normalized

    def insert_data_normalized(self, data: Any, normalized: Any, config: dict[str, Any] | None = None) -> Any:
        """Insert additional data into normalized result. Can be overridden by providers."""
        config = getattr(self, 'services_cfg', {}).get(getattr(self, 'current_service_name', None), config) or config
        if isinstance(normalized, list):
            normalized = self.insert_data_as_list(data, normalized, config)
        elif isinstance(normalized, dict):
            normalized = self.insert_data_as_dict(data, normalized, config)
        return normalized

    def normalize(
        self, data: dict[str, Any], config: dict[str, Any] | None = None
    ) -> dict[str, Any]:
        if config is None:
            config = getattr(self, 'config', {})
        fields = config.get('fields', {})
        normalized: dict[str, Any] = {}
        for field, cfg in fields.items():
            normalize_method = getattr(self, f'get_normalize_{field}', None)
            if normalize_method and callable(normalize_method):
                value = normalize_method(data)
            else:
                source = cfg.get('source', self.fields_associations.get(field, field))
                value = self._normalize_recursive(data, field, source)
            label = field if self.provider_key == 'key' else cfg.get(self.provider_key, field)
            normalized[label] = value
        normalized = self.insert_data_normalized(data, normalized, config)
        return normalized

    def get_insert_normalized_backend(self, _data: Any, _normalized: dict[str, Any], _config: dict[str, Any]) -> str:
        return self.name

    def get_insert_normalized_backend_name(self, _data: Any, _normalized: dict[str, Any], _config: dict[str, Any]) -> str:
        return self.display_name
