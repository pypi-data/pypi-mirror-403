"""
DBGear Document Templates.

This module provides Jinja2-based template engine for generating
Markdown documentation from database schema definitions.
"""
from .engine import DocTemplateEngine, template_engine

__all__ = ["DocTemplateEngine", "template_engine"]
