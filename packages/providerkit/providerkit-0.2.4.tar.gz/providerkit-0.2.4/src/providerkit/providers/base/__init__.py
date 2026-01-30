from __future__ import annotations

from typing import TYPE_CHECKING, Any, cast

if TYPE_CHECKING:
    from collections.abc import Callable

from providerkit.kit import FIELDS_PROVIDER_BASE, ProviderBase
from providerkit.kit.config import FIELDS_CONFIG_BASE
from providerkit.kit.cost import FIELDS_COSTS_BASE
from providerkit.kit.package import FIELDS_PACKAGE_BASE
from providerkit.kit.service import FIELDS_SERVICE_BASE
from providerkit.kit.urls import FIELDS_URLS_BASE

from .execute import ProviderListExecute
from .filter import ProviderListFilter
from .sort import ProviderListSort

FIELDS_GET_PROVIDERS = {
    **FIELDS_PROVIDER_BASE,
    'config_status_str': FIELDS_CONFIG_BASE['config_status_str'],
    'package_status_str': FIELDS_PACKAGE_BASE['package_status_str'],
    'service_status_str': FIELDS_SERVICE_BASE['service_status_str'],
}

FIELDS_GET_INFOS = {
    'hash': {
        'label': 'Hash',
        'source': lambda obj: hash(obj),
        'format': 'str',
        'description': 'Hash of the provider',
    },
    'class_name': {
        'label': 'Class Name',
        'source': '__class__.__name__',
        'format': 'str',
        'description': 'Class name of the provider',
    },
}

FIELDS_SERVICE_DEFAULTS = {
    **{'name': FIELDS_PROVIDER_BASE['name']},
    **{'display_name': FIELDS_PROVIDER_BASE['display_name']},
}


class ProviderListBase(ProviderBase, ProviderListSort, ProviderListFilter, ProviderListExecute):
    name = 'providerlist'
    display_name = 'Provider List'
    description = 'Provider list'
    config_prefix = 'PROVIDERLIST'
    documentation_url = 'https://pypi.org/project/providerkit/'
    site_url = 'https://github.com/hicinformatic/python-providerkit'
    status_url = 'https://github.com/hicinformatic/python-providerkit'
    _default_services_cfg = {
        'get_providers': {'label': 'Get providers', 'description': 'Get providers', 'fields': FIELDS_GET_PROVIDERS},
        'get_infos': {'label': 'Get infos', 'description': 'Get infos', 'fields': {**FIELDS_PROVIDER_BASE, **FIELDS_GET_INFOS}},
        'get_config': {'label': 'Get config', 'description': 'Get config', 'fields': {**FIELDS_SERVICE_DEFAULTS, **FIELDS_CONFIG_BASE}},
        'get_package': {'label': 'Get package', 'description': 'Get package', 'fields': {**FIELDS_SERVICE_DEFAULTS, **FIELDS_PACKAGE_BASE}},
        'get_service': {'label': 'Get service', 'description': 'Get service', 'fields': {**FIELDS_SERVICE_DEFAULTS, **FIELDS_SERVICE_BASE}},
        'get_urls': {'label': 'Get urls', 'description': 'Get urls', 'fields': {**FIELDS_SERVICE_DEFAULTS, **FIELDS_URLS_BASE}},
        'get_costs': {'label': 'Get cost', 'description': 'Get cost', 'fields': {**FIELDS_COSTS_BASE}},
    }

    def get_infos(self) -> dict[str, Any]:
        return cast('dict[str, Any]', self.__dict__)

    def get_config(self, *args, **kwargs) -> list[ProviderBase]:
        get_providers_func: Callable[..., list[ProviderBase]] = cast('Callable[..., list[ProviderBase]]', self.get_providers)  # type: ignore[attr-defined]
        return get_providers_func(*args, **kwargs)

    def get_package(self, *args, **kwargs) -> list[ProviderBase]:
        get_providers_func: Callable[..., list[ProviderBase]] = cast('Callable[..., list[ProviderBase]]', self.get_providers)  # type: ignore[attr-defined]
        return get_providers_func(*args, **kwargs)

    def get_service(self, *args, **kwargs) -> list[ProviderBase]:
        get_providers_func: Callable[..., list[ProviderBase]] = cast('Callable[..., list[ProviderBase]]', self.get_providers)  # type: ignore[attr-defined]
        return get_providers_func(*args, **kwargs)

    def get_urls(self, *args, **kwargs) -> list[ProviderBase]:
        get_providers_func: Callable[..., list[ProviderBase]] = cast('Callable[..., list[ProviderBase]]', self.get_providers)  # type: ignore[attr-defined]
        return get_providers_func(*args, **kwargs)

    def get_costs(self, *_args: Any, **_kwargs: Any) -> list[dict[str, Any]]:
        costs = self.get_costs_services()
        return [{"service": key, "cost": value} for key, value in costs.items()]

    def compile_providers(self, providers: dict[str, ProviderBase] | list[ProviderBase], **kwargs) -> list[ProviderBase]:
        if kwargs.get('add_fields'):
            services_cfg = getattr(self, 'services_cfg', {})
            for service in services_cfg:
                services_cfg[service]['fields'].update(kwargs.get('add_fields', {}))
        providers_list = list(providers.values()) if isinstance(providers, dict) else providers
        attribute_search = kwargs.pop('attribute_search', {})
        if attribute_search:
            providers_list = self.filter_providers(providers_list, attribute_search)
        return self.sort_providers(providers_list, kwargs.get('order_by', ['-priority', 'name']))
