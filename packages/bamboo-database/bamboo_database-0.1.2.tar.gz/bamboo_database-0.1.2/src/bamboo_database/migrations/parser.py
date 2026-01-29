"""Migration file parser for bamboo_database."""

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Literal


MigrationType = Literal["migrate", "seed", "index"]
MIGRATION_TYPES: tuple[MigrationType, ...] = ("migrate", "seed", "index")

# Migration filename pattern: {version}_{type}_{description}.sql
# Example: 0001_migrate_create_users.sql
MIGRATION_PATTERN = re.compile(
    r"^(\d{4})_(migrate|seed|index)_(.+)\.sql$",
    re.IGNORECASE,
)


@dataclass
class MigrationFile:
    """Represents a parsed migration file.

    Attributes:
        path: Full path to the migration file
        version: 4-digit version number (e.g., "0001")
        type: Migration type ("migrate", "seed", or "index")
        description: Description extracted from filename
        content: SQL content of the file (loaded lazily)
    """

    path: Path
    version: str
    type: MigrationType
    description: str
    _content: str | None = None

    @property
    def filename(self) -> str:
        """Get the filename without directory."""
        return self.path.name

    @property
    def content(self) -> str:
        """Get the SQL content of the migration file.

        Content is loaded lazily on first access.
        """
        if self._content is None:
            self._content = self.path.read_text(encoding="utf-8")
        return self._content

    @property
    def sort_key(self) -> tuple[str, int, str]:
        """Get sort key for ordering migrations.

        Migrations are sorted by:
        1. Version number (ascending)
        2. Type order: migrate=0, seed=1, index=2
        3. Description (alphabetical)
        """
        type_order = {"migrate": 0, "seed": 1, "index": 2}
        return (self.version, type_order.get(self.type, 99), self.description)

    def __lt__(self, other: "MigrationFile") -> bool:
        """Enable sorting of migration files."""
        return self.sort_key < other.sort_key


def parse_migration_filename(filename: str) -> tuple[str, MigrationType, str] | None:
    """Parse a migration filename into its components.

    Args:
        filename: The filename to parse (e.g., "0001_migrate_create_users.sql")

    Returns:
        Tuple of (version, type, description) if valid, None otherwise

    Example:
        >>> parse_migration_filename("0001_migrate_create_users.sql")
        ("0001", "migrate", "create_users")
        >>> parse_migration_filename("invalid.sql")
        None
    """
    match = MIGRATION_PATTERN.match(filename)
    if not match:
        return None

    version = match.group(1)
    migration_type = match.group(2).lower()
    description = match.group(3)

    # Validate migration type
    if migration_type not in MIGRATION_TYPES:
        return None

    return (version, migration_type, description)  # type: ignore[return-value]


def parse_migration_files(migrations_path: Path) -> list[MigrationFile]:
    """Parse all migration files in a directory.

    Args:
        migrations_path: Path to the migrations directory

    Returns:
        List of MigrationFile objects, sorted by version and type

    Raises:
        FileNotFoundError: If the migrations directory doesn't exist
    """
    if not migrations_path.exists():
        raise FileNotFoundError(f"Migrations directory not found: {migrations_path}")

    if not migrations_path.is_dir():
        raise NotADirectoryError(f"Not a directory: {migrations_path}")

    migrations: list[MigrationFile] = []

    for file_path in migrations_path.glob("*.sql"):
        parsed = parse_migration_filename(file_path.name)
        if parsed is None:
            # Skip files that don't match the migration pattern
            continue

        version, migration_type, description = parsed
        migrations.append(
            MigrationFile(
                path=file_path,
                version=version,
                type=migration_type,
                description=description,
            )
        )

    # Sort migrations by version, then type, then description
    migrations.sort()
    return migrations


def get_next_version(migrations_path: Path) -> str:
    """Get the next available migration version number.

    Args:
        migrations_path: Path to the migrations directory

    Returns:
        Next version number as 4-digit zero-padded string (e.g., "0001")
    """
    try:
        migrations = parse_migration_files(migrations_path)
    except (FileNotFoundError, NotADirectoryError):
        return "0001"

    if not migrations:
        return "0001"

    max_version = max(int(m.version) for m in migrations)
    return f"{max_version + 1:04d}"
