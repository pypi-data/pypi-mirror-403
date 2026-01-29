"""
DBGear Document Generator Plugin

This package provides documentation generation capabilities for DBGear.
It generates Markdown documentation from database schema definitions.
"""

from .generator import DocumentGenerator, generate_docs

__version__ = "0.1.0"

__all__ = [
    "DocumentGenerator",
    "generate_docs",
]
