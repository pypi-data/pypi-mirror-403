"""News article module.

This module defines data structures for representing news articles.
"""

from dataclasses import dataclass
from datetime import datetime, UTC


@dataclass(frozen=True)
class Article:
    """Data class for news articles.

    Attributes:
        title: Article headline
        description: Article description or summary
        url: URL to the full article
        timestamp: Unix epoch timestamp in seconds (UTC) for the published date
        source: News source name
        ticker: Stock ticker symbol
        id: Unique identifier composed of ticker hash concatenated with timestamp

    """

    title: str
    description: str
    url: str
    timestamp: int
    source: str
    ticker: str

    @property
    def id(self) -> int:
        """Generate a unique identifier from ticker and timestamp.

        Combines the hash of the ticker symbol with the timestamp to create
        a unique integer identifier for this news article. Uses Python's
        built-in hash on a tuple to ensure consistent and collision-resistant IDs.

        Returns:
            int: Unique identifier as integer

        """
        return hash((self.ticker, self.timestamp))

    def to_pd_df_row(self) -> dict[str, object]:
        """Convert Article instance to a dictionary suitable for pandas DataFrame row.

        Returns:
            dict[str, object]: Dictionary with all Article fields including the id property.
                              Keys match the attribute names and can be used directly with
                              pandas DataFrame constructor.

        Example:
            >>> article = Article(
            ...     title="Market Update",
            ...     description="Stock markets rise",
            ...     url="https://example.com/article",
            ...     timestamp=1701388800,
            ...     source="Financial Times",
            ...     ticker="AAPL",
            ... )
            >>> row = article.to_pd_df_row()
            >>> import pandas as pd
            >>> df = pd.DataFrame([row])

        """
        return {
            "id": self.id,
            "ticker": self.ticker,
            "timestamp": self.timestamp,
            "title": self.title,
            "description": self.description,
            "url": self.url,
            "source": self.source,
        }

    def __str__(self) -> str:
        """Return a formatted string representation of the news article.

        Returns:
            str: Formatted string with all article properties, with timestamp in human-readable format.

        """
        # Format timestamp as human-readable date
        formatted_date = datetime.fromtimestamp(self.timestamp, tz=UTC).strftime("%Y-%m-%d %H:%M:%S UTC")

        return (
            f"Article: {formatted_date} - {self.title}\n"
            f"  ticker: {self.ticker}\n"
            f"  description: {self.description}\n"
            f"  source: {self.source} | url: {self.url}\n"
        )
