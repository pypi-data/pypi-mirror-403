"""ICAO advisory fetcher for loading from filesystem."""

import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterator, Optional, Union

from swx_advisories.fetchers.base import BaseFetcher, FetchResult
from swx_advisories.models.advisory import ICAOAdvisory, ICAOEvent
from swx_advisories.parsers.icao import ICAOTextParser, ICAOEventBuilder

logger = logging.getLogger(__name__)


class ICAOFetcher(BaseFetcher[ICAOAdvisory]):
    """
    Fetch ICAO advisories from filesystem.

    Loads fnxx01*.txt and fnxx02*.txt files from a directory and parses them
    into ICAOAdvisory objects. Automatically builds event chains.

    Usage:
        # Fetch from a directory
        fetcher = ICAOFetcher("/path/to/advisories")
        result = fetcher.fetch()

        for advisory in result:
            print(advisory.advisory_id)

        # Events are automatically built and available on the result
        for event in result.events:
            print(event.event_id)

        # Disable event building if not needed
        result = fetcher.fetch(build_events=False)
        assert result.events is None
    """

    def __init__(
        self,
        path: Union[str, Path],
        pattern: str = "fnxx0*.txt",
        recursive: bool = False,
    ):
        """
        Initialize ICAO fetcher.

        Args:
            path: Directory or file path to load advisories from
            pattern: Glob pattern for matching files (default: fnxx0*.txt)
            recursive: Whether to search subdirectories
        """
        self.path = Path(path)
        self.pattern = pattern
        self.recursive = recursive
        self._parser = ICAOTextParser()
        self._event_builder = ICAOEventBuilder()

    def fetch(self, build_events: bool = True) -> FetchResult[ICAOAdvisory]:
        """
        Fetch all advisories from the configured path.

        Args:
            build_events: If True (default), build event chains and populate result.events.
                         If False, result.events will be None.

        Returns:
            FetchResult containing parsed ICAOAdvisory objects and optionally events
        """
        advisories = []
        errors = []
        source_path = str(self.path)

        try:
            for advisory in self.fetch_iter():
                advisories.append(advisory)
        except Exception as e:
            errors.append(str(e))

        events = None
        if build_events and advisories:
            events = self._build_events(advisories)

        return FetchResult(
            advisories=advisories,
            fetch_time=datetime.now(timezone.utc),
            source_path=source_path,
            errors=errors,
            events=events,
        )

    def fetch_iter(self) -> Iterator[ICAOAdvisory]:
        """
        Fetch advisories as an iterator.

        Yields:
            ICAOAdvisory objects
        """
        if self.path.is_file():
            yield from self._parser.parse_file(self.path)
        elif self.path.is_dir():
            yield from self._fetch_from_directory()
        else:
            raise ValueError(f"Path does not exist: {self.path}")

    def _fetch_from_directory(self) -> Iterator[ICAOAdvisory]:
        """Fetch from a directory of files."""
        if self.recursive:
            files = sorted(self.path.rglob(self.pattern))
        else:
            files = sorted(self.path.glob(self.pattern))

        if not files:
            logger.warning(f"No files matching '{self.pattern}' found in {self.path}")
            return

        for file_path in files:
            logger.debug(f"Parsing {file_path}")
            try:
                yield from self._parser.parse_file(file_path)
            except Exception as e:
                logger.error(f"Error parsing {file_path}: {e}")

    def _build_events(self, advisories: list[ICAOAdvisory]) -> list[ICAOEvent]:
        """
        Build event chains from advisories.

        Args:
            advisories: List of advisories

        Returns:
            List of ICAOEvent objects
        """
        return self._event_builder.build_events(advisories)

    @classmethod
    def from_text(cls, content: str, build_events: bool = True) -> FetchResult[ICAOAdvisory]:
        """
        Parse advisories from raw text content.

        Args:
            content: Raw text containing one or more advisories
            build_events: If True (default), build event chains and populate result.events.
                         If False, result.events will be None.

        Returns:
            FetchResult containing parsed advisories and optionally events
        """
        parser = ICAOTextParser()
        event_builder = ICAOEventBuilder()
        advisories = list(parser.parse_text(content))

        events = None
        if build_events and advisories:
            events = event_builder.build_events(advisories)

        return FetchResult(
            advisories=advisories,
            fetch_time=datetime.now(timezone.utc),
            events=events,
        )
