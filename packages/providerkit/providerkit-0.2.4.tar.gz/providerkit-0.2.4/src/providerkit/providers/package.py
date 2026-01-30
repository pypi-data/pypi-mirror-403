from __future__ import annotations

from providerkit.kit import ProviderBase  # noqa: TC001
from providerkit.providers.base import ProviderListBase


class ProviderListPackage(ProviderListBase):
    name = 'package'
    display_name = 'Package Providers'
    description = 'Get providers from a package.'
    priority = 4

    def get_providers(self, *_args, **kwargs) -> list[ProviderBase]:
        from providerkit.helpers.load import load_providers_from_package

        lib_name = kwargs.pop('lib_name', 'providerkit')
        if lib_name is None:
            return []
        providers_result = load_providers_from_package(lib_name)
        if isinstance(providers_result, str):
            return []

        return self.compile_providers(providers_result, **kwargs)

