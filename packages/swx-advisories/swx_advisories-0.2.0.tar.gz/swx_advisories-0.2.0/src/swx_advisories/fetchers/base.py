"""Base fetcher interface for space weather data sources."""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Generic, Iterator, Optional, TypeVar

from pydantic import BaseModel

# Type variable for advisory types
T = TypeVar("T", bound=BaseModel)


@dataclass
class FetchResult(Generic[T]):
    """Result of a fetch operation."""

    advisories: list[T] = field(default_factory=list)
    fetch_time: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    source_url: Optional[str] = None
    source_path: Optional[str] = None
    errors: list[str] = field(default_factory=list)
    events: Optional[list[Any]] = None  # For ICAO: list[ICAOEvent]

    @property
    def count(self) -> int:
        """Number of advisories fetched."""
        return len(self.advisories)

    @property
    def success(self) -> bool:
        """Whether fetch completed without errors."""
        return len(self.errors) == 0

    def __iter__(self) -> Iterator[T]:
        """Iterate over advisories."""
        return iter(self.advisories)


class BaseFetcher(ABC, Generic[T]):
    """
    Abstract base class for advisory fetchers.

    Fetchers retrieve advisory data from various sources (filesystem, HTTP, FTP)
    and return parsed advisory objects.
    """

    @abstractmethod
    def fetch(self) -> FetchResult[T]:
        """
        Fetch advisories from the data source.

        Returns:
            FetchResult containing parsed advisories and metadata
        """
        pass

    @abstractmethod
    def fetch_iter(self) -> Iterator[T]:
        """
        Fetch advisories as an iterator (for memory efficiency).

        Yields:
            Advisory objects
        """
        pass
