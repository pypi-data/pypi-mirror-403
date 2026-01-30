from __future__ import annotations

import importlib
import importlib.util
import inspect
import json
import sys
from pathlib import Path
from typing import Any

from providerkit.kit import ProviderBase

from .module import (
    _build_module_path,
    _extract_providers_from_module,
    _infer_base_module,
)


def load_providers_from_json(
    json_path: str | Path | dict[str, Any] | None = None,
    *,
    lib_name: str = 'providerkit',
    search_paths: list[str | Path] | None = None,
) -> dict[str, ProviderBase]:
    if isinstance(json_path, dict):
        return _load_providers_from_config(json_path.get('providers', []))

    json_file = json_path
    if json_file is None:
        if search_paths is None:
            search_paths = [
                Path(f'.{lib_name}.json'),
                Path(f'{lib_name}.json'),
                Path.home() / f'.{lib_name}.json',
                Path(f'tests/{lib_name}.json'),
                Path(f'tests/.{lib_name}.json'),
            ]
        else:
            search_paths = [Path(p) if not isinstance(p, Path) else p for p in search_paths]

        for path_obj in search_paths:
            path_obj_path = Path(path_obj) if isinstance(path_obj, str) else path_obj
            if path_obj_path.exists():
                json_file = path_obj_path
                break
        else:
            return {}

    if json_file is None:
        return {}

    try:
        with open(json_file, encoding='utf-8') as f:
            config = json.load(f)
    except (json.JSONDecodeError, OSError):
        return {}

    return _load_providers_from_config(
        config.get('providers', []) if isinstance(config, dict) else config
    )


def load_providers_from_config(config: list[dict[str, Any]]) -> dict[str, ProviderBase]:
    return _load_providers_from_config(config)


def _load_providers_from_config(config: list[dict[str, Any]]) -> dict[str, ProviderBase]:
    providers: dict[str, ProviderBase] = {}

    for provider_config in config:
        class_path = provider_config.get('class', '')
        if not class_path:
            continue

        try:
            parts = class_path.split('.')
            module_path = '.'.join(parts[:-1])
            class_name = parts[-1]
            module = importlib.import_module(module_path)  # nosec B307
            provider_class = getattr(module, class_name)

            if not issubclass(provider_class, ProviderBase):
                continue

            config_dict = provider_config.get('config', {})
            provider_instance = provider_class(
                config=config_dict, **provider_config.get('kwargs', {})
            )

            provider_name = getattr(provider_instance, 'name', '').lower()
            if provider_name:
                providers[provider_name] = provider_instance
        except (ImportError, AttributeError, TypeError):
            continue

    return providers


def autodiscover_providers(  # noqa: C901
    dir_path: str | Path,
    *,
    base_module: str | None = None,
    exclude_files: list[str] | None = None,
) -> dict[str, type[ProviderBase]]:
    if exclude_files is None:
        exclude_files = ['__init__.py', 'base.py']

    dir_path_obj = Path(dir_path)
    if not dir_path_obj.exists() or not dir_path_obj.is_dir():
        return {}

    providers: dict[str, type[ProviderBase]] = {}

    if base_module is None:
        inferred_base = _infer_base_module(dir_path_obj)
        if inferred_base:
            base_module = inferred_base
            cwd = Path.cwd()
            if str(cwd) not in sys.path:
                sys.path.insert(0, str(cwd))

    for py_file in dir_path_obj.rglob('*.py'):
        if py_file.name in exclude_files or py_file.name.startswith('_'):
            continue

        try:
            if base_module:
                module_path = _build_module_path(py_file, dir_path_obj, base_module)
                module = importlib.import_module(module_path)  # nosec B307
            else:
                spec = importlib.util.spec_from_file_location(py_file.stem, py_file)
                if spec is None or spec.loader is None:
                    continue
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)
                module_path = module.__name__

            found_providers = _extract_providers_from_module(module, module_path)
            providers.update(found_providers)
        except (ImportError, AttributeError, TypeError, ValueError):
            continue

    return providers


def load_providers_from_dir(
    dir_path: str | Path,
    base_module: str | None = None,
) -> dict[str, ProviderBase]:
    dir_path_obj = Path(dir_path).resolve()
    if not dir_path_obj.exists():
        raise FileNotFoundError(f'Directory not found: {dir_path}')
    if not dir_path_obj.is_dir():
        raise NotADirectoryError(f'Path is not a directory: {dir_path}')

    provider_classes = autodiscover_providers(dir_path, base_module=base_module)
    providers: dict[str, ProviderBase] = {}
    for name, provider_class in provider_classes.items():
        try:
            provider_file = Path(inspect.getfile(provider_class)).resolve()
            relative_path = provider_file.relative_to(dir_path_obj)
            provider_instance = provider_class(path=str(relative_path))
            setattr(provider_instance, 'class_name', provider_class.__name__)  # noqa: B010
            setattr(provider_instance, 'class_path', provider_class.__module__)  # noqa: B010
            providers[name] = provider_instance
        except (TypeError, ValueError):
            continue
    return providers


def _find_package_providers_dir(lib_name: str) -> Path | None:
    try:
        package_module = importlib.import_module(lib_name)  # nosec B307
        if hasattr(package_module, '__file__') and package_module.__file__:
            package_dir = Path(package_module.__file__).parent
            providers_dir = package_dir / 'providers'
            if providers_dir.exists() and providers_dir.is_dir():
                return providers_dir
    except (ImportError, AttributeError):
        pass
    return None


def load_providers_from_package(
    lib_name: str, base_module: str | None = None
) -> dict[str, ProviderBase]:
    providers_dir = _find_package_providers_dir(lib_name)
    if providers_dir:
        if base_module is None:
            base_module = f'{lib_name}.providers'
        return load_providers_from_dir(providers_dir, base_module)
    return {}
