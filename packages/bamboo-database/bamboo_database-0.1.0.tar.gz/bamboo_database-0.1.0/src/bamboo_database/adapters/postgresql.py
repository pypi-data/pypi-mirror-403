"""PostgreSQL database adapter."""

from typing import Any

from bamboo_database.adapters.base import DatabaseAdapter
from bamboo_database.config.models import DatabaseProfile


class PostgreSQLAdapter(DatabaseAdapter):
    """PostgreSQL database adapter using psycopg.

    Requires the 'postgresql' extra to be installed:
        pip install bamboo_database[postgresql]
    """

    def __init__(self, profile: DatabaseProfile) -> None:
        """Initialize the PostgreSQL adapter.

        Args:
            profile: Database profile with connection settings
        """
        self._profile = profile
        self._connection: Any = None
        self._cursor: Any = None

    def connect(self) -> None:
        """Establish connection to PostgreSQL database."""
        try:
            import psycopg
        except ImportError as e:
            raise ImportError(
                "psycopg is required for PostgreSQL support. "
                "Install it with: pip install bamboo_database[postgresql]"
            ) from e

        self._connection = psycopg.connect(
            host=self._profile.host,
            port=self._profile.get_port(),
            dbname=self._profile.database,
            user=self._profile.user,
            password=self._profile.password,
            autocommit=False,
        )
        self._cursor = self._connection.cursor()

    def disconnect(self) -> None:
        """Close the PostgreSQL connection."""
        if self._cursor:
            self._cursor.close()
            self._cursor = None
        if self._connection:
            self._connection.close()
            self._connection = None

    def execute(self, sql: str, params: tuple[Any, ...] | None = None) -> None:
        """Execute a SQL statement."""
        self._ensure_connected()
        if params:
            self._cursor.execute(sql, params)
        else:
            self._cursor.execute(sql)

    def fetch_all(self, sql: str, params: tuple[Any, ...] | None = None) -> list[dict[str, Any]]:
        """Execute a query and return all results."""
        self._ensure_connected()
        if params:
            self._cursor.execute(sql, params)
        else:
            self._cursor.execute(sql)

        columns = [desc[0] for desc in self._cursor.description or []]
        return [dict(zip(columns, row)) for row in self._cursor.fetchall()]

    def fetch_one(self, sql: str, params: tuple[Any, ...] | None = None) -> dict[str, Any] | None:
        """Execute a query and return the first result."""
        self._ensure_connected()
        if params:
            self._cursor.execute(sql, params)
        else:
            self._cursor.execute(sql)

        row = self._cursor.fetchone()
        if row is None:
            return None

        columns = [desc[0] for desc in self._cursor.description or []]
        return dict(zip(columns, row))

    def begin_transaction(self) -> None:
        """Begin a transaction (PostgreSQL starts transactions automatically)."""
        self._ensure_connected()
        # psycopg with autocommit=False starts transactions automatically

    def commit(self) -> None:
        """Commit the current transaction."""
        self._ensure_connected()
        if self._connection:
            self._connection.commit()

    def rollback(self) -> None:
        """Rollback the current transaction."""
        self._ensure_connected()
        if self._connection:
            self._connection.rollback()

    @property
    def is_connected(self) -> bool:
        """Check if connected to the database."""
        return self._connection is not None and not self._connection.closed

    def _ensure_connected(self) -> None:
        """Ensure the adapter is connected."""
        if not self.is_connected:
            raise RuntimeError("Not connected to database. Call connect() first.")
