"""Test configuration for alphabet providers.

This test module loads providers from .alphabet.json and tests the configuration.
"""

from __future__ import annotations

import os
from pathlib import Path

import pytest

from providerkit import load_providers_from_json, get_providers


def _get_alphabet_json_path() -> Path | None:
    """Get path to alphabet.json configuration file.

    Returns:
        Path to alphabet.json if found, None otherwise.
    """
    config_paths = [
        Path(".alphabet.json"),
        Path("alphabet.json"),
        Path.home() / ".alphabet.json",
        Path("tests/alphabet.json"),
        Path("tests/.alphabet.json"),
    ]

    for config_path in config_paths:
        if config_path.exists():
            return config_path
    return None


def test_alphabet_json_exists() -> None:
    """Test that alphabet.json configuration file exists."""
    json_path = _get_alphabet_json_path()
    assert json_path is not None, "alphabet.json file not found in expected locations"
    assert json_path.exists(), f"alphabet.json path {json_path} does not exist"


def test_load_providers_from_json() -> None:
    """Test loading providers from alphabet.json."""
    providers = load_providers_from_json(lib_name="alphabet")

    assert len(providers) > 0, "No providers loaded from alphabet.json"

    expected_providers = [
        "china_alphabet",
        "japan_alphabet",
        "france_alphabet",
        "spain_alphabet",
        "arabic_alphabet",
        "swahili_alphabet",
    ]

    provider_names = list(providers.keys())
    for expected_name in expected_providers:
        assert expected_name in provider_names, f"Provider {expected_name} not found in loaded providers"


def test_provider_configuration() -> None:
    """Test that each provider has correct configuration."""
    providers = load_providers_from_json(lib_name="alphabet")

    china_provider = providers.get("china_alphabet")
    assert china_provider is not None
    assert china_provider.config_keys == ["CHINA_API_KEY", "CHINA_API_SECRET", "CHINA_ENCODING"]
    assert "CHINA_ENCODING" in china_provider.config
    assert china_provider.config["CHINA_ENCODING"] == "UTF-8"

    japan_provider = providers.get("japan_alphabet")
    assert japan_provider is not None
    assert japan_provider.config_keys == ["JAPAN_API_KEY", "JAPAN_API_TOKEN", "JAPAN_CHARSET"]

    france_provider = providers.get("france_alphabet")
    assert france_provider is not None
    assert france_provider.config_keys == ["FRANCE_API_KEY", "FRANCE_LOCALE", "FRANCE_DIACRITICS"]
    assert france_provider.config["FRANCE_LOCALE"] == "fr_FR"

    spain_provider = providers.get("spain_alphabet")
    assert spain_provider is not None
    assert spain_provider.config_keys == ["SPAIN_API_KEY", "SPAIN_REGION", "SPAIN_ENCODING"]

    arabic_provider = providers.get("arabic_alphabet")
    assert arabic_provider is not None
    assert arabic_provider.config_keys == ["ARABIC_API_KEY", "ARABIC_DIRECTION", "ARABIC_SCRIPT"]
    assert arabic_provider.config["ARABIC_DIRECTION"] == "rtl"

    swahili_provider = providers.get("swahili_alphabet")
    assert swahili_provider is not None
    assert swahili_provider.config_keys == ["SWAHILI_API_KEY", "SWAHILI_COUNTRY", "SWAHILI_DIALECT"]
    assert swahili_provider.config["SWAHILI_COUNTRY"] == "tanzania"


def test_provider_urls() -> None:
    """Test that each provider has URLs configured."""
    providers = load_providers_from_json(lib_name="alphabet")

    for name, provider in providers.items():
        assert provider.site_url is not None, f"Provider {name} has no site_url"
        assert provider.documentation_url is not None, f"Provider {name} has no documentation_url"
        assert provider.status_url is not None, f"Provider {name} has no status_url"

        if hasattr(provider, 'get_urls'):
            urls = provider.get_urls()
            assert "site" in urls
            assert "documentation" in urls
            assert "status" in urls


def test_provider_required_packages() -> None:
    """Test that each provider has required packages configured."""
    providers = load_providers_from_json(lib_name="alphabet")

    for name, provider in providers.items():
        packages = provider.get_required_packages()
        assert len(packages) > 0, f"Provider {name} has no required packages"
        assert isinstance(packages, list), f"Provider {name} required_packages is not a list"


def test_provider_services() -> None:
    """Test that each provider has services configured and implemented."""
    providers = load_providers_from_json(lib_name="alphabet")

    for name, provider in providers.items():
        services = provider.get_required_services()
        assert len(services) > 0, f"Provider {name} has no services"
        assert "get_alphabet" in services, f"Provider {name} does not have get_alphabet service"

        assert provider.are_services_implemented(), f"Provider {name} services are not all implemented"
        assert provider.is_service_implemented("get_alphabet"), f"Provider {name} get_alphabet service is not implemented"


def test_provider_get_alphabet() -> None:
    """Test that each provider can retrieve alphabet."""
    providers = load_providers_from_json(lib_name="alphabet")

    for name, provider in providers.items():
        alphabet = provider.get_alphabet()
        assert isinstance(alphabet, list), f"Provider {name} get_alphabet() does not return a list"
        assert len(alphabet) > 0, f"Provider {name} get_alphabet() returns empty list"


def test_get_providers_with_lib_name() -> None:
    """Test get_providers function with lib_name parameter."""
    json_path = _get_alphabet_json_path()
    if json_path is None:
        pytest.skip(".alphabet.json file not found")

    providers = get_providers(lib_name="alphabet")

    assert len(providers) > 0, "No providers loaded using get_providers(lib_name='alphabet')"

    provider_names = [p.name for p in providers]
    assert "china_alphabet" in provider_names
    assert "japan_alphabet" in provider_names
    assert "france_alphabet" in provider_names
    assert "spain_alphabet" in provider_names
    assert "arabic_alphabet" in provider_names
    assert "swahili_alphabet" in provider_names


def test_provider_names_and_display_names() -> None:
    """Test that providers have proper names and display names."""
    providers = load_providers_from_json(lib_name="alphabet")

    for name, provider in providers.items():
        assert provider.name is not None and provider.name != "", f"Provider {name} has no name"
        assert provider.display_name is not None and provider.display_name != "", f"Provider {name} has no display_name"
        assert provider.name == name, f"Provider name mismatch: expected {name}, got {provider.name}"

