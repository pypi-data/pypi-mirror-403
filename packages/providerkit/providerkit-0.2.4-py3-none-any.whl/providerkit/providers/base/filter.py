from providerkit.kit import ProviderBase


class ProviderListFilter:
    def filter_providers(
        self, providers: list[ProviderBase], attr: dict[str, str]
    ) -> list[ProviderBase]:
        filtered = []
        for provider in providers:
            match = True
            for attr_name, filter_value in attr.items():
                attr_value = getattr(provider, attr_name, None)
                if callable(attr_value):
                    try:
                        attr_value = attr_value()
                    except Exception:
                        attr_value = None

                if attr_value is None:
                    match = False
                    break

                attr_str = str(attr_value).lower()
                filter_str = str(filter_value).lower()
                if filter_str not in attr_str:
                    match = False
                    break

            if match:
                filtered.append(provider)

        return filtered
