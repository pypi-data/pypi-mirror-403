"""Service implementation mixin for providers."""

from __future__ import annotations

import copy
import hashlib
import json
from typing import TYPE_CHECKING, Any, cast

if TYPE_CHECKING:
    from collections.abc import Callable

FIELDS_SERVICE_BASE = {
    'service_status_str': {
        'label': 'Service status',
        'description': 'Service status',
        'format': 'str',
    },
    'missing_services': {
        'label': 'Missing services',
        'description': 'Missing services',
        'format': 'list',
    },
    'services': {'label': 'Services', 'description': 'Services', 'format': 'list'},
    'are_services_implemented': {
        'label': 'Are services implemented',
        'description': 'Are services implemented',
        'format': 'bool',
    },
}


class ServiceMixin:
    """Mixin for managing required service methods."""
    _default_services_cfg: dict[str, dict[str, Any]] = {}
    services_authorized: list[str] = [
        'check_services',
        'get_required_services',
        'get_missing_services',
        'get_services_authorized',
    ]

    @classmethod
    def _merge_services_fields(cls, services_fields: dict) -> None:
        """Merge services_fields into services_cfg fields."""
        services_cfg = getattr(cls, 'services_cfg', {})
        for service_name, fields in services_fields.items():
            if service_name in services_cfg:
                if 'fields' not in services_cfg[service_name]:
                    services_cfg[service_name]['fields'] = {}
                services_cfg[service_name]['fields'].update(fields)

    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        cls.current_service_name = None
        cls.services_cfg = copy.deepcopy(cls._default_services_cfg)
        # Merge services_fields into services_cfg fields
        services_fields = getattr(cls, 'services_fields', {})
        cls._merge_services_fields(services_fields)

    def get_required_services(self) -> list[str]:
        """Get required service methods."""
        return getattr(self, 'services', [])

    def is_service_implemented(self, service_name: str) -> bool:
        """Check if service method is implemented."""
        method = getattr(self, service_name, None)
        return callable(method) and not isinstance(method, type)

    def check_services(self) -> dict[str, bool]:
        """Check implementation status of all required services."""
        if hasattr(self, '_services_cache'):
            cached = getattr(self, '_services_cache', {})
            return cast('dict[str, bool]', cached)

        services = self.get_required_services()
        status: dict[str, bool] = {
            service: self.is_service_implemented(service) for service in services
        }
        self._services_cache = status
        return status

    def clear_services_cache(self) -> None:
        """Clear cached service check results."""
        if hasattr(self, '_services_cache'):
            delattr(self, '_services_cache')

    def are_services_implemented(self) -> bool:
        """Check if all required services are implemented."""
        status = self.check_services()
        return all(status.values())

    def get_missing_services(self) -> list[str]:
        """Get list of missing services."""
        status = self.check_services()
        return [service for service, implemented in status.items() if not implemented]

    @property
    def missing_services(self) -> list[str]:
        """Get list of missing services."""
        return self.get_missing_services()

    @property
    def services(self) -> list[str]:
        """Get list of services."""
        return list(getattr(self, 'services_cfg', {}).keys())

    @property
    def service_status_str(self) -> str:
        if self.are_services_implemented():
            return '✓'
        services = self.get_required_services()
        if not services:
            return 'N/A'
        implemented_count = sum(1 for service in services if self.is_service_implemented(service))
        total_count = len(services)

        if implemented_count == total_count:
            return '✓'
        return f'{implemented_count}/{total_count}'

    def _get_hash_service_args(self, *args: Any, **kwargs: Any) -> str:
        """Generate hash from service arguments."""
        try:
            cache_data = json.dumps(
                {'args': args, 'kwargs': sorted(kwargs.items())},
                sort_keys=True,
                default=str,
            )
            return hashlib.md5(cache_data.encode(), usedforsecurity=False).hexdigest()  # noqa: S324
        except (TypeError, ValueError):
            cache_data = f'{repr(args)}:{repr(sorted(kwargs.items()))}'
            return hashlib.md5(cache_data.encode(), usedforsecurity=False).hexdigest()  # noqa: S324

    def get_services_authorized(self) -> list[str]:
        svc = list(self.services_authorized)
        svc.extend(cast('list[str]', getattr(self, 'package_authorized', [])))
        svc.extend(cast('list[str]', getattr(self, 'config_authorized', [])))
        svc.extend(cast('list[str]', getattr(self, 'urls_authorized', [])))
        svc.extend(getattr(self, 'services_cfg', {}).keys())
        return svc

    def call_service(self, service_name: str, *args: Any, **kwargs: Any) -> Any:
        """Call service method with caching."""
        if not hasattr(self, '_service_results_cache'):
            self._service_results_cache: dict[str, dict[str, Any]] = {}

        if service_name not in self._service_results_cache:
            self._service_results_cache[service_name] = {}

        service_args_hash = self._get_hash_service_args(*args, **kwargs)

        if (
            'hash' in self._service_results_cache[service_name]
            and self._service_results_cache[service_name]['hash'] == service_args_hash
            and 'result' in self._service_results_cache[service_name]
        ):
            return self._service_results_cache[service_name]['result']

        if service_name not in self.get_services_authorized():
            error_result = {'error': f"Service '{service_name}' do not appears in services list"}
            self._service_results_cache[service_name]['hash'] = service_args_hash
            self._service_results_cache[service_name]['result'] = error_result
            raise AttributeError(f"Service '{service_name}' do not appears in services list")

        if not self.is_service_implemented(service_name):
            error_result = {'error': f"Service '{service_name}' is not implemented"}
            self._service_results_cache[service_name]['hash'] = service_args_hash
            self._service_results_cache[service_name]['result'] = error_result
            raise AttributeError(f"Service '{service_name}' is not implemented")

        method = getattr(self, service_name)
        self._service_results_cache[service_name]['hash'] = service_args_hash
        try:
            result = method(*args, **kwargs)
            self._service_results_cache[service_name]['result'] = result
            return result
        except Exception as e:
            self._service_results_cache[service_name]['error'] = str(e)
            raise e

    def clear_service_results_cache(self) -> None:
        """Clear cached service results."""
        if hasattr(self, '_service_results_cache'):
            self._service_results_cache.clear()

    def get_service_results_cache(self) -> dict[str, dict[str, Any]]:
        """Get cached service results."""
        return getattr(self, '_service_results_cache', {})

    def get_service_result(self, service_name: str) -> Any:
        """Get cached service result."""
        if not hasattr(self, '_service_results_cache'):
            raise ValueError(f"No cache found for service '{service_name}'")

        if service_name not in self._service_results_cache:
            raise ValueError(f"Service '{service_name}' not found in cache")

        return self._service_results_cache[service_name]['result']

    def get_service_normalize(self, service_name: str, **kwargs: Any) -> dict[str, Any] | list[dict[str, Any]]:
        """Get cached service result normalized."""
        self.current_service_name = service_name
        if not hasattr(self, '_service_results_cache'):
            raise ValueError(f"No cache found for service '{service_name}'")

        if service_name not in self._service_results_cache:
            raise ValueError(f"Service '{service_name}' not found in cache")

        if 'result' not in self._service_results_cache[service_name]:
            raise ValueError(f"No result cached for service '{service_name}'")
        result = self._service_results_cache[service_name]['result']
        # Check if result contains an error - if so, return only the error
        if isinstance(result, dict) and 'error' in result:
            return {'error': result['error']}
        if isinstance(result, list) and result and isinstance(result[0], dict) and 'error' in result[0]:
            return {'error': result[0]['error']}

        config = kwargs.get('services_cfg') or getattr(self, 'services_cfg', {}).get(service_name, {})
        result = self.serialize_data(result, config)
        setattr(self, 'current_service_name', None)  # noqa: B010
        return result

    def serialize_data(self, result: Any, config: dict[str, Any], **_kwargs: Any) -> dict[str, Any] | list[dict[str, Any]]:
        normalize_func: Callable[[Any, dict[str, Any]], dict[str, Any]] = cast(
            'Callable[[Any, dict[str, Any]], dict[str, Any]]',
            getattr(self, 'normalize', lambda x, _: x)
        )
        if isinstance(result, list):
            normalized = [cast('dict[str, Any]', normalize_func(item, config)) for item in result]
            return normalized
        if isinstance(result, dict):
            normalized_dict = cast('dict[str, Any]', normalize_func(result, config))
            return normalized_dict
        normalized_single = cast('dict[str, Any]', normalize_func(result, config))
        return normalized_single
