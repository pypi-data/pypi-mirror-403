"""Factory function for creating database adapters."""

from bamboo_database.adapters.base import DatabaseAdapter
from bamboo_database.config.models import DatabaseProfile, SUPPORTED_DATABASE_TYPES


def create_adapter(profile: DatabaseProfile) -> DatabaseAdapter:
    """Create a database adapter based on the profile type.

    Args:
        profile: Database profile with connection settings

    Returns:
        An appropriate DatabaseAdapter instance for the profile type

    Raises:
        ValueError: If the database type is not supported

    Example:
        >>> from bamboo_database import load_config, create_adapter
        >>> config = load_config()
        >>> profile = config.get_database("default")
        >>> with create_adapter(profile) as adapter:
        ...     results = adapter.fetch_all("SELECT * FROM users")
    """
    match profile.type:
        case "postgresql":
            from bamboo_database.adapters.postgresql import PostgreSQLAdapter
            return PostgreSQLAdapter(profile)
        case "mysql":
            from bamboo_database.adapters.mysql import MySQLAdapter
            return MySQLAdapter(profile)
        case "sqlite":
            from bamboo_database.adapters.sqlite import SQLiteAdapter
            return SQLiteAdapter(profile)
        case _:
            raise ValueError(
                f"Unsupported database type: '{profile.type}'. "
                f"Supported types: {', '.join(SUPPORTED_DATABASE_TYPES)}"
            )
