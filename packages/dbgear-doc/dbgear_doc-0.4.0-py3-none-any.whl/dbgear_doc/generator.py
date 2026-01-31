"""
Document Generator for DBGear schemas.

This module provides the core functionality for generating
documentation from database schema definitions using custom templates.
"""

from pathlib import Path

from jinja2 import Environment, FileSystemLoader

from dbgear.models.schema import SchemaManager
from dbgear.models.table import Table


def _create_jinja_env(template_dir: Path) -> Environment:
    """
    Create a Jinja2 environment with custom filters.

    Args:
        template_dir: Directory containing template files.

    Returns:
        Configured Jinja2 Environment.
    """
    env = Environment(
        loader=FileSystemLoader(template_dir),
        trim_blocks=True,
        lstrip_blocks=True,
        keep_trailing_newline=True,
    )

    # Register custom filters
    env.filters["get_table_note"] = _get_table_note
    env.filters["get_column_note"] = _get_column_note
    env.filters["truncate_note"] = _truncate_note
    env.filters["escape_pipe"] = _escape_pipe
    env.filters["format_column_type"] = _format_column_type

    return env


def _get_table_note(table) -> str:
    """Extract note text from a table object."""
    if not hasattr(table, "notes") or not table.notes:
        return ""
    note = table.notes.note if hasattr(table.notes, "note") else str(table.notes)
    return note.replace("\n", " ")


def _get_column_note(column) -> str:
    """Extract note text from a column object."""
    if not hasattr(column, "notes") or not column.notes:
        return ""
    note = column.notes.note if hasattr(column.notes, "note") else str(column.notes)
    return note.replace("\n", " ")


def _truncate_note(text: str, length: int) -> str:
    """Truncate text to specified length with ellipsis."""
    if len(text) <= length:
        return text
    return text[:length] + "..."


def _escape_pipe(text: str) -> str:
    """Escape pipe characters for Markdown table cells."""
    return text.replace("|", "\\|")


def _format_column_type(column_type) -> str:
    """Format column type for display."""
    if column_type is None:
        return ""
    if hasattr(column_type, "column_type"):
        return column_type.column_type
    return str(column_type)


def _collect_related_tables_info(
    all_tables: dict[str, Table],
    table_name: str,
) -> dict:
    """
    Collect related tables information for a given table.

    Args:
        all_tables: Dictionary of all tables in the schema {table_name: Table}
        table_name: Name of the target table

    Returns:
        Dictionary with 'referenced_tables' and 'referencing_tables' lists.
    """
    table = all_tables.get(table_name)
    if not table:
        return {'referenced_tables': [], 'referencing_tables': []}

    # Tables that this table references (via foreign keys/relations)
    referenced_tables = []
    for relation in table.relations:
        target_table_name = relation.target.table_name
        target_table = all_tables.get(target_table_name)
        if target_table:
            bindings = [
                f"{bc.source_column} -> {bc.target_column}"
                for bc in relation.bind_columns
            ]
            referenced_tables.append({
                'table_name': target_table_name,
                'display_name': target_table.display_name,
                'constraint_name': relation.constraint_name,
                'bindings': bindings,
                'on_delete': relation.on_delete,
                'on_update': relation.on_update,
            })

    # Tables that reference this table
    referencing_tables = []
    for other_table_name, other_table in all_tables.items():
        if other_table_name == table_name:
            continue
        for relation in other_table.relations:
            if relation.target.table_name == table_name:
                bindings = [
                    f"{bc.source_column} -> {bc.target_column}"
                    for bc in relation.bind_columns
                ]
                referencing_tables.append({
                    'table_name': other_table_name,
                    'display_name': other_table.display_name,
                    'constraint_name': relation.constraint_name,
                    'bindings': bindings,
                    'on_delete': relation.on_delete,
                    'on_update': relation.on_update,
                })

    return {
        'referenced_tables': referenced_tables,
        'referencing_tables': referencing_tables,
    }


def _get_output_extension(template_name: str) -> str:
    """
    Extract output file extension from template name.

    Args:
        template_name: Template filename (e.g., "template.md.j2")

    Returns:
        Output extension (e.g., ".md")
    """
    name = template_name
    if name.endswith('.j2'):
        name = name[:-3]
    elif name.endswith('.jinja2'):
        name = name[:-7]

    if '.' in name:
        return '.' + name.rsplit('.', 1)[1]
    return '.txt'


