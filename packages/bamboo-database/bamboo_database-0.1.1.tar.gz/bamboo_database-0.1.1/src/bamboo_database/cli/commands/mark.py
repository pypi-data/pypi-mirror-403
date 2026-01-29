"""Mark command for bamboo_database CLI."""

import argparse
import sys

from bamboo_database.config import load_config, ConfigurationError
from bamboo_database.adapters import create_adapter
from bamboo_database.migrations import MigrationExecutor


def run(args: argparse.Namespace) -> int:
    """Run the mark command.

    Marks pending migrations as applied without executing their SQL.
    This is useful when adding bamboo_database to an existing project
    where the database schema already exists.

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

    # Determine which databases to process
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

    total_marked = 0
    failed = False

    for db_name in database_names:
        profile = config.get_database(db_name)
        print(f"\n=== Marking migrations for database: {db_name} ({profile.type}) ===")

        try:
            with create_adapter(profile) as adapter:
                executor = MigrationExecutor(adapter, profile)
                executor.ensure_tracker_table()

                pending = executor.get_pending_migrations()
                if not pending:
                    print("  No pending migrations to mark.")
                    continue

                print(f"  Found {len(pending)} pending migration(s):")
                for migration in pending:
                    print(f"    - {migration.filename}")

                print("\n  Marking migrations as applied...")
                marked = executor.mark_pending()

                for filename in marked:
                    print(f"    ✓ {filename}")
                    total_marked += 1

        except ImportError as e:
            print(f"  Error: {e}", file=sys.stderr)
            failed = True
        except Exception as e:
            print(f"  Error: {e}", file=sys.stderr)
            failed = True

    print(f"\n{'='*50}")
    print(f"Total migrations marked as applied: {total_marked}")

    if failed:
        print("Some operations failed. See errors above.")
        return 1

    return 0
