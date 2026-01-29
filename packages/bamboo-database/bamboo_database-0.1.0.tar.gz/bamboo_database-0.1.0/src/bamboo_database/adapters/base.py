"""Abstract base class for database adapters."""

from abc import ABC, abstractmethod
from types import TracebackType
from typing import Any


class DatabaseAdapter(ABC):
    """Abstract base class for database adapters.

    All database adapters must implement these methods to provide
    a consistent interface for database operations.

    Adapters support context manager protocol for automatic connection
    cleanup:

        with create_adapter(profile) as adapter:
            adapter.execute("SELECT 1")
    """

    @abstractmethod
    def connect(self) -> None:
        """Establish connection to the database.

        Raises:
            ConnectionError: If connection cannot be established
        """
        ...

    @abstractmethod
    def disconnect(self) -> None:
        """Close the database connection.

        Should be safe to call multiple times.
        """
        ...

    @abstractmethod
    def execute(self, sql: str, params: tuple[Any, ...] | None = None) -> None:
        """Execute a SQL statement without returning results.

        Args:
            sql: SQL statement to execute
            params: Optional tuple of parameters for parameterized queries

        Raises:
            RuntimeError: If not connected
            DatabaseError: If SQL execution fails
        """
        ...

    @abstractmethod
    def fetch_all(self, sql: str, params: tuple[Any, ...] | None = None) -> list[dict[str, Any]]:
        """Execute a SQL query and return all results.

        Args:
            sql: SQL query to execute
            params: Optional tuple of parameters for parameterized queries

        Returns:
            List of dictionaries, where each dict represents a row
            with column names as keys

        Raises:
            RuntimeError: If not connected
            DatabaseError: If SQL execution fails
        """
        ...

    @abstractmethod
    def fetch_one(self, sql: str, params: tuple[Any, ...] | None = None) -> dict[str, Any] | None:
        """Execute a SQL query and return the first result.

        Args:
            sql: SQL query to execute
            params: Optional tuple of parameters for parameterized queries

        Returns:
            Dictionary representing the first row, or None if no results

        Raises:
            RuntimeError: If not connected
            DatabaseError: If SQL execution fails
        """
        ...

    @abstractmethod
    def begin_transaction(self) -> None:
        """Begin a database transaction.

        Raises:
            RuntimeError: If not connected
        """
        ...

    @abstractmethod
    def commit(self) -> None:
        """Commit the current transaction.

        Raises:
            RuntimeError: If not connected or no active transaction
        """
        ...

    @abstractmethod
    def rollback(self) -> None:
        """Rollback the current transaction.

        Raises:
            RuntimeError: If not connected
        """
        ...

    @property
    @abstractmethod
    def is_connected(self) -> bool:
        """Check if the adapter is currently connected.

        Returns:
            True if connected, False otherwise
        """
        ...

    def __enter__(self) -> "DatabaseAdapter":
        """Enter context manager, establishing connection."""
        self.connect()
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> None:
        """Exit context manager, closing connection."""
        self.disconnect()
