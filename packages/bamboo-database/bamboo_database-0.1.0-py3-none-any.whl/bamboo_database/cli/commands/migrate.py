"""Migrate command for bamboo_database CLI."""

import argparse
import sys

from bamboo_database.config import load_config, ConfigurationError
from bamboo_database.adapters import create_adapter
from bamboo_database.migrations import MigrationExecutor


def run(args: argparse.Namespace) -> int:
    """Run the migrate command.

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

    # Determine which databases to migrate
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

    total_applied = 0
    failed = False

    for db_name in database_names:
        profile = config.get_database(db_name)
        print(f"\n=== Migrating database: {db_name} ({profile.type}) ===")

        try:
            with create_adapter(profile) as adapter:
                executor = MigrationExecutor(adapter, profile)
                executor.ensure_tracker_table()

                pending = executor.get_pending_migrations()
                if not pending:
                    print("  No pending migrations.")
                    continue

                print(f"  Found {len(pending)} pending migration(s):")
                for migration in pending:
                    print(f"    - {migration.filename}")

                print("\n  Executing migrations...")
                results = executor.execute_pending()

                for result in results:
                    if result.success:
                        print(f"    ✓ {result.migration.filename}")
                        total_applied += 1
                    else:
                        print(f"    ✗ {result.migration.filename}")
                        print(f"      Error: {result.error}")
                        failed = True
                        break

        except ImportError as e:
            print(f"  Error: {e}", file=sys.stderr)
            failed = True
        except Exception as e:
            print(f"  Error: {e}", file=sys.stderr)
            failed = True

    print(f"\n{'='*50}")
    print(f"Total migrations applied: {total_applied}")

    if failed:
        print("Some migrations failed. See errors above.")
        return 1

    return 0
