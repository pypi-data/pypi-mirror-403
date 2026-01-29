"""Generate schema command for bamboo_database CLI."""

import argparse
import sys
from pathlib import Path

from bamboo_database.config import load_config, ConfigurationError
from bamboo_database.migrations import parse_migration_files


def run(args: argparse.Namespace) -> int:
    """Run the generate-schema command.

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

    output_base = Path(args.output)

    for db_name in database_names:
        profile = config.get_database(db_name)
        print(f"\n=== Generating schema for: {db_name} ({profile.type}) ===")

        # Get all migrations
        migrations_path = profile.get_migrations_path()
        try:
            migrations = parse_migration_files(migrations_path)
        except (FileNotFoundError, NotADirectoryError) as e:
            print(f"  Warning: {e}")
            continue

        if not migrations:
            print("  No migration files found.")
            continue

        # Create output directory
        output_dir = output_base / db_name
        output_dir.mkdir(parents=True, exist_ok=True)

        print(f"  Found {len(migrations)} migration file(s)")
        print(f"  Output directory: {output_dir}")

        # TODO: Implement actual schema generation logic
        # For now, this is a stub that shows what would be generated
        print("\n  Schema generation requires SQL parsing logic.")
        print("  This is a placeholder - full implementation in future proposal.")
        print("\n  Detected migrations:")
        for migration in migrations:
            print(f"    - {migration.filename} ({migration.type})")

        # Create a placeholder file explaining the schema generation
        readme_path = output_dir / "README.md"
        readme_content = f"""# Schema for {db_name}

This directory will contain auto-generated schema files from migrations.

## Source Migrations

Path: `{migrations_path}`

## Files

After full implementation, this directory will contain:
- `table-schema-{{table}}.sql` - Complete CREATE TABLE statements
- `table-seed-{{table}}.sql` - All seed data for each table
- `table-index-{{table}}.sql` - All indexes for each table

## Migration Files Detected

"""
        for migration in migrations:
            readme_content += f"- `{migration.filename}` ({migration.type})\n"

        readme_path.write_text(readme_content)
        print(f"\n  Created: {readme_path}")

    print(f"\n{'='*50}")
    print("Schema generation complete (stub implementation).")
    print("Full SQL parsing will be implemented in a future proposal.")

    return 0
