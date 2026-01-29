"""
Command definitions for dbgear-doc plugin.

This module provides CLI subcommand registration and execution
for the dbgear documentation plugin.
"""

import logging
from pathlib import Path

from .generator import generate_docs
from .er_diagram import generate_svg, generate_drawio


def register_commands(subparsers):
    """
    Register all subcommands provided by this plugin.

    Args:
        subparsers: argparse subparsers object from the main CLI.

    Returns:
        List of registered command names.
    """
    _register_doc_command(subparsers)
    _register_svg_command(subparsers)
    _register_drawio_command(subparsers)

    return ['doc', 'svg', 'drawio']


def execute(args, project):
    """
    Execute the specified subcommand.

    Args:
        args: Parsed command line arguments.
        project: The loaded project object.

    Returns:
        True if execution was successful, False otherwise.
    """
    schema_path = Path(project.folder) / 'schema.yaml'

    if not schema_path.exists():
        logging.error(f'schema.yaml not found: {schema_path}')
        return False

    if args.command == 'doc':
        return _execute_doc(args, schema_path)
    elif args.command == 'svg':
        return _execute_svg(args, schema_path)
    elif args.command == 'drawio':
        return _execute_drawio(args, schema_path)

    return False


def _register_doc_command(subparsers):
    """Register the doc subcommand."""
    parser = subparsers.add_parser('doc', help='generate documentation from schema')
    parser.add_argument(
        '-o', '--output',
        default='./docs',
        help='output path: directory for default/table scope, file path for schema scope'
    )
    parser.add_argument(
        '--template',
        help='custom Jinja2 template file path'
    )
    parser.add_argument(
        '--scope',
        choices=['schema', 'table'],
        default='table',
        help='data scope for custom template: schema (1 file, -o is file path) or table (per-table files)'
    )


def _register_svg_command(subparsers):
    """Register the svg subcommand."""
    parser = subparsers.add_parser('svg', help='generate ER diagram in SVG format')
    parser.add_argument(
        '-o', '--output',
        default='./er_diagram.svg',
        help='output file path (default: ./er_diagram.svg)'
    )
    parser.add_argument(
        '-s', '--schema',
        help='schema name (uses first schema if not specified)'
    )
    parser.add_argument(
        '-t', '--table',
        help='center table name (shows all tables if not specified)'
    )
    parser.add_argument(
        '--ref-level',
        type=int,
        default=1,
        help='levels of referencing tables to include (default: 1)'
    )
    parser.add_argument(
        '--fk-level',
        type=int,
        default=1,
        help='levels of referenced tables to include (default: 1)'
    )


def _register_drawio_command(subparsers):
    """Register the drawio subcommand."""
    parser = subparsers.add_parser('drawio', help='generate ER diagram in draw.io format')
    parser.add_argument(
        '-o', '--output',
        default='./er_diagram.drawio',
        help='output file path (default: ./er_diagram.drawio)'
    )
    parser.add_argument(
        '-s', '--schema',
        help='schema name (uses first schema if not specified)'
    )
    parser.add_argument(
        '-t', '--table',
        help='center table name (shows all tables if not specified)'
    )
    parser.add_argument(
        '--ref-level',
        type=int,
        default=1,
        help='levels of referencing tables to include (default: 1)'
    )
    parser.add_argument(
        '--fk-level',
        type=int,
        default=1,
        help='levels of referenced tables to include (default: 1)'
    )


def _execute_doc(args, schema_path):
    """Execute the doc command."""
    generated_files = generate_docs(
        schema_path=str(schema_path),
        output_dir=args.output,
        template=args.template,
        scope=args.scope,
    )
    logging.info(f'Generated {len(generated_files)} documentation files in {args.output}')
    return True


def _execute_svg(args, schema_path):
    """Execute the svg command."""
    generate_svg(
        schema_path=str(schema_path),
        output_path=args.output,
        schema_name=args.schema,
        table_name=args.table,
        ref_level=args.ref_level,
        fk_level=args.fk_level,
    )
    logging.info(f'Generated ER diagram: {args.output}')
    return True


def _execute_drawio(args, schema_path):
    """Execute the drawio command."""
    generate_drawio(
        schema_path=str(schema_path),
        output_path=args.output,
        schema_name=args.schema,
        table_name=args.table,
        ref_level=args.ref_level,
        fk_level=args.fk_level,
    )
    logging.info(f'Generated ER diagram: {args.output}')
    return True
