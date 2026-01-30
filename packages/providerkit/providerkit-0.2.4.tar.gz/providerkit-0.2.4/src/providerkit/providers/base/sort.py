from typing import Any

from providerkit.kit import ProviderBase


class _ReverseOrder:
    """Wrapper to reverse sort order."""

    def __init__(self, value: Any):
        self.value = value

    def __lt__(self, other: Any) -> bool:
        if isinstance(other, _ReverseOrder):
            return bool(self.value > other.value)
        return bool(self.value > other)

    def __gt__(self, other: Any) -> bool:
        if isinstance(other, _ReverseOrder):
            return bool(self.value < other.value)
        return bool(self.value < other)

    def __eq__(self, other: Any) -> bool:
        if isinstance(other, _ReverseOrder):
            return bool(self.value == other.value)
        return bool(self.value == other)

    def __le__(self, other: Any) -> bool:
        return self.__lt__(other) or self.__eq__(other)

    def __ge__(self, other: Any) -> bool:
        return self.__gt__(other) or self.__eq__(other)


class ProviderListSort:
    """Sort providers."""

    def _get_sort_key(
        self, provider: ProviderBase, order_by: list[str] | None = None
    ) -> tuple[tuple[int, Any], ...]:
        """Get sort key for a provider."""
        if order_by is None:
            order_by = ['priority', 'name']
        key_parts: list[tuple[int, Any]] = []
        for attr_name in order_by:
            reverse = attr_name.startswith('-')
            actual_attr_name = attr_name[1:] if reverse else attr_name
            attr_value = getattr(provider, actual_attr_name, None)
            if callable(attr_value):
                try:
                    attr_value = attr_value()
                except Exception:
                    attr_value = None
            if attr_value is None:
                key_parts.append((1, None))
            else:
                if reverse:
                    if isinstance(attr_value, (int, float)):
                        attr_value = -attr_value
                    else:
                        attr_value = _ReverseOrder(attr_value)
                key_parts.append((0, attr_value))
        return tuple(key_parts)

    def sort_providers(
        self, providers: list[ProviderBase], order_by: list[str] | None = None
    ) -> list[ProviderBase]:
        """Sort providers."""
        return sorted(providers, key=lambda p: self._get_sort_key(p, order_by))