def generate_docs(
    schema_path: str,
    output_dir: str,
    template: str,
    scope: str = 'table',
) -> list[Path]:
    """
    Generate documentation from a schema file using a custom template.

    Args:
        schema_path: Path to the schema.yaml file.
        output_dir: Output path (file path for schema scope, directory for others).
        template: Path to Jinja2 template file.
        scope: Data scope ('schema', 'table', 'view', 'trigger', 'procedure').

    Returns:
        List of generated file paths.
    """
    schema_manager = SchemaManager.load(schema_path)
    template_path = Path(template)
    output_path = Path(output_dir)

    env = _create_jinja_env(template_path.parent)
    template_obj = env.get_template(template_path.name)

    generated_files = []

    if scope == 'schema':
        # Output to specified file path
        output_file = output_path
        output_file.parent.mkdir(parents=True, exist_ok=True)
        content = template_obj.render(
            schemas=schema_manager.schemas,
            registry=schema_manager.registry,
            notes=schema_manager.notes,
        )
        output_file.write_text(content, encoding="utf-8")
        generated_files.append(output_file)

    elif scope == 'table':
        # Generate one file per table
        output_path.mkdir(parents=True, exist_ok=True)
        output_ext = _get_output_extension(template_path.name)

        for schema_name, schema in schema_manager.schemas.items():
            schema_dir = output_path / schema_name
            schema_dir.mkdir(parents=True, exist_ok=True)

            all_tables = schema.tables.tables if schema.tables else {}
            for table_name, table in all_tables.items():
                related = _collect_related_tables_info(all_tables, table_name)
                output_file = schema_dir / f"{table_name}{output_ext}"
                content = template_obj.render(
                    schema_name=schema_name,
                    table_name=table_name,
                    table=table,
                    referenced_tables=related['referenced_tables'],
                    referencing_tables=related['referencing_tables'],
                )
                output_file.write_text(content, encoding="utf-8")
                generated_files.append(output_file)

    elif scope == 'view':
        # Generate one file per view
        output_path.mkdir(parents=True, exist_ok=True)
        output_ext = _get_output_extension(template_path.name)

        for schema_name, schema in schema_manager.schemas.items():
            schema_dir = output_path / schema_name
            schema_dir.mkdir(parents=True, exist_ok=True)

            all_views = schema.views.views if schema.views else {}
            for view_name, view in all_views.items():
                output_file = schema_dir / f"{view_name}{output_ext}"
                content = template_obj.render(
                    schema_name=schema_name,
                    view_name=view_name,
                    view=view,
                )
                output_file.write_text(content, encoding="utf-8")
                generated_files.append(output_file)

    elif scope == 'trigger':
        # Generate one file per trigger
        output_path.mkdir(parents=True, exist_ok=True)
        output_ext = _get_output_extension(template_path.name)

        for schema_name, schema in schema_manager.schemas.items():
            schema_dir = output_path / schema_name
            schema_dir.mkdir(parents=True, exist_ok=True)

            all_tables = schema.tables.tables if schema.tables else {}
            all_triggers = schema.triggers.triggers if schema.triggers else {}
            for trigger_name, trigger in all_triggers.items():
                # Get target table object if exists
                target_table = all_tables.get(trigger.table_name)
                output_file = schema_dir / f"{trigger_name}{output_ext}"
                content = template_obj.render(
                    schema_name=schema_name,
                    trigger_name=trigger_name,
                    trigger=trigger,
                    target_table=target_table,
                )
                output_file.write_text(content, encoding="utf-8")
                generated_files.append(output_file)

    elif scope == 'procedure':
        # Generate one file per procedure
        output_path.mkdir(parents=True, exist_ok=True)
        output_ext = _get_output_extension(template_path.name)

        for schema_name, schema in schema_manager.schemas.items():
            schema_dir = output_path / schema_name
            schema_dir.mkdir(parents=True, exist_ok=True)

            all_procedures = schema.procedures.procedures if schema.procedures else {}
            for procedure_name, procedure in all_procedures.items():
                output_file = schema_dir / f"{procedure_name}{output_ext}"
                content = template_obj.render(
                    schema_name=schema_name,
                    procedure_name=procedure_name,
                    procedure=procedure,
                )
                output_file.write_text(content, encoding="utf-8")
                generated_files.append(output_file)

    return generated_files
