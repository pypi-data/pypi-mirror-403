"""
prmpt command-line interface.

Usage:
    prmpt validate <file>...
    prmpt resolve <file> [--output <path>]
    prmpt info <file>
    prmpt prompt <file>
"""

import argparse
import sys
from pathlib import Path

from .contract import Contract
from .validator import validate, parse_file
from .resolver import resolve_to_json
from .exceptions import ParseError, ValidationError


def cmd_validate(args) -> int:
    """Validate one or more .prmpt files."""
    exit_code = 0

    for filepath in args.files:
        path = Path(filepath)

        if not path.exists():
            print(f"✗ {filepath}: File not found", file=sys.stderr)
            exit_code = 1
            continue

        try:
            errors = validate(path)
            if errors:
                print(f"✗ {filepath}:", file=sys.stderr)
                for error in errors:
                    print(f"  - {error}", file=sys.stderr)
                exit_code = 1
            else:
                print(f"✓ {filepath}")
        except ParseError as e:
            print(f"✗ {filepath}: {e}", file=sys.stderr)
            exit_code = 1

    return exit_code


def cmd_resolve(args) -> int:
    """Resolve a .prmpt file to canonical JSON."""
    path = Path(args.file)

    if not path.exists():
        print(f"Error: File not found: {path}", file=sys.stderr)
        return 1

    try:
        json_output = resolve_to_json(path)

        if args.output:
            Path(args.output).write_text(json_output, encoding='utf-8')
            print(f"✓ Resolved to {args.output}")
        else:
            print(json_output, end='')

        return 0

    except (ParseError, ValidationError) as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1


def cmd_info(args) -> int:
    """Show information about a .prmpt contract."""
    path = Path(args.file)

    if not path.exists():
        print(f"Error: File not found: {path}", file=sys.stderr)
        return 1

    try:
        contract = Contract.load(path)

        print(f"Contract: {contract.name}")
        print(f"Version:  {contract.version}")

        if contract.spec_version:
            print(f"Spec Version: {contract.spec_version}")
            warning = contract.check_spec_compatibility()
            if warning:
                print(f"  ⚠️  {warning}")

        if contract.description:
            print(f"Description: {contract.description}")

        if contract.target_model:
            print(f"Target Model: {contract.target_model}")

        print()
        print(f"Scope: {contract.scope.get('description', 'N/A')}")

        print()
        print(f"Constraints:")
        print(f"  Invariants: {len(contract.invariants)}")
        print(f"  Allowed Actions: {len(contract.allowed_actions)}")
        print(f"  Forbidden Actions: {len(contract.forbidden_actions)}")
        print(f"  Failure Modes: {len(contract.failure_modes)}")

        if contract.handoff_rules:
            print(f"  Handoff Rules: Yes")
        else:
            print(f"  Handoff Rules: No")

        print()
        print(f"Output Format: {contract.outputs.get('format', 'text')}")

        return 0

    except (ParseError, ValidationError) as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1


def cmd_prompt(args) -> int:
    """Generate a system prompt from a .prmpt contract."""
    path = Path(args.file)

    if not path.exists():
        print(f"Error: File not found: {path}", file=sys.stderr)
        return 1

    try:
        contract = Contract.load(path)
        print(contract.to_system_prompt())
        return 0

    except (ParseError, ValidationError) as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1


def main(argv=None) -> int:
    """Main entry point for the prmpt CLI."""
    parser = argparse.ArgumentParser(
        prog='prmpt',
        description='prmpt - System-enforced LLM contracts',
    )
    parser.add_argument(
        '--version',
        action='version',
        version='prmpt 0.1.0 (spec v0.1.0)'
    )

    subparsers = parser.add_subparsers(dest='command', help='Commands')

    # validate command
    validate_parser = subparsers.add_parser(
        'validate',
        help='Validate .prmpt files'
    )
    validate_parser.add_argument(
        'files',
        nargs='+',
        help='Files to validate'
    )

    # resolve command
    resolve_parser = subparsers.add_parser(
        'resolve',
        help='Resolve to canonical JSON'
    )
    resolve_parser.add_argument(
        'file',
        help='File to resolve'
    )
    resolve_parser.add_argument(
        '-o', '--output',
        help='Output file (default: stdout)'
    )

    # info command
    info_parser = subparsers.add_parser(
        'info',
        help='Show contract information'
    )
    info_parser.add_argument(
        'file',
        help='Contract file'
    )

    # prompt command
    prompt_parser = subparsers.add_parser(
        'prompt',
        help='Generate system prompt'
    )
    prompt_parser.add_argument(
        'file',
        help='Contract file'
    )

    args = parser.parse_args(argv)

    if args.command is None:
        parser.print_help()
        return 0

    if args.command == 'validate':
        return cmd_validate(args)
    elif args.command == 'resolve':
        return cmd_resolve(args)
    elif args.command == 'info':
        return cmd_info(args)
    elif args.command == 'prompt':
        return cmd_prompt(args)

    return 0


if __name__ == '__main__':
    sys.exit(main())
