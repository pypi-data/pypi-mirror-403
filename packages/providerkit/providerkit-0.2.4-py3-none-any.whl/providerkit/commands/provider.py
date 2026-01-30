"""Provider command for listing and filtering providers."""

from __future__ import annotations

import sys
from typing import Any, cast

from qualitybase.cli import _get_package_name as _get_package_name_from_context  # noqa: TID252
from qualitybase.commands import parse_args_from_config
from qualitybase.commands.base import Command
from qualitybase.services.utils import print_header, print_separator

from providerkit.helpers import get_providerkit

# Parser arguments configuration
_PROVIDER_COMMAND_CONFIG = {
    'format': {'type': str, 'default': 'terminal'},
    'first': {'type': 'store_true'},
    'raw': {'type': 'store_true'},
    'filter': {'type': str},
    'backend': {'type': str},
    'attr': {'type': str, 'nargs': '*', 'default': []},
}

_ARG_CONFIG = {
    **_PROVIDER_COMMAND_CONFIG,
    'command': {'type': str, 'nargs': '*', 'default': []},
    'dir': {'type': str},
    'json': {'type': str},
}


def _parse_all_args(args: list[str]) -> dict[str, Any]:
    result = parse_args_from_config(args, _ARG_CONFIG, prog='provider')
    return cast('dict[str, Any]', result)


def _execute_command(
    command: str,
    first: bool,
    raw: bool,
    output_format: str,
    additional_args: dict[str, str | bool],
) -> None:
    """Execute the provider command."""
    package_name = _get_package_name_from_context()
    pvk = get_providerkit(**additional_args)

    if command in ['get_providers', 'get_config', 'get_package', 'get_service', 'get_urls']:
        pvk.call_service(command, lib_name=package_name, **additional_args)
        print(pvk.response(command, raw, format=output_format))
    else:
        pvk.execute_providers(command, first, **additional_args)

        for pv in pvk.get_service_result(command):
            provider = pv['provider']
            print_separator()
            print_header(provider.name)
            print_separator()
            print(provider.response(command, raw, format=output_format))
            print()


def _provider_command(args: list[str]) -> bool:  # noqa: C901
    """Execute provider command with parsed arguments."""
    parsed = _parse_all_args(args)

    if not parsed:
        return False

    output_format = parsed.get('format', 'terminal')

    command: str = 'get_providers'
    additional_args: dict[str, Any] = {}

    if 'command' in parsed:
        cmd_data = parsed['command']
        if isinstance(cmd_data, dict) and 'args' in cmd_data:
            if cmd_data['args']:
                command = cmd_data['args'][0]
                if len(cmd_data['args']) > 1:
                    additional_args['query'] = cmd_data['args'][1]
                for arg in cmd_data['args'][2:]:
                    additional_args[arg] = True
            additional_args.update(cmd_data.get('kwargs', {}))

    first = parsed.get('first', False)
    raw = parsed.get('raw', False)

    if 'dir' in parsed:
        dir_val = parsed['dir']
        if isinstance(dir_val, str):
            additional_args['dir_path'] = dir_val

    if 'json' in parsed:
        json_val = parsed['json']
        if isinstance(json_val, str):
            additional_args['json'] = json_val

    if 'filter' in parsed:
        filter_val = parsed['filter']
        if isinstance(filter_val, str):
            additional_args['query'] = filter_val
    elif 'backend' in parsed:
        backend_val = parsed['backend']
        if isinstance(backend_val, str):
            additional_args['query'] = backend_val

    attribute_search: dict[str, str] = {}
    if 'attr' in parsed:
        attr_data = parsed['attr']
        if isinstance(attr_data, dict):
            if attr_data.get('args'):
                print(
                    'Invalid attribute format: positional arguments not allowed. Expected format: key=value', file=sys.stderr
                )
                return False
            kwargs_data = attr_data.get('kwargs', {})
            attribute_search = cast('dict[str, str]', kwargs_data) if isinstance(kwargs_data, dict) else {}
            additional_args['attribute_search'] = attribute_search

    _execute_command(command, first, raw, output_format, additional_args,)
    return True


provider_command = Command(
    _provider_command, 'List and filter providers (use --list [query] --format [terminal|json|xml])'
)
