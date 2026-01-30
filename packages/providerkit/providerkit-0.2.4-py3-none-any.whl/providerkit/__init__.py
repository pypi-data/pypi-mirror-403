"""ProviderKit - Generic provider management library."""

__version__ = '0.2.3'

from .cli import main
from .helpers import get_providers
from .helpers.load import (
    autodiscover_providers,
    load_providers_from_config,
    load_providers_from_json,
)
from .kit import ProviderBase
from .kit.config import ConfigMixin
from .kit.cost import CostMixin
from .kit.package import PackageMixin
from .kit.urls import UrlsMixin

PROVIDERKIT_FIELDS_BACKEND = {
    "backend": {
        "label": "Backend display name",
        "description": "Backend display name",
        "format": "str",
    },
    "backend_name": {
        "label": "Simple backend name (e.g., nominatim)",
        "description": "Simple backend name (e.g., nominatim)",
        "format": "str",
    },
}

__all__ = [
    'ProviderBase',
    'ConfigMixin',
    'CostMixin',
    'PackageMixin',
    'UrlsMixin',
    'autodiscover_providers',
    'get_providers',
    'load_providers_from_config',
    'load_providers_from_json',
    'main',
]
