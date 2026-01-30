from __future__ import annotations

from providerkit.kit import ProviderBase  # noqa: TC001
from providerkit.providers.base import ProviderListBase


class ProviderListFolder(ProviderListBase):
    name = 'folder'
    display_name = 'Folder Providers'
    description = 'Get providers from a folder.'
    priority = 1

    def get_providers(self, *_args, **kwargs) -> list[ProviderBase]:
        from providerkit.helpers import load_providers_from_dir

        dir_path = kwargs.get('dir_path')
        base_module = kwargs.get('base_module')
        if dir_path is None:
            return []
        providers_dict = load_providers_from_dir(dir_path, base_module=base_module)
        return self.compile_providers(providers_dict, **kwargs)
