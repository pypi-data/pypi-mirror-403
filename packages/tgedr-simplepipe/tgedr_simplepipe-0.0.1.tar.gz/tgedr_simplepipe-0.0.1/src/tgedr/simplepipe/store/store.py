"""Store module providing abstract base classes and exceptions for data persistence operations."""

import abc
from typing import Any


class StoreException(Exception):  # pragma: no cover
    """Base exception for errors raised by store operations."""


class NoStoreException(StoreException):  # pragma: no cover
    """Exception raised when no store is available or configured."""


class Store(abc.ABC):  # pragma: no cover
    """abstract class used to manage persistence, defining CRUD-like (CreateReadUpdateDelete) methods."""

    @staticmethod
    def get_default_instance() -> "Store":  # pragma: no cover
        """Factory method to get an instance of a Store subclass.

        Uses lazy import to avoid circular dependency with ParquetStore.

        Returns:
            Store: An instance of a Store subclass.

        """
        from tgedr.simplepipe.store.parquet_store import ParquetStore
        return ParquetStore()

    def __init__(self, config: dict[str, int | str | float] | None = None) -> None:  # pragma: no cover
        """Initialize the Store with an optional configuration dictionary.

        Parameters
        ----------
        config : dict[str, int | str | float] or None, optional
            Configuration parameters for the store.

        """
        self._config = config

    @abc.abstractmethod
    def get(self, key: str, **kwargs) -> Any:  # pragma: no cover  # noqa: ANN003
        """Retrieve an object from the store by its key.

        Parameters
        ----------
        key : str
            The key identifying the object to retrieve.
        **kwargs
            Additional arguments for retrieval.

        Returns
        -------
        Any
            The object associated with the given key.

        Raises
        ------
        NotImplementedError
            If the method is not implemented by a subclass.

        """
        raise NotImplementedError

    @abc.abstractmethod
    def delete(self, key: str, **kwargs) -> None:  # pragma: no cover  # noqa: ANN003
        """Delete an object from the store by its key.

        Parameters
        ----------
        key : str
            The key identifying the object to delete.
        **kwargs
            Additional arguments for deletion.

        Raises
        ------
        NotImplementedError
            If the method is not implemented by a subclass.

        """
        raise NotImplementedError

    @abc.abstractmethod
    def save(
        self, df: Any, key: str, partition_fields: list[str] | None = None,
            append: bool = False, **kwargs) -> None:  # pragma: no cover  # noqa: ANN003
        """Save an object to the store under the specified key.

        Parameters
        ----------
        df : Any
            The object to be saved.
        key : str
            The key under which to save the object.
        partition_fields : list[str] or None, optional
            Fields to partition the data by, if applicable.
        append : bool, optional
            Whether to append to an existing object (if supported), by default False
        **kwargs
            Additional arguments for saving.

        Raises
        ------
        NotImplementedError
            If the method is not implemented by a subclass.

        """
        raise NotImplementedError
