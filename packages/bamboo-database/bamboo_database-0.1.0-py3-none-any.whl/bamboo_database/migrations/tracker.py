"""Migration state tracking for bamboo_database."""

from datetime import datetime

from bamboo_database.adapters.base import DatabaseAdapter


TRACKING_TABLE_NAME = "bamboo_migrations"


class MigrationTracker:
    """Tracks which migrations have been applied to a database.

    Each database maintains its own `bamboo_migrations` table to track
    the state of applied migrations.
    """

    def __init__(self, adapter: DatabaseAdapter) -> None:
        """Initialize the migration tracker.

        Args:
            adapter: Database adapter for executing SQL
        """
        self._adapter = adapter
        self._table_ensured = False

    def ensure_table(self) -> None:
        """Ensure the migration tracking table exists.

        Creates the table if it doesn't exist. Safe to call multiple times.
        """
        if self._table_ensured:
            return

        # Use ANSI SQL that works across PostgreSQL, MySQL, and SQLite
        create_sql = f"""
            CREATE TABLE IF NOT EXISTS {TRACKING_TABLE_NAME} (
                id INTEGER PRIMARY KEY,
                filename VARCHAR(255) NOT NULL UNIQUE,
                applied_at TIMESTAMP NOT NULL
            )
        """

        self._adapter.execute(create_sql)
        self._adapter.commit()
        self._table_ensured = True

    def get_applied_migrations(self) -> list[str]:
        """Get all applied migration filenames.

        Returns:
            List of migration filenames that have been applied,
            ordered by application time
        """
        self.ensure_table()

        sql = f"""
            SELECT filename FROM {TRACKING_TABLE_NAME}
            ORDER BY applied_at ASC, id ASC
        """

        results = self._adapter.fetch_all(sql)
        return [row["filename"] for row in results]

    def is_applied(self, filename: str) -> bool:
        """Check if a migration has been applied.

        Args:
            filename: The migration filename to check

        Returns:
            True if the migration has been applied, False otherwise
        """
        self.ensure_table()

        sql = f"""
            SELECT COUNT(*) as count FROM {TRACKING_TABLE_NAME}
            WHERE filename = ?
        """

        # Use parameterized query
        result = self._adapter.fetch_one(sql, (filename,))
        if result is None:
            return False
        return result.get("count", 0) > 0

    def record_migration(self, filename: str) -> None:
        """Record a migration as applied.

        Args:
            filename: The migration filename to record
        """
        self.ensure_table()

        now = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")

        sql = f"""
            INSERT INTO {TRACKING_TABLE_NAME} (filename, applied_at)
            VALUES (?, ?)
        """

        self._adapter.execute(sql, (filename, now))
        self._adapter.commit()

    def remove_migration(self, filename: str) -> None:
        """Remove a migration record (for rollback purposes).

        Args:
            filename: The migration filename to remove
        """
        self.ensure_table()

        sql = f"""
            DELETE FROM {TRACKING_TABLE_NAME}
            WHERE filename = ?
        """

        self._adapter.execute(sql, (filename,))
        self._adapter.commit()

    def get_migration_info(self, filename: str) -> dict[str, str] | None:
        """Get information about a specific migration.

        Args:
            filename: The migration filename to look up

        Returns:
            Dictionary with migration info, or None if not found
        """
        self.ensure_table()

        sql = f"""
            SELECT filename, applied_at FROM {TRACKING_TABLE_NAME}
            WHERE filename = ?
        """

        return self._adapter.fetch_one(sql, (filename,))
