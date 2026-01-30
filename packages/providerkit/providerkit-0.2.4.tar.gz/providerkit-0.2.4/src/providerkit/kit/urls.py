"""URL management mixin for providers."""

from __future__ import annotations

FIELDS_URLS_BASE = {
    'documentation_url': {
        'label': 'Documentation URL',
        'description': 'Documentation URL',
        'format': 'url',
    },
    'site_url': {'label': 'Site URL', 'description': 'Site URL', 'format': 'url'},
    'status_url': {'label': 'Status URL', 'description': 'Status URL', 'format': 'url'},
}


class UrlsMixin:
    """Mixin for managing provider URLs."""

    documentation_url: str | None = None
    site_url: str | None = None
    status_url: str | None = None
    urls_authorized: list[str] = [
        'get_documentation_url',
        'get_site_url',
        'get_status_url',
    ]

    def get_documentation_url(self) -> str | None:
        """Get documentation URL."""
        return getattr(self, 'documentation_url', None)

    def get_site_url(self) -> str | None:
        """Get website URL."""
        return getattr(self, 'site_url', None)

    def get_status_url(self) -> str | None:
        """Get status page URL."""
        return getattr(self, 'status_url', None)

    @property
    def urls(self) -> dict[str, str | None]:
        """Get all URLs."""
        return {
            'documentation': self.get_documentation_url(),
            'site': self.get_site_url(),
            'status': self.get_status_url(),
        }
