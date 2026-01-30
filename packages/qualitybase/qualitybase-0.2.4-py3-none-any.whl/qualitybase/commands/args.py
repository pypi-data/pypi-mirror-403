"""Command-line argument parsing utilities."""

from __future__ import annotations

import argparse
import sys
from typing import Any


def create_parser_from_config(
    config: dict[str, dict[str, Any]], prog: str = 'command', add_help: bool = False
) -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog=prog, add_help=add_help, allow_abbrev=False)

    for arg_name, arg_config in config.items():
        arg_type = arg_config.get('type')
        default = arg_config.get('default')
        nargs = arg_config.get('nargs')

        if arg_type == 'store_true':
            parser.add_argument(f'--{arg_name}', action='store_true', default=default or False)
        else:
            kwargs: dict[str, Any] = {}
            if arg_type:
                kwargs['type'] = arg_type
            if default is not None:
                kwargs['default'] = default
            if nargs:
                kwargs['nargs'] = nargs

            parser.add_argument(f'--{arg_name}', **kwargs)

    return parser


def classify_args(values: list[str]) -> dict[str, list[str] | dict[str, str]]:
    args_list: list[str] = []
    kwargs_dict: dict[str, str] = {}

    for value in values:
        if '=' in value:
            key, val = value.split('=', 1)
            kwargs_dict[key] = val
        else:
            args_list.append(value)

    return {'args': args_list, 'kwargs': kwargs_dict}


def parse_args_from_config(
    args: list[str], config: dict[str, dict[str, Any]], prog: str = 'command'
) -> dict[str, Any]:
    parser = create_parser_from_config(config, prog=prog)
    
    try:
        parsed, unknown = parser.parse_known_args(args)
    except SystemExit:
        return {}
    
    result: dict[str, Any] = {}
    
    for arg_name in config.keys():
        value = getattr(parsed, arg_name, None)
        arg_config = config[arg_name]
        
        if value is None:
            continue
        
        has_nargs = 'nargs' in arg_config and arg_config['nargs'] is not None
            
        if isinstance(value, list):
            if has_nargs:
                if value:
                    result[arg_name] = classify_args(value)
            else:
                result[arg_name] = value
        elif isinstance(value, bool):
            if value:
                result[arg_name] = True
        else:
            if has_nargs:
                result[arg_name] = {'args': [value], 'kwargs': {}}
            else:
                result[arg_name] = value
    
    return result
