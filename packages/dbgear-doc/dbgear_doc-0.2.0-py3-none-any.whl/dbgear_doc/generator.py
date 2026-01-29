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


def generate_docs(
    schema_path: str,
    output_dir: str,
) -> list[Path]:
    """
    Generate documentation from a schema file.

    This function serves as the entry point for the dbgear doc plugin.

    Args:
        schema_path: Path to the schema.yaml file.
        output_dir: Directory to write documentation files.

    Returns:
        List of generated file paths.
    """
    schema_manager = SchemaManager.load(schema_path)

    generator = DocumentGenerator(schema_manager)
    return generator.generate(Path(output_dir))
