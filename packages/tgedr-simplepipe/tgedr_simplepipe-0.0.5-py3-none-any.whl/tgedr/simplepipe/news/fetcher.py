"""Abstract base class for article fetchers.

This module defines the ArticleFetcher abstract base class that establishes
the interface contract for all article fetcher implementations. Following the
Open-Closed Principle, new fetcher implementations can extend this base class
without modifying existing code.
"""

from abc import ABC, abstractmethod

from tgedr.simplepipe.news.article import Article


class ArticleFetcher(ABC):
    """Abstract base class for fetching news articles related to stock tickers.

    This class defines the interface that all concrete article fetcher implementations
    must follow. It enforces a consistent API across different news sources while
    allowing each implementation to handle its specific data source requirements.

    The Open-Closed Principle is applied here: this interface is closed for
    modification but open for extension through concrete implementations.
    """

    @staticmethod
    def get_default_instance() -> "ArticleFetcher":  # pragma: no cover
        """Factory method to get an instance of a ArticleFetcher subclass.

        Uses lazy import to avoid circular dependency.

        Returns:
            ArticleFetcher: An instance of a ArticleFetcher subclass.

        """
        from tgedr.simplepipe.news.finnhub_fetcher import FinnhubNewsFetcher

        return FinnhubNewsFetcher()

    @abstractmethod
    def get_stock_news(
        self,
        ticker: str,
        start_date: int,
        end_date: int | None = None,
        company_name: str | None = None,
        max_articles: int = 100,
    ) -> list[Article]:
        """Fetch news articles for a given stock ticker within a date range.

        This abstract method must be implemented by all concrete fetcher classes.
        Each implementation will fetch articles from its specific data source.

        Args:
            ticker: Stock ticker symbol (e.g., "AAPL", "GOOGL")
            start_date: Start of date range as UTC epoch timestamp (seconds)
            end_date: End of date range as UTC epoch timestamp (seconds).
                     If None, defaults to current time.
            company_name: Optional company name for enhanced search queries.
                         Some APIs can use this for better results.
            max_articles: Maximum number of articles to fetch. Default is 100.

        Returns:
            List of Article objects sorted by timestamp, or empty list on error.

        Raises:
            NotImplementedError: If called directly on the abstract base class.

        """
        raise NotImplementedError
