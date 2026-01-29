"""MySQL database adapter."""

from typing import Any

from bamboo_database.adapters.base import DatabaseAdapter
from bamboo_database.config.models import DatabaseProfile


class MySQLAdapter(DatabaseAdapter):
    """MySQL database adapter using mysql-connector-python.

    Requires the 'mysql' extra to be installed:
        pip install bamboo_database[mysql]
    """

    def __init__(self, profile: DatabaseProfile) -> None:
        """Initialize the MySQL adapter.

        Args:
            profile: Database profile with connection settings
        """
        self._profile = profile
        self._connection: Any = None
        self._cursor: Any = None

    def connect(self) -> None:
        """Establish connection to MySQL database."""
        try:
            import mysql.connector
        except ImportError as e:
            raise ImportError(
                "mysql-connector-python is required for MySQL support. "
                "Install it with: pip install bamboo_database[mysql]"
            ) from e

        self._connection = mysql.connector.connect(
            host=self._profile.host,
            port=self._profile.get_port(),
            database=self._profile.database,
            user=self._profile.user,
            password=self._profile.password or "",
            autocommit=False,
        )
        self._cursor = self._connection.cursor(dictionary=True)

    def disconnect(self) -> None:
        """Close the MySQL connection."""
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
        return list(self._cursor.fetchall())

    def fetch_one(self, sql: str, params: tuple[Any, ...] | None = None) -> dict[str, Any] | None:
        """Execute a query and return the first result."""
        self._ensure_connected()
        if params:
            self._cursor.execute(sql, params)
        else:
            self._cursor.execute(sql)
        return self._cursor.fetchone()

    def begin_transaction(self) -> None:
        """Begin a transaction."""
        self._ensure_connected()
        if self._connection:
            self._connection.start_transaction()

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
        return self._connection is not None and self._connection.is_connected()

    def _ensure_connected(self) -> None:
        """Ensure the adapter is connected."""
        if not self.is_connected:
            raise RuntimeError("Not connected to database. Call connect() first.")
