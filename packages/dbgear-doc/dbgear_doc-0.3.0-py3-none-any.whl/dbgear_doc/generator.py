"""
Document Generator for DBGear schemas.

This module provides the core functionality for generating
Markdown documentation from database schema definitions.
"""

from pathlib import Path

from dbgear.models.schema import SchemaManager

from .templates import template_engine


class DocumentGenerator:
    """
    Generates Markdown documentation from DBGear schema definitions.

    Uses Jinja2 templates for maintainable Markdown generation.
    """

    def __init__(self, schema_manager: SchemaManager):
        """
        Initialize the document generator.

        Args:
            schema_manager: The schema manager containing database definitions.
        """
        self.schema_manager = schema_manager

    def generate(self, output_dir: Path) -> list[Path]:
        """
        Generate documentation files.

        Args:
            output_dir: Directory to write documentation files.

        Returns:
            List of generated file paths.
        """
        output_dir.mkdir(parents=True, exist_ok=True)
        generated_files = []

        # Generate index file
        index_path = output_dir / "index.md"
        self._generate_index(index_path)
        generated_files.append(index_path)

        # Generate documentation for each schema
        for schema_name, schema in self.schema_manager.schemas.items():
            schema_dir = output_dir / schema_name
            schema_dir.mkdir(parents=True, exist_ok=True)

            # Generate schema overview
            schema_path = schema_dir / "README.md"
            self._generate_schema_doc(schema_path, schema_name, schema)
            generated_files.append(schema_path)

            # Generate table documentation
            for table_name, table in schema.tables.tables.items():
                table_path = schema_dir / f"{table_name}.md"
                self._generate_table_doc(table_path, schema_name, table_name, table)
                generated_files.append(table_path)

        return generated_files

    def _generate_index(self, path: Path) -> None:
        """Generate the main index file."""
        content = template_engine.render(
            "index.md.j2",
            schemas=self.schema_manager.schemas.keys(),
        )
        path.write_text(content, encoding="utf-8")

    def _generate_schema_doc(self, path: Path, schema_name: str, schema) -> None:
        """Generate documentation for a schema."""
        tables = schema.tables.tables if schema.tables else {}
        content = template_engine.render(
            "schema.md.j2",
            schema_name=schema_name,
            tables=tables,
        )
        path.write_text(content, encoding="utf-8")

    def _generate_table_doc(
        self, path: Path, schema_name: str, table_name: str, table
    ) -> None:
        """Generate documentation for a table."""
        content = template_engine.render(
            "table.md.j2",
            schema_name=schema_name,
            table_name=table_name,
            table=table,
        )
        path.write_text(content, encoding="utf-8")


def _generate_with_custom_template(
    schema_manager: SchemaManager,
    output_path: Path,
    template_path: Path,
    scope: str,
) -> list[Path]:
    """
    Generate documentation using a custom template.

    Args:
        schema_manager: The schema manager containing database definitions.
        output_path: For scope='schema', this is the output file path.
                    For scope='table', this is the output directory.
        template_path: Path to the custom Jinja2 template file.
        scope: Data scope ('schema' or 'table').

    Returns:
        List of generated file paths.
    """
    generated_files = []

    # Create template engine with custom template directory
    custom_engine = template_engine.create_for_directory(template_path.parent)
    template_name = template_path.name

    if scope == 'schema':
        # Pass entire schema_manager, output to specified file path
        output_file = output_path
        output_file.parent.mkdir(parents=True, exist_ok=True)
        content = custom_engine.render(
            template_name,
            schema_manager=schema_manager,
            schemas=schema_manager.schemas,
        )
        output_file.write_text(content, encoding="utf-8")
        generated_files.append(output_file)
    else:
        # scope == 'table': generate one file per table in output directory
        output_dir = output_path
        output_dir.mkdir(parents=True, exist_ok=True)

        # Determine output file extension from template name
        # e.g., "template.md.j2" -> ".md", "template.html.j2" -> ".html"
        output_ext = _get_output_extension(template_name)

        for schema_name, schema in schema_manager.schemas.items():
            tables = schema.tables.tables if schema.tables else {}
            for table_name, table in tables.items():
                output_file = output_dir / f"{schema_name}_{table_name}{output_ext}"
                content = custom_engine.render(
                    template_name,
                    schema_name=schema_name,
                    table_name=table_name,
                    table=table,
                )
                output_file.write_text(content, encoding="utf-8")
                generated_files.append(output_file)

    return generated_files


def _get_output_extension(template_name: str) -> str:
    """
    Extract output file extension from template name.

    Args:
        template_name: Template filename (e.g., "template.md.j2")

    Returns:
        Output extension (e.g., ".md")
    """
    # Remove .j2 or .jinja2 suffix
    name = template_name
    if name.endswith('.j2'):
        name = name[:-3]
    elif name.endswith('.jinja2'):
        name = name[:-7]

    # Get remaining extension
    if '.' in name:
        return '.' + name.rsplit('.', 1)[1]
    return '.txt'


def generate_docs(
    schema_path: str,
    output_dir: str,
    template: str | None = None,
    scope: str = 'table',
) -> list[Path]:
    """
    Generate documentation from a schema file.

    This function serves as the entry point for the dbgear doc plugin.

    Args:
        schema_path: Path to the schema.yaml file.
        output_dir: Directory to write documentation files.
        template: Optional custom Jinja2 template file path.
        scope: Data scope for custom template ('schema' or 'table').

    Returns:
        List of generated file paths.
    """
    schema_manager = SchemaManager.load(schema_path)

    if template is None:
        # Default behavior: generate standard documentation
        generator = DocumentGenerator(schema_manager)
        return generator.generate(Path(output_dir))

    # Custom template mode
    return _generate_with_custom_template(
        schema_manager, Path(output_dir), Path(template), scope
    )
