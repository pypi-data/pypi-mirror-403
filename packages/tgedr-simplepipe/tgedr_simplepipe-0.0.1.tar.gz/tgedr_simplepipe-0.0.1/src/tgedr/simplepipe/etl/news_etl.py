"""ETL process for fetching, transforming, and loading news articles.

This module provides the NewsEtl class which orchestrates the extraction,
transformation, and loading of news articles from external sources into
a Parquet data store.
"""

import logging
from typing import Any
from datetime import datetime, UTC
import tempfile
import pandas as pd
from tgedr.simplepipe.etl.etl import Etl
from tgedr.simplepipe.news.article import Article
from tgedr.simplepipe.news.fetcher import ArticleFetcher
from tgedr.simplepipe.store.store import Store

logger = logging.getLogger(__name__)

class NewsEtl(Etl):
    """ETL process for fetching, transforming, and loading news articles."""

    def __init__(self, configuration: dict[str, Any] | None = None) -> None:  # pragma: no cover
        """Initialize NewsEtl with optional configuration.

        Args:
            configuration : dict[str, Any]
                source for configuration injection

        """
        super().__init__(configuration)
        self._data: list[Article] = []
        self._result: pd.DataFrame = None

    @Etl.inject_configuration
    def extract(self, tickers: str) -> None:
        """Extract news articles from a data source.

        Returns:
            list: List of raw news article data.

        """
        logger.info(f"[extract|in] ({tickers})")

        ticker_list = [x.strip() for x in tickers.split(",")]
        fetcher = ArticleFetcher.get_default_instance()
        ts_end = int(datetime.now(tz=UTC).timestamp())
        ts_start = ts_end - 86400  # 1 day ago
        for ticker in ticker_list:
            self._data.extend(fetcher.get_stock_news(ticker, ts_start, ts_end))

        logger.info("[extract|out]")

    def transform(self) -> None:
        """Transform raw news article data into Article objects.

        Returns:
            Dataframe: DataFrame of transformed Article objects.

        """
        logger.info("[transform|in]")
        self._result = pd.DataFrame([x.to_pd_df_row() for x in self._data])
        logger.info("[transform|out]")

    def load(self) -> str:
        """Load transformed Article objects into a temporary destination.

        Returns:
            str: Path to the temporary directory where the parquet file was saved.

        """
        logger.info("[load|in]")
        output_path = tempfile.mkdtemp(prefix="news_etl_")
        store: Store = Store.get_default_instance()
        store.save(self._result, output_path, partition_fields=["ticker"], append=True)
        logger.info(f"[load] saved articles dataset with shape {self._result.shape} to {output_path}")
        logger.info(f"[load|out] => {output_path}")
        return output_path
