"""Module for Pandas-based data validation using Great Expectations."""

from typing import Any

import great_expectations as ge
from great_expectations.dataset import PandasDataset

from tgedr.simplepipe.utils.validation.data_validation import DataValidation


class PandasValidation(DataValidation):
    """Implementation of DataValidation using PandasDataset for data validation."""

    def _get_dataset(self, df: Any) -> PandasDataset:
        """Convert a Pandas DataFrame into a Great Expectations PandasDataset."""
        return ge.from_pandas(df)
