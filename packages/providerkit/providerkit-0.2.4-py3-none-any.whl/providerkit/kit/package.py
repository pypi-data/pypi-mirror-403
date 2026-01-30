"""Package dependency management mixin for providers."""

from __future__ import annotations

import importlib
import importlib.util
import sys
from typing import Any, cast

FIELDS_PACKAGE_BASE = {
    'package_status_str': {
        'label': 'Package status',
        'description': 'Package status',
        'format': 'str',
    },
    'required_packages': {
        'label': 'Required packages',
        'description': 'Required packages',
        'format': 'list',
    },
    'missing_packages': {
        'label': 'Missing packages',
        'description': 'Missing packages',
        'format': 'list',
    },
    'are_packages_installed': {
        'label': 'Are packages installed',
        'description': 'Are packages installed',
        'format': 'bool',
    },
}


class PackageMixin:
    """Mixin for managing required packages and checking their installation."""

    required_packages: list[str] = []
    package_authorized: list[str] = [
        'check_packages',
        'get_required_packages',
        'get_missing_packages',
    ]

    def get_required_packages(self) -> list[str]:
        """Get required packages."""
        return getattr(self, 'required_packages', [])

    def is_package_installed(self, package_name: str) -> bool:
        """Check if package is installed."""
        normalized_name = package_name.replace('-', '_').replace('.', '_')

        try:
            spec = importlib.util.find_spec(normalized_name)
            if spec is None:
                spec = importlib.util.find_spec(package_name)
            return spec is not None
        except (ImportError, ModuleNotFoundError, ValueError):
            return False

    def check_packages(self) -> dict[str, bool]:
        """Check installation status of all required packages."""
        if hasattr(self, '_packages_cache'):
            cached = getattr(self, '_packages_cache', {})
            return cast('dict[str, bool]', cached)

        packages = self.get_required_packages()
        status: dict[str, bool] = {pkg: self.is_package_installed(pkg) for pkg in packages}
        self._packages_cache = status
        return status

    def clear_packages_cache(self) -> None:
        """Clear cached package check results."""
        if hasattr(self, '_packages_cache'):
            delattr(self, '_packages_cache')

    def are_packages_installed(self) -> bool:
        """Check if all required packages are installed."""
        status = self.check_packages()
        return all(status.values())

    def get_missing_packages(self) -> list[str]:
        """Get list of missing packages."""
        status = self.check_packages()
        return [pkg for pkg, installed in status.items() if not installed]

    @property
    def missing_packages(self) -> list[str]:
        """Get list of missing packages."""
        return self.get_missing_packages()

    @classmethod
    def _import_single_package(
        cls, package_name: str, globals_dict: dict[str, Any] | None = None
    ) -> None:
        """Import a single package with normalized name fallback."""
        normalized_name = package_name.replace('-', '_').replace('.', '_')

        try:
            module = importlib.import_module(normalized_name)  # nosec B307
            sys.modules[package_name] = module
            if globals_dict is not None:
                globals_dict[package_name] = module
                globals_dict[normalized_name] = module
        except (ImportError, ModuleNotFoundError):
            try:
                module = importlib.import_module(package_name)  # nosec B307
                sys.modules[normalized_name] = module
                if globals_dict is not None:
                    globals_dict[package_name] = module
                    globals_dict[normalized_name] = module
            except (ImportError, ModuleNotFoundError):
                pass

    @classmethod
    def safe_import_packages(
        cls, packages: list[str], globals_dict: dict[str, Any] | None = None
    ) -> None:
        """Import packages safely at module level."""
        for package_name in packages:
            cls._import_single_package(package_name, globals_dict)

    def safe_import(self, globals_dict: dict[str, Any] | None = None) -> None:
        """Import required packages safely, skipping those that are not installed."""
        packages = self.get_required_packages()
        for package_name in packages:
            self._import_single_package(package_name, globals_dict)

    @property
    def package_status_str(self) -> str:
        """Get status of packages."""
        if self.are_packages_installed():
            return '✓'
        packages = self.get_required_packages()
        if not packages:
            return 'N/A'
        installed_count = sum(1 for package in packages if self.is_package_installed(package))
        total_count = len(packages)
        if installed_count == total_count:
            return '✓'
        return f'{installed_count}/{total_count}'
