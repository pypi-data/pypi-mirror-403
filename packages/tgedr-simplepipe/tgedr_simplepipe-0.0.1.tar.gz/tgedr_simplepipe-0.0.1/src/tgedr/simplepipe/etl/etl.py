"""ETL framework for extract, transform, load operations.

This module provides an abstract base class for ETL processes, utility decorators for configuration injection,
and a dummy implementation for testing or demonstration purposes.
"""

import inspect
import logging
from abc import ABC, abstractmethod
from typing import Any

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


class EtlException(Exception):
    """Custom exception for errors raised during ETL operations."""


"""
ETL is an abstract base class that should be extended when you want to run an ETL-like task/job
A subclass of ETL has extract, transform and load methods.

The ETL class has static utility methods that serve as an outline for the class. Use example below:

```python
class MyEtl(Etl):
    @Etl.inject_configuration
    def extract(self, MY_PARAM) -> None:
        # "MY_PARAM" should be supplied in 'configuration' dict otherwise an exception will be raised

    @Etl.inject_configuration
    def load(self, NOT_IN_CONFIG=123) -> None:
        # If you try to inject a configuration key that is NOT on the configuration dictionary
        # supplied to the constructor, it will not throw an error as long as you set a default
        # value in the method you wish to decorate
        assert NOT_IN_CONFIG == 123, "This will be ok"

```
"""


class Etl(ABC):  # pragma: no cover
    """Abstract base class for ETL (Extract, Transform, Load) processes.

    Subclasses should implement the extract, transform, and load methods.
    Provides utility methods for configuration injection and validation.

    Attributes
    ----------
    _configuration : dict[str, Any] or None
        Configuration dictionary for parameter injection.

    Methods
    -------
    extract() -> Any
        Abstract method to extract data.
    transform() -> Any
        Abstract method to transform data.
    load() -> Any
        Abstract method to load data.
    validate_extract()
        Optional extra checks for extract step.
    validate_transform()
        Optional extra checks for transform step.
    run() -> Any
        Runs the ETL process: extract, validate_extract, transform, validate_transform, load.
    inject_configuration(f)
        Static method decorator for injecting configuration parameters into methods.

    """

    def __init__(self, configuration: dict[str, Any] | None = None) -> None:  # pragma: no cover
        """Initialize a new instance of ETL.

        Args:
            configuration : dict[str, Any]
                source for configuration injection

        """
        self._configuration = configuration

    @abstractmethod
    def extract(self) -> Any:  # pragma: no cover
        """Extract data from the source."""
        raise NotImplementedError

    @abstractmethod
    def transform(self) -> Any:  # pragma: no cover
        """Transform the extracted data."""
        raise NotImplementedError

    @abstractmethod
    def load(self) -> Any:  # pragma: no cover
        """Load the transformed data to the target destination."""
        raise NotImplementedError

    def validate_extract(self) -> None:  # noqa: B027   # pragma: no cover
        """Optional extra checks for extract step."""

    def validate_transform(self) -> None:  # noqa: B027   # pragma: no cover
        """Optional extra checks for transform step."""

    def run(self) -> Any:  # pragma: no cover
        """Runs the ETL process.

        By executing extract, validate_extract, transform, validate_transform, and load steps in order.

        Returns:
            Any
                The result of the load step.

        """
        logger.info("[run|in]")

        self.extract()
        self.validate_extract()

        self.transform()
        self.validate_transform()

        result: Any = self.load()

        logger.info(f"[run|out] => {result}")
        return result

    @staticmethod
    def inject_configuration(f):  # noqa: ANN001, ANN205, D102
        def decorator(self):  # noqa: ANN001, ANN202
            signature = inspect.signature(f)

            missing_params = []
            params = {}
            for param in [parameter for parameter in signature.parameters if parameter != "self"]:
                if signature.parameters[param].default != inspect._empty:  # noqa: SLF001
                    params[param] = signature.parameters[param].default
                else:
                    params[param] = None
                    if self._configuration is None or param not in self._configuration:
                        missing_params.append(param)

                if self._configuration is not None and param in self._configuration:
                    params[param] = self._configuration[param]

            if 0 < len(missing_params):
                msg = f"missing required configuration parameters: {missing_params}"
                raise EtlException(msg)

            return f(
                self,
                *[params[argument] for argument in params],
            )

        return decorator
