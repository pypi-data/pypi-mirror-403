"""
Jinja2-based template engine for Markdown documentation generation.
"""
from pathlib import Path
from jinja2 import Environment, FileSystemLoader


class DocTemplateEngine:
    """
    Template engine for generating Markdown documentation from database schemas.
    """

    def __init__(self):
        """Initialize the template engine with Jinja2 environment."""
        template_dir = Path(__file__).parent
        self.env = Environment(
            loader=FileSystemLoader(template_dir),
            trim_blocks=True,
            lstrip_blocks=True,
            keep_trailing_newline=True,
        )
        self._setup_filters()

    def _setup_filters(self):
        """Register custom Jinja2 filters."""
        self.env.filters["get_table_note"] = self._get_table_note
        self.env.filters["get_column_note"] = self._get_column_note
        self.env.filters["truncate_note"] = self._truncate_note
        self.env.filters["escape_pipe"] = self._escape_pipe
        self.env.filters["format_column_type"] = self._format_column_type

    @staticmethod
    def _get_table_note(table) -> str:
        """Extract note text from a table object."""
        if not hasattr(table, "notes") or not table.notes:
            return ""
        note = table.notes.note if hasattr(table.notes, "note") else str(table.notes)
        return note.replace("\n", " ")

    @staticmethod
    def _get_column_note(column) -> str:
        """Extract note text from a column object."""
        if not hasattr(column, "notes") or not column.notes:
            return ""
        note = column.notes.note if hasattr(column.notes, "note") else str(column.notes)
        return note.replace("\n", " ")

    @staticmethod
    def _truncate_note(text: str, length: int) -> str:
        """Truncate text to specified length with ellipsis."""
        if len(text) <= length:
            return text
        return text[:length] + "..."

    @staticmethod
    def _escape_pipe(text: str) -> str:
        """Escape pipe characters for Markdown table cells."""
        return text.replace("|", "\\|")

    @staticmethod
    def _format_column_type(column_type) -> str:
        """Format column type for display."""
        if column_type is None:
            return ""
        if hasattr(column_type, "column_type"):
            return column_type.column_type
        return str(column_type)

    def render(self, template_name: str, **kwargs) -> str:
        """
        Render a template with the given context.

        Args:
            template_name: Name of the template file (e.g., 'index.md.j2')
            **kwargs: Template context variables

        Returns:
            Rendered template string
        """
        template = self.env.get_template(template_name)
        return template.render(**kwargs)


# Global template engine instance
template_engine = DocTemplateEngine()
