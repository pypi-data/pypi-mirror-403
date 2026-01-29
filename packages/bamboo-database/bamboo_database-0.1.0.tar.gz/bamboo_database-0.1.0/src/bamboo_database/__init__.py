"""
bamboo_database - CLI tool for managing database migrations and seed data.

A unified interface for working with multiple database backends using raw SQL,
allowing developers to version control their database schemas and seed data
across different environments.
"""

from bamboo_database.config import load_config, Config, DatabaseProfile
from bamboo_database.adapters import create_adapter, DatabaseAdapter

__version__ = "0.1.0"
__all__ = [
    "__version__",
    "load_config",
    "Config",
    "DatabaseProfile",
    "create_adapter",
    "DatabaseAdapter",
]
