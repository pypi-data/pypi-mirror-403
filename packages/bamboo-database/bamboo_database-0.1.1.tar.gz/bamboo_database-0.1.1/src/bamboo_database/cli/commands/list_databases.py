"""List databases command for bamboo_database CLI."""

import argparse
import sys

from bamboo_database.config import load_config, ConfigurationError


def run(args: argparse.Namespace) -> int:
    """Run the list-databases command.

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

    profiles = config.get_all_profiles()

    if not profiles:
        print("No databases configured.")
        return 0

    print(f"Configured databases ({len(profiles)}):\n")

    for profile in profiles:
        print(f"  {profile.name}")
        print(f"    Type: {profile.type}")

        if profile.type == "sqlite":
            print(f"    Path: {profile.path}")
        else:
            host = profile.host or "localhost"
            port = profile.get_port()
            print(f"    Host: {host}:{port}")
            print(f"    Database: {profile.database}")
            print(f"    User: {profile.user}")

        print(f"    Migrations: {profile.migrations_path}")
        print()

    return 0
