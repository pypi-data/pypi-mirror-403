"""Main CLI entry point for bamboo_database."""

import argparse
import sys

from bamboo_database import __version__
from bamboo_database.cli.commands import (
    migrate,
    generate_schema,
    generate_rules,
    status,
    list_databases,
)


def create_parser() -> argparse.ArgumentParser:
    """Create the main argument parser with all subcommands."""
    parser = argparse.ArgumentParser(
        prog="bamboodb",
        description="CLI tool for managing database migrations and seed data",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  bamboodb migrate                    Run migrations for all databases
  bamboodb migrate --database default Run migrations for specific database
  bamboodb status                     Show migration status
  bamboodb list-databases             List configured databases
  bamboodb generate-schema            Generate schema files from migrations
  bamboodb generate-rules             Generate AI migration guidelines
        """,
    )

    parser.add_argument(
        "--version",
        action="version",
        version=f"%(prog)s {__version__}",
    )

    subparsers = parser.add_subparsers(
        title="commands",
        dest="command",
        metavar="<command>",
    )

    # migrate command
    migrate_parser = subparsers.add_parser(
        "migrate",
        help="Run pending database migrations",
        description="Execute pending migrations for configured databases",
    )
    migrate_parser.add_argument(
        "--database", "-d",
        action="append",
        dest="databases",
        metavar="NAME",
        help="Target specific database(s). Can be used multiple times. "
             "If not specified, all databases are migrated.",
    )
    migrate_parser.set_defaults(func=migrate.run)

    # status command
    status_parser = subparsers.add_parser(
        "status",
        help="Show migration status",
        description="Display pending and applied migrations for databases",
    )
    status_parser.add_argument(
        "--database", "-d",
        action="append",
        dest="databases",
        metavar="NAME",
        help="Target specific database(s). Can be used multiple times.",
    )
    status_parser.set_defaults(func=status.run)

    # list-databases command
    list_db_parser = subparsers.add_parser(
        "list-databases",
        help="List configured databases",
        description="Show all database profiles from configuration",
    )
    list_db_parser.set_defaults(func=list_databases.run)

    # generate-schema command
    gen_schema_parser = subparsers.add_parser(
        "generate-schema",
        help="Generate schema files from migrations",
        description="Create organized schema files by analyzing migrations",
    )
    gen_schema_parser.add_argument(
        "--database", "-d",
        action="append",
        dest="databases",
        metavar="NAME",
        help="Target specific database(s). Can be used multiple times.",
    )
    gen_schema_parser.add_argument(
        "--output", "-o",
        default="schema",
        metavar="PATH",
        help="Output directory for schema files (default: schema)",
    )
    gen_schema_parser.set_defaults(func=generate_schema.run)

    # generate-rules command
    gen_rules_parser = subparsers.add_parser(
        "generate-rules",
        help="Generate AI migration guidelines",
        description="Create a markdown file with migration rules for AI assistants",
    )
    gen_rules_parser.add_argument(
        "--output", "-o",
        default="bamboo_database-rule.md",
        metavar="PATH",
        help="Output file path (default: bamboo_database-rule.md)",
    )
    gen_rules_parser.set_defaults(func=generate_rules.run)

    return parser


def main(argv: list[str] | None = None) -> int:
    """Main entry point for the CLI.

    Args:
        argv: Command line arguments (defaults to sys.argv[1:])

    Returns:
        Exit code (0 for success, non-zero for failure)
    """
    parser = create_parser()
    args = parser.parse_args(argv)

    if args.command is None:
        parser.print_help()
        return 0

    try:
        return args.func(args)
    except KeyboardInterrupt:
        print("\nOperation cancelled.")
        return 130
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
