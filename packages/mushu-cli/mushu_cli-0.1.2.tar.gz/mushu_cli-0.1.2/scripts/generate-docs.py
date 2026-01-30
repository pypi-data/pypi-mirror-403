#!/usr/bin/env python3
"""
Generate CLI documentation JSON from Typer app.

This script introspects the Typer CLI and outputs a JSON structure
suitable for the docs site.

Usage: python scripts/generate-docs.py > ../mushu-admin/src/data/cli-docs.json
"""

import json
import sys
from pathlib import Path

# Add the parent directory to the path so we can import mushu
sys.path.insert(0, str(Path(__file__).parent.parent))

from mushu.cli import app
import typer
from typer.main import get_command


def extract_option_info(param) -> dict:
    """Extract option information from a click parameter."""
    if hasattr(param, 'opts'):
        flags = ', '.join(param.opts)
    else:
        flags = f'--{param.name}'

    return {
        'flag': flags,
        'description': param.help or '',
        'required': param.required if hasattr(param, 'required') else False,
    }


def extract_argument_info(param) -> dict:
    """Extract argument information from a click parameter."""
    return {
        'name': param.name,
        'description': param.help if hasattr(param, 'help') else '',
        'required': param.required if hasattr(param, 'required') else True,
    }


def extract_command_info(cmd, prefix: str = '') -> dict:
    """Extract information about a command."""
    usage = f"mushu {prefix}{cmd.name}".strip()

    # Get arguments and options
    arguments = []
    options = []

    for param in cmd.params:
        if isinstance(param, typer.core.TyperArgument):
            arg_info = extract_argument_info(param)
            arguments.append(arg_info)
            if arg_info.get('required', True):
                usage += f" <{param.name}>"
            else:
                usage += f" [{param.name}]"
        elif isinstance(param, typer.core.TyperOption):
            opt_info = extract_option_info(param)
            options.append(opt_info)

    result = {
        'name': cmd.name,
        'description': cmd.help or '',
        'usage': usage,
    }

    if arguments:
        result['arguments'] = arguments
    if options:
        result['options'] = options

    return result


def extract_group_info(group, name: str) -> dict:
    """Extract information about a command group."""
    commands = []

    click_cmd = get_command(group)

    if hasattr(click_cmd, 'commands'):
        for cmd_name, cmd in click_cmd.commands.items():
            cmd_info = extract_command_info(cmd, prefix=f"{name} ")
            commands.append(cmd_info)

    return {
        'name': name,
        'description': group.info.help or '',
        'commands': commands,
    }


def main():
    """Generate CLI documentation JSON."""
    click_app = get_command(app)

    # Global commands (not in a group)
    global_commands = []
    groups = []

    for name, cmd in click_app.commands.items():
        if hasattr(cmd, 'commands'):
            # This is a group (sub-typer)
            # Find the corresponding typer app
            for registered in app.registered_groups:
                if registered.name == name:
                    group_info = extract_group_info(registered.typer_instance, name)
                    groups.append(group_info)
                    break
        else:
            # This is a direct command
            cmd_info = extract_command_info(cmd)
            global_commands.append(cmd_info)

    output = {
        'name': 'mushu',
        'description': 'Mushu CLI - Authentication and push notifications for your apps',
        'install': 'pip install mushu-cli',
        'globalCommands': global_commands,
        'groups': groups,
    }

    print(json.dumps(output, indent=2))


if __name__ == '__main__':
    main()
