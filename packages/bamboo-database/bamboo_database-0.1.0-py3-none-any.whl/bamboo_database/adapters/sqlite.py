"""SQLite database adapter."""

import sqlite3
from typing import Any

from bamboo_database.adapters.base import DatabaseAdapter
from bamboo_database.config.models import DatabaseProfile


class SQLiteAdapter(DatabaseAdapter):
    """SQLite database adapter using built-in sqlite3 module.

    This adapter is always available without extra dependencies.
    """

    def __init__(self, profile: DatabaseProfile) -> None:
        """Initialize the SQLite adapter.

        Args:
            profile: Database profile with connection settings
        """
        self._profile = profile
        self._connection: sqlite3.Connection | None = None
        self._cursor: sqlite3.Cursor | None = None

    def connect(self) -> None:
        """Establish connection to SQLite database."""
        if not self._profile.path:
            raise ValueError("SQLite profile must have a 'path' configured")

        self._connection = sqlite3.connect(self._profile.path)
        self._connection.row_factory = sqlite3.Row
        self._cursor = self._connection.cursor()

    def disconnect(self) -> None:
        """Close the SQLite connection."""
        if self._cursor:
            self._cursor.close()
            self._cursor = None
        if self._connection:
            self._connection.close()
            self._connection = None

    def execute(self, sql: str, params: tuple[Any, ...] | None = None) -> None:
        """Execute a SQL statement."""
        self._ensure_connected()
        if self._cursor:
            if params:
                self._cursor.execute(sql, params)
            else:
                self._cursor.execute(sql)

    def fetch_all(self, sql: str, params: tuple[Any, ...] | None = None) -> list[dict[str, Any]]:
        """Execute a query and return all results."""
        self._ensure_connected()
        if not self._cursor:
            return []

        if params:
            self._cursor.execute(sql, params)
        else:
            self._cursor.execute(sql)

        rows = self._cursor.fetchall()
        return [dict(row) for row in rows]

    def fetch_one(self, sql: str, params: tuple[Any, ...] | None = None) -> dict[str, Any] | None:
        """Execute a query and return the first result."""
        self._ensure_connected()
        if not self._cursor:
            return None

        if params:
            self._cursor.execute(sql, params)
        else:
            self._cursor.execute(sql)

        row = self._cursor.fetchone()
        if row is None:
            return None
        return dict(row)

    def begin_transaction(self) -> None:
        """Begin a transaction."""
        self._ensure_connected()
        # SQLite begins transactions automatically when executing statements
        # in autocommit mode (isolation_level=None) or uses implicit transactions

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
        return self._connection is not None

    def _ensure_connected(self) -> None:
        """Ensure the adapter is connected."""
        if not self.is_connected:
            raise RuntimeError("Not connected to database. Call connect() first.")
