"""Sentiment analysis ETL pipeline module.

This module provides the SentimentEtl class for performing Extract, Transform,
and Load operations on text data using pre-trained transformer models for
sentiment analysis.
"""

import json
import logging
from pathlib import Path
from typing import Any
import pandas as pd
from transformers import pipeline
from tgedr.simplepipe.etl.etl import Etl
from tgedr.simplepipe.store.store import Store
from tgedr.simplepipe.utils.validation.data_validation import DataValidation, DataValidationException


logger = logging.getLogger(__name__)

class SentimentEtl(Etl):
    """Sentiment analysis ETL pipeline.

    This class performs Extract, Transform, and Load operations for sentiment
    analysis on text data using a pre-trained transformer model.

    Attributes
    ----------
    __MODEL_ID : str
        The model identifier for the sentiment analysis transformer.
    _data : pd.DataFrame
        The extracted data before transformation.
    _result : pd.DataFrame
        The transformed data with sentiment analysis results.

    """

    __MODEL_ID = "cross-encoder/ms-marco-TinyBERT-L-2-v2"

    def __init__(self, configuration: dict[str, Any] | None = None) -> None:  # pragma: no cover
        """Initialize the SentimentEtl instance.

        Parameters
        ----------
        configuration : dict[str, Any] | None, optional
            Configuration dictionary for the ETL process, by default None.

        """
        super().__init__(configuration)
        self._data: pd.DataFrame = None
        self._result: pd.DataFrame = None

    @Etl.inject_configuration
    def extract(self, new_data_url: str) -> None:
        """Extract data from the specified URL.

        Parameters
        ----------
        new_data_url : str
            The URL or path where the data should be extracted from.

        """
        logger.info(f"[extract|in] ({new_data_url})")

        store: Store = Store.get_default_instance()
        self._data = store.get(new_data_url)
        logger.info(f"[extract] data extracted successfully with shape: {self._data.shape}")

        logger.info("[extract|out]")

    def transform(self) -> None:
        """Transform the extracted data by performing sentiment analysis."""
        logger.info("[transform|in]")

        classifier = pipeline(
            "sentiment-analysis",
            model=self.__MODEL_ID,
            tokenizer=self.__MODEL_ID
        )
        results = pd.DataFrame(classifier(self._data["description"].tolist()))
        self._result = pd.concat([self._data, results], axis=1)
        logger.info(f"[transform] data transformed successfully with shape: {self._result.shape}")

        logger.info("[transform|out]")

    @Etl.inject_configuration
    def load(self, data_url: str) -> None:
        """Load the transformed sentiment data to the specified location.

        Parameters
        ----------
        data_url : str
            The URL or path where the transformed data should be saved.

        """
        logger.info(f"[load|in] ({data_url})")

        store: Store = Store.get_default_instance()
        store.save(self._result, data_url, partition_fields=["ticker"], append=True)
        logger.info(f"[load] appended new articles dataset with shape {self._result.shape} to {data_url}")

        logger.info("[load|out]")

    def _load_data_expectations(self, data_spec_url: str) -> dict[str, Any]:
        """Load data specification from a JSON file.

        Parameters
        ----------
        data_spec_url : str
            The URL or path to the data specification JSON file.

        Returns
        -------
        dict[str, Any]
            The loaded data specification.

        Raises
        ------
        ValueError
            If the data specification cannot be loaded from JSON.

        """
        logger.info(f"[_load_data_expectations|in] ({data_spec_url})")

        expectations = None
        try:
            with Path(data_spec_url).open() as file:
              expectations = json.load(file)
        except Exception as x:  # pragma: no cover
            msg = "[_load_data_expectations] could not load data expectations from JSON"
            raise ValueError(msg) from x  # pragma: no cover

        return expectations

    @Etl.inject_configuration
    def validate_transform(self, data_spec_url: str) -> None:
        """Validate the extracted data against provided expectations.

        Parameters
        ----------
        data_spec_url : str
            The URL or path to the data specification json file.

        Raises
        ------
        ValueError: If expectations cannot be loaded from JSON.
        DataValidationException: If validation fails for any table.

        """
        logger.info(f"[validate_transform|in] ({data_spec_url})")

        expectations = self._load_data_expectations(data_spec_url)["sentiment"]
        validation: DataValidation = DataValidation.get_default_instance()

        validation_outcome = validation.validate(df=self._result, expectations=expectations)
        if validation_outcome["success"] is not True:
            exc_msg = validation_outcome["results"]
            error_message = f"[validate_transform] expectations validation failed: {exc_msg}"
            raise DataValidationException(error_message)
        logger.info("[validate_transform] expectations validation succeeded")

        logger.info("[validate_transform|out]")
