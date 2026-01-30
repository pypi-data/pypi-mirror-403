from typing import TYPE_CHECKING, Any, cast

if TYPE_CHECKING:
    from collections.abc import Callable

    from providerkit.kit import ProviderBase


class ProviderListExecute:
    """Execute providers."""

    def execute_providers(
        self, command: str, first: bool = False, *args, **kwargs
    ) -> tuple[list[dict[str, Any]], str]:
        """Execute each provider."""
        lib_name = kwargs.get('lib_name', 'providerkit')
        get_providers_func: Callable[..., list[ProviderBase]] = cast('Callable[..., list[ProviderBase]]', self.get_providers)  # type: ignore[attr-defined]
        providers = get_providers_func(lib_name=lib_name)
        if not providers:
            raise RuntimeError('No providers available')
        pv_executed = []
        last_provider = None

        for provider in providers:
            last_provider = provider
            try:
                provider.call_service(command, *args, **kwargs)
                pv_executed.append(
                    {
                        'name': provider.name,
                        'provider': provider,
                    }
                )
                if first:
                    break
            except Exception as e:
                pv_executed.append(
                    {
                        'name': provider.name,
                        'provider': provider,
                        'error': str(e),
                    }
                )
        if not hasattr(self, '_service_results_cache'):
            self._service_results_cache: dict[str, Any] = {}
        if not hasattr(self, '_get_hash_service_args'):

            def _get_hash_service_args(*_args, **_kwargs):
                return ''

            self._get_hash_service_args = _get_hash_service_args
        self._service_results_cache[command] = {
            'hash': self._get_hash_service_args(command, first, *args, **kwargs),
            'result': pv_executed,
            'last_provider': last_provider.name if last_provider else '',
        }
        return pv_executed, last_provider.name if last_provider else ''
