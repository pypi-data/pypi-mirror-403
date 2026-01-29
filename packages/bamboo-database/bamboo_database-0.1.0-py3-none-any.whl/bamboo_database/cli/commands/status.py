"""Status command for bamboo_database CLI."""

import argparse
import sys

from bamboo_database.config import load_config, ConfigurationError
from bamboo_database.adapters import create_adapter
from bamboo_database.migrations import MigrationExecutor, parse_migration_files


def run(args: argparse.Namespace) -> int:
    """Run the status command.

    Args:
        args: Parsed command line arguments

    Returns:
        Exit code (0 for success, non-zero for failure)
    """
    try:
        config = load_config()
    except FileNotFoundError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1
    except ConfigurationError as e:
        print(f"Configuration error: {e}", file=sys.stderr)
        return 1

    # Determine which databases to check
    if args.databases:
        database_names = args.databases
        # Validate database names
        for name in database_names:
            if name not in config:
                available = ", ".join(config.get_databases())
                print(
                    f"Error: Database profile '{name}' not found. "
                    f"Available profiles: {available}",
                    file=sys.stderr,
                )
                return 1
    else:
        database_names = config.get_databases()

    if not database_names:
        print("No databases configured.", file=sys.stderr)
        return 1

    for db_name in database_names:
        profile = config.get_database(db_name)
        print(f"\n=== Database: {db_name} ({profile.type}) ===")
        print(f"  Migrations path: {profile.get_migrations_path()}")

        # Get all migrations from files
        migrations_path = profile.get_migrations_path()
        try:
            all_migrations = parse_migration_files(migrations_path)
        except (FileNotFoundError, NotADirectoryError) as e:
            print(f"  Warning: {e}")
            all_migrations = []

        if not all_migrations:
            print("  No migration files found.")
            continue

        # Try to get applied migrations from database
        applied_set: set[str] = set()
        try:
            with create_adapter(profile) as adapter:
                executor = MigrationExecutor(adapter, profile)
                executor.ensure_tracker_table()
                applied_set = set(executor.get_applied_migrations())
        except ImportError as e:
            print(f"  Warning: Cannot connect to database - {e}")
            print("  Showing all migrations as pending (database status unknown)")
        except Exception as e:
            print(f"  Warning: Cannot connect to database - {e}")
            print("  Showing all migrations as pending (database status unknown)")

        # Display status
        pending = [m for m in all_migrations if m.filename not in applied_set]
        applied = [m for m in all_migrations if m.filename in applied_set]

        if applied:
            print(f"\n  Applied ({len(applied)}):")
            for migration in applied:
                print(f"    ✓ {migration.filename}")

        if pending:
            print(f"\n  Pending ({len(pending)}):")
            for migration in pending:
                print(f"    ○ {migration.filename}")

        if not pending:
            print("\n  All migrations have been applied.")

    return 0
