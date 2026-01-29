"""Configuration models for bamboo_database."""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Literal


class ConfigurationError(Exception):
    """Raised when configuration is invalid or missing required fields."""

    pass


DatabaseType = Literal["postgresql", "mysql", "sqlite"]
SUPPORTED_DATABASE_TYPES: tuple[DatabaseType, ...] = ("postgresql", "mysql", "sqlite")


@dataclass
class DatabaseProfile:
    """Configuration for a single database connection.

    Attributes:
        name: Profile name (e.g., "default", "analytics")
        type: Database type ("postgresql", "mysql", "sqlite")
        migrations_path: Path to migrations folder for this database
        host: Database host (required for postgresql, mysql)
        port: Database port (optional, uses default if not specified)
        database: Database name (required for postgresql, mysql)
        user: Database user (required for postgresql, mysql)
        password: Database password (optional)
        path: File path for SQLite databases
    """

    name: str
    type: DatabaseType
    migrations_path: str
    host: str | None = None
    port: int | None = None
    database: str | None = None
    user: str | None = None
    password: str | None = None
    path: str | None = None  # For SQLite

    # Internal: resolved absolute path to migrations folder
    _resolved_migrations_path: Path | None = field(default=None, repr=False)

    def __post_init__(self) -> None:
        """Validate the profile configuration."""
        self._validate()

    def _validate(self) -> None:
        """Validate required fields based on database type."""
        if self.type not in SUPPORTED_DATABASE_TYPES:
            raise ConfigurationError(
                f"Invalid database type '{self.type}' for profile '{self.name}'. "
                f"Supported types: {', '.join(SUPPORTED_DATABASE_TYPES)}"
            )

        if self.type in ("postgresql", "mysql"):
            if not self.host:
                raise ConfigurationError(
                    f"Profile '{self.name}' ({self.type}): 'host' is required"
                )
            if not self.database:
                raise ConfigurationError(
                    f"Profile '{self.name}' ({self.type}): 'database' is required"
                )
            if not self.user:
                raise ConfigurationError(
                    f"Profile '{self.name}' ({self.type}): 'user' is required"
                )

        if self.type == "sqlite":
            if not self.path:
                raise ConfigurationError(
                    f"Profile '{self.name}' (sqlite): 'path' is required"
                )

    def get_default_port(self) -> int | None:
        """Get the default port for the database type."""
        defaults: dict[str, int] = {
            "postgresql": 5432,
            "mysql": 3306,
        }
        return defaults.get(self.type)

    def get_port(self) -> int | None:
        """Get the port, falling back to default if not specified."""
        return self.port or self.get_default_port()

    def get_migrations_path(self) -> Path:
        """Get the resolved migrations path."""
        if self._resolved_migrations_path:
            return self._resolved_migrations_path
        return Path(self.migrations_path)

    def resolve_paths(self, base_path: Path) -> None:
        """Resolve relative paths based on the configuration file location.

        Args:
            base_path: Directory containing the configuration file
        """
        migrations_path = Path(self.migrations_path)
        if not migrations_path.is_absolute():
            self._resolved_migrations_path = (base_path / migrations_path).resolve()
        else:
            self._resolved_migrations_path = migrations_path

        # Also resolve SQLite path
        if self.type == "sqlite" and self.path:
            sqlite_path = Path(self.path)
            if not sqlite_path.is_absolute():
                self.path = str((base_path / sqlite_path).resolve())
