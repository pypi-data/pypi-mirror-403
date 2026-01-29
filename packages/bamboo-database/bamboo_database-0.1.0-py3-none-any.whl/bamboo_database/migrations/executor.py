"""Migration executor for bamboo_database."""

from dataclasses import dataclass
from pathlib import Path

from bamboo_database.adapters.base import DatabaseAdapter
from bamboo_database.config.models import DatabaseProfile
from bamboo_database.migrations.parser import MigrationFile, parse_migration_files
from bamboo_database.migrations.tracker import MigrationTracker


@dataclass
class MigrationResult:
    """Result of a migration execution.

    Attributes:
        migration: The migration file that was executed
        success: Whether the migration succeeded
        error: Error message if failed, None if succeeded
    """

    migration: MigrationFile
    success: bool
    error: str | None = None


class MigrationExecutor:
    """Executes migrations against a database.

    This class handles:
    - Loading pending migrations
    - Executing migrations in order
    - Tracking migration state
    """

    def __init__(
        self,
        adapter: DatabaseAdapter,
        profile: DatabaseProfile,
        tracker: MigrationTracker | None = None,
    ) -> None:
        """Initialize the migration executor.

        Args:
            adapter: Database adapter for executing SQL
            profile: Database profile with migrations path
            tracker: Migration tracker (created automatically if not provided)
        """
        self._adapter = adapter
        self._profile = profile
        self._tracker = tracker or MigrationTracker(adapter)

    def get_pending_migrations(self) -> list[MigrationFile]:
        """Get all pending (not yet applied) migrations.

        Returns:
            List of MigrationFile objects that haven't been applied yet
        """
        migrations_path = self._profile.get_migrations_path()

        try:
            all_migrations = parse_migration_files(migrations_path)
        except (FileNotFoundError, NotADirectoryError):
            return []

        applied = self._tracker.get_applied_migrations()
        applied_set = set(applied)

        return [m for m in all_migrations if m.filename not in applied_set]

    def get_applied_migrations(self) -> list[str]:
        """Get all applied migration filenames.

        Returns:
            List of applied migration filenames
        """
        return self._tracker.get_applied_migrations()

    def execute_migration(self, migration: MigrationFile) -> MigrationResult:
        """Execute a single migration.

        The migration is executed within a transaction. If successful,
        the migration is recorded in the tracking table.

        Args:
            migration: The migration to execute

        Returns:
            MigrationResult with success status and any error
        """
        try:
            # Execute the migration SQL
            # Note: The migration file should contain its own BEGIN/COMMIT
            # but we still wrap in our transaction tracking
            self._adapter.execute(migration.content)

            # Record the migration as applied
            self._tracker.record_migration(migration.filename)

            return MigrationResult(migration=migration, success=True)

        except Exception as e:
            # Attempt to rollback on failure
            try:
                self._adapter.rollback()
            except Exception:
                pass  # Ignore rollback errors

            return MigrationResult(
                migration=migration,
                success=False,
                error=str(e),
            )

    def execute_pending(self) -> list[MigrationResult]:
        """Execute all pending migrations.

        Migrations are executed in order. Execution stops on first failure.

        Returns:
            List of MigrationResult objects for each attempted migration
        """
        pending = self.get_pending_migrations()
        results: list[MigrationResult] = []

        for migration in pending:
            result = self.execute_migration(migration)
            results.append(result)

            if not result.success:
                # Stop on first failure
                break

        return results

    def ensure_tracker_table(self) -> None:
        """Ensure the migration tracking table exists.

        Call this before running migrations to set up tracking.
        """
        self._tracker.ensure_table()
