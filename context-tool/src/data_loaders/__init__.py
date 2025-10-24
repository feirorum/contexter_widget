"""Data loaders for Context Tool - supports YAML and Markdown formats"""

from pathlib import Path
from typing import Literal
import sqlite3

from .yaml_data_loader import YAMLDataLoader
from .markdown_data_loader import MarkdownDataLoader


DataFormat = Literal['yaml', 'markdown']


def load_data(
    db_connection: sqlite3.Connection,
    data_dir: Path,
    format: DataFormat = 'yaml'
) -> None:
    """
    Load data into database using the appropriate loader

    Args:
        db_connection: Active SQLite database connection
        data_dir: Directory containing data files
        format: Data format ('yaml' or 'markdown')

    Example:
        >>> db = get_database(':memory:')
        >>> load_data(db.connection, Path('./data'), format='yaml')
        >>> load_data(db.connection, Path('./data-md'), format='markdown')
    """
    if format == 'yaml':
        loader = YAMLDataLoader(db_connection)
        loader.load_from_yaml(data_dir)
    elif format == 'markdown':
        loader = MarkdownDataLoader(db_connection)
        loader.load_from_markdown(data_dir)
    else:
        raise ValueError(f"Unsupported data format: {format}. Use 'yaml' or 'markdown'.")


# For backward compatibility - old function name
def load_data_yaml(db_connection: sqlite3.Connection, data_dir: Path) -> None:
    """Load YAML data (deprecated - use load_data with format='yaml')"""
    load_data(db_connection, data_dir, format='yaml')


def load_data_markdown(db_connection: sqlite3.Connection, data_dir: Path) -> None:
    """Load Markdown data (deprecated - use load_data with format='markdown')"""
    load_data(db_connection, data_dir, format='markdown')


__all__ = [
    'load_data',
    'load_data_yaml',
    'load_data_markdown',
    'YAMLDataLoader',
    'MarkdownDataLoader',
]
