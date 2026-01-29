"""Configuration loader for bamboo_database."""

import sys
from pathlib import Path
from typing import Any

from bamboo_database.config.models import (
    ConfigurationError,
    DatabaseProfile,
    SUPPORTED_DATABASE_TYPES,
)

# Python 3.11+ has tomllib built-in, otherwise use tomli
if sys.version_info >= (3, 11):
    import tomllib
else:
    try:
        import tomli as tomllib
    except ImportError as e:
        raise ImportError(
            "tomli is required for Python < 3.11. "
            "Install it with: pip install tomli"
        ) from e


DEFAULT_CONFIG_FILENAME = "bamboo_database.toml"


class Config:
    """Configuration container for bamboo_database.

    Holds all database profiles and provides methods to access them.
    """

    def __init__(
        self,
        profiles: dict[str, DatabaseProfile],
        config_path: Path,
    ) -> None:
        """Initialize the configuration.

        Args:
            profiles: Dictionary mapping profile names to DatabaseProfile objects
            config_path: Path to the configuration file
        """
        self._profiles = profiles
        self._config_path = config_path

    @property
    def config_path(self) -> Path:
        """Get the path to the configuration file."""
        return self._config_path

    def get_database(self, name: str) -> DatabaseProfile:
        """Get a database profile by name.

        Args:
            name: Profile name

        Returns:
            The DatabaseProfile for the given name

        Raises:
            ConfigurationError: If the profile is not found
        """
        if name not in self._profiles:
            available = ", ".join(sorted(self._profiles.keys()))
            raise ConfigurationError(
                f"Database profile '{name}' not found. "
                f"Available profiles: {available}"
            )
        return self._profiles[name]

    def get_databases(self) -> list[str]:
        """Get all database profile names.

        Returns:
            List of profile names
        """
        return list(self._profiles.keys())

    def get_all_profiles(self) -> list[DatabaseProfile]:
        """Get all database profiles.

        Returns:
            List of all DatabaseProfile objects
        """
        return list(self._profiles.values())

    def __len__(self) -> int:
        """Return the number of configured databases."""
        return len(self._profiles)

    def __contains__(self, name: str) -> bool:
        """Check if a profile exists."""
        return name in self._profiles


def load_config(path: str | Path | None = None) -> Config:
    """Load configuration from a TOML file.

    Args:
        path: Path to the configuration file. If None, looks for
              'bamboo_database.toml' in the current directory.

    Returns:
        Config object containing all database profiles

    Raises:
        FileNotFoundError: If the configuration file does not exist
        ConfigurationError: If the configuration is invalid
    """
    if path is None:
        config_path = Path.cwd() / DEFAULT_CONFIG_FILENAME
    else:
        config_path = Path(path)

    if not config_path.exists():
        raise FileNotFoundError(
            f"Configuration file not found: {config_path}\n"
            f"Create a '{DEFAULT_CONFIG_FILENAME}' file or specify a custom path."
        )

    try:
        with open(config_path, "rb") as f:
            data = tomllib.load(f)
    except tomllib.TOMLDecodeError as e:
        raise ConfigurationError(f"Invalid TOML in {config_path}: {e}") from e

    profiles = _parse_profiles(data, config_path)
    return Config(profiles, config_path)


def _parse_profiles(data: dict[str, Any], config_path: Path) -> dict[str, DatabaseProfile]:
    """Parse database profiles from configuration data.

    Args:
        data: Parsed TOML data
        config_path: Path to the configuration file (for resolving relative paths)

    Returns:
        Dictionary mapping profile names to DatabaseProfile objects

    Raises:
        ConfigurationError: If profiles are missing or invalid
    """
    if "databases" not in data:
        raise ConfigurationError(
            "Configuration must contain a [databases] section with at least one profile"
        )

    databases = data["databases"]
    if not isinstance(databases, dict) or len(databases) == 0:
        raise ConfigurationError(
            "Configuration must contain at least one database profile under [databases]"
        )

    profiles: dict[str, DatabaseProfile] = {}
    base_path = config_path.parent

    for name, profile_data in databases.items():
        if not isinstance(profile_data, dict):
            raise ConfigurationError(
                f"Database profile '{name}' must be a table, not {type(profile_data).__name__}"
            )

        # Check for required 'type' field
        if "type" not in profile_data:
            raise ConfigurationError(
                f"Database profile '{name}' is missing required field 'type'. "
                f"Supported types: {', '.join(SUPPORTED_DATABASE_TYPES)}"
            )

        # Check for required 'migrations_path' field
        if "migrations_path" not in profile_data:
            raise ConfigurationError(
                f"Database profile '{name}' is missing required field 'migrations_path'"
            )

        try:
            profile = DatabaseProfile(
                name=name,
                type=profile_data["type"],
                migrations_path=profile_data["migrations_path"],
                host=profile_data.get("host"),
                port=profile_data.get("port"),
                database=profile_data.get("database"),
                user=profile_data.get("user"),
                password=profile_data.get("password"),
                path=profile_data.get("path"),
            )
            profile.resolve_paths(base_path)
            profiles[name] = profile
        except (TypeError, ValueError) as e:
            raise ConfigurationError(
                f"Invalid configuration for profile '{name}': {e}"
            ) from e

    return profiles
