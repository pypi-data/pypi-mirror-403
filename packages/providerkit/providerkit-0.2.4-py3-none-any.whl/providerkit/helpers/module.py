from __future__ import annotations

import importlib
import importlib.util
import inspect
from pathlib import Path
from typing import Any

from providerkit.kit import ProviderBase


def _build_module_path(
    py_file: Path,
    dir_path_obj: Path,
    base_module: str,
) -> str:
    if dir_path_obj.is_absolute():
        relative_path = py_file.relative_to(dir_path_obj)
    else:
        cwd = Path.cwd()
        abs_dir = (cwd / dir_path_obj).resolve()
        abs_file = py_file.resolve()
        relative_path = abs_file.relative_to(abs_dir)

    module_parts = list(relative_path.parts[:-1]) + [py_file.stem]
    return f'{base_module}.{".".join(module_parts)}'


def _get_module_path_from_file(py_file: Path) -> str | None:
    spec = importlib.util.spec_from_file_location(py_file.stem, py_file)
    if spec is None or spec.loader is None:
        return None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.__name__


def _extract_providers_from_module(
    module: Any,
    module_path: str,
) -> dict[str, type[ProviderBase]]:
    providers: dict[str, type[ProviderBase]] = {}
    for name, obj in inspect.getmembers(module, inspect.isclass):
        if (
            obj is not ProviderBase
            and issubclass(obj, ProviderBase)
            and obj.__module__ == module_path
            and 'Provider' in name
        ):
            provider_name = getattr(obj, 'name', '').lower()
            if provider_name:
                providers[provider_name] = obj
    return providers


def _infer_base_module(dir_path_obj: Path) -> str | None:
    if dir_path_obj.is_absolute():
        cwd = Path.cwd()
        try:
            relative_path = dir_path_obj.relative_to(cwd)
            return str(relative_path).replace('/', '.').replace('\\', '.')
        except ValueError:
            return None
    return str(dir_path_obj).replace('/', '.').replace('\\', '.')
