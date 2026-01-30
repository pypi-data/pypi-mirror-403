from __future__ import annotations

from providerkit.kit import ProviderBase  # noqa: TC001
from providerkit.providers.base import ProviderListBase


class ProviderListJson(ProviderListBase):
    name = 'json'
    display_name = 'JSON Providers'
    description = 'Get providers from a JSON file.'
    priority = 2

    def get_providers(self, *_args, **kwargs) -> list[ProviderBase]:
        from providerkit.helpers import load_providers_from_json

        lib_name = kwargs.get('lib_name', 'providerkit')
        json_param = kwargs.get('json')
        providers_dict = load_providers_from_json(json_param, lib_name=lib_name)
        return self.compile_providers(providers_dict, **kwargs)

