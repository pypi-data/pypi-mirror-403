"""Abstract base classes and utilities for data validation using Great Expectations.

This module defines the DataValidation abstract base class, a custom exception for validation errors,
and a factory method for loading concrete validation implementations.
"""

import logging
from abc import ABC, abstractmethod
from typing import Any
from great_expectations.core import ExpectationSuite
from great_expectations.dataset import PandasDataset



logger = logging.getLogger(__name__)


class DataValidationException(Exception):
  """Custom exception raised for data validation errors."""


class DataValidation(ABC):
  """Abstract base class for data validation using Great Expectations.

  Subclasses should implement the _get_dataset method to convert input data
  into a Great Expectations Dataset for validation.
  """

  @abstractmethod
  def _get_dataset(self, df: Any) -> PandasDataset:
      """Convert a Pandas DataFrame into a Great Expectations PandasDataset."""


  @staticmethod
  def get_default_instance() -> "DataValidation":  # pragma: no cover
      """Factory method to get an instance of a DataValidation subclass.

      Uses lazy import to avoid circular dependency.

      Returns:
          DataValidation: An instance of a DataValidation subclass.

      """
      from tgedr.simplepipe.utils.validation.pandas_validation import PandasValidation
      return PandasValidation()


  def validate(self, df: Any, expectations: dict) -> None:
    """Validate the given data against the provided expectations using Great Expectations.

    Args:
    df (Any): The input data to validate.
    expectations (dict): The expectations suite to validate against.

    Returns:
    dict: The validation result as a JSON-serializable dictionary.

    Raises:
    DataValidationException: If validation fails or an error occurs.

    """
    logger.info(f"[validate|in] ({df}, {expectations})")

    try:
      dataset = self._get_dataset(df)

      validation = dataset.validate(expectation_suite=ExpectationSuite(**expectations), only_return_failures=True)
      result = validation.to_json_dict()
    except Exception as x: # pragma: no cover
      msg = "[validate] failed data expectations"
      raise DataValidationException(msg) from x # pragma: no cover

    logger.info(f"[validate|out] => {result['success']}")
    return result
