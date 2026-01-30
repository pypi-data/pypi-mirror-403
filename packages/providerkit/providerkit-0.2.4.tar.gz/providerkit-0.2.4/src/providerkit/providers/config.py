from __future__ import annotations

from providerkit.kit import ProviderBase  # noqa: TC001
from providerkit.providers.base import ProviderListBase


class ProviderListConfig(ProviderListBase):
    name = 'config'
    display_name = 'Config Providers'
    description = 'Get providers from a configuration.'
    priority = 3

    def get_providers(self, *_args, **kwargs) -> list[ProviderBase]:
        from providerkit.helpers import load_providers_from_config

        config = kwargs.get('config')

        if config is None:
            return []
        providers_dict = load_providers_from_config(config)
        return self.compile_providers(providers_dict, **kwargs)
