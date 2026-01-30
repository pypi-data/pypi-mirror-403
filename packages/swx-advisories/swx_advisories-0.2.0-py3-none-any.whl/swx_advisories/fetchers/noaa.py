"""NOAA/SWPC advisory fetcher for JSON API, FTP archive, and local files."""

import io
import json
import logging
import re
import sys
import urllib.request
import zipfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable, Iterator, Optional, Union

# Type alias for progress callbacks
# Callback receives (message: str, current: int, total: int)
# current/total are 0 when not applicable (e.g., downloading)
ProgressCallback = Callable[[str, int, int], None]

from swx_advisories.fetchers.base import BaseFetcher, FetchResult
from swx_advisories.models.advisory import SpaceWeatherAdvisory
from swx_advisories.models.enums import EventType, MessageType
from swx_advisories.parsers.noaa import NOAAParser

logger = logging.getLogger(__name__)

# NOAA SWPC JSON API endpoint
NOAA_ALERTS_URL = "https://services.swpc.noaa.gov/products/alerts.json"

# NOAA FTP archive base URL
NOAA_FTP_ARCHIVE_URL = "ftp://ftp.swpc.noaa.gov/pub/alerts/"


class NOAAFetcher(BaseFetcher[SpaceWeatherAdvisory]):
    """
    Fetch NOAA/SWPC space weather alerts.

    Can fetch from:
    - NOAA SWPC JSON API (default)
    - Local JSON or HTML file
    - Raw JSON string

    Usage:
        # Fetch from live API
        fetcher = NOAAFetcher()
        result = fetcher.fetch()

        for alert in result:
            print(f"{alert.advisory_id}: {alert.event_type}")

        # Fetch from local JSON file
        fetcher = NOAAFetcher(from_file="/path/to/alerts.json")
        result = fetcher.fetch()

        # Fetch from local HTML archive file
        fetcher = NOAAFetcher(from_file="/path/to/alerts_202601.html")
        result = fetcher.fetch()

        # Filter by event type
        geomag_alerts = fetcher.fetch_by_type(EventType.GEOMAGNETIC_STORM)

    For FTP archive access, use NOAAArchiveFetcher instead.
    """

    def __init__(
        self,
        url: str = NOAA_ALERTS_URL,
        timeout: float = 30.0,
        from_file: Optional[Union[str, Path]] = None,
    ):
        """
        Initialize NOAA fetcher.

        Args:
            url: URL of the NOAA alerts JSON API
            timeout: HTTP request timeout in seconds
            from_file: Optional path to local file (JSON or HTML, overrides URL)
        """
        self.url = url
        self.timeout = timeout
        self.from_file = Path(from_file) if from_file else None
        self._parser = NOAAParser()

    def fetch(self) -> FetchResult[SpaceWeatherAdvisory]:
        """
        Fetch all alerts from the configured source.

        Returns:
            FetchResult containing parsed SpaceWeatherAdvisory objects
        """
        advisories = []
        errors = []
        source_url = None
        source_path = None

        try:
            if self.from_file:
                source_path = str(self.from_file)
                advisories = list(self._fetch_from_file())
            else:
                source_url = self.url
                advisories = list(self._fetch_from_api())
        except Exception as e:
            errors.append(str(e))
            logger.error(f"Failed to fetch NOAA alerts: {e}")

        return FetchResult(
            advisories=advisories,
            fetch_time=datetime.now(timezone.utc),
            source_url=source_url,
            source_path=source_path,
            errors=errors,
        )

    def fetch_iter(self) -> Iterator[SpaceWeatherAdvisory]:
        """
        Fetch alerts as an iterator.

        Yields:
            SpaceWeatherAdvisory objects
        """
        if self.from_file:
            yield from self._fetch_from_file()
        else:
            yield from self._fetch_from_api()

    def _fetch_from_api(self) -> Iterator[SpaceWeatherAdvisory]:
        """Fetch from NOAA JSON API."""
        try:
            import httpx
        except ImportError:
            raise ImportError(
                "httpx is required for API fetching. Install with: pip install httpx"
            )

        logger.info(f"Fetching NOAA alerts from {self.url}")

        with httpx.Client(timeout=self.timeout) as client:
            response = client.get(self.url)
            response.raise_for_status()
            data = response.json()

        logger.info(f"Received {len(data)} alerts from NOAA API")
        yield from self._parser.parse_json(data)

    def _fetch_from_file(self) -> Iterator[SpaceWeatherAdvisory]:
        """Fetch from local JSON or HTML file."""
        if not self.from_file or not self.from_file.exists():
            raise FileNotFoundError(f"File not found: {self.from_file}")

        logger.info(f"Loading NOAA alerts from {self.from_file}")

        # Detect file type by extension
        suffix = self.from_file.suffix.lower()
        if suffix in (".html", ".htm"):
            yield from self._parser.parse_html_file(str(self.from_file))
        else:
            # Default to JSON
            yield from self._parser.parse_json_file(str(self.from_file))

    def fetch_by_type(
        self,
        event_type: EventType,
    ) -> FetchResult[SpaceWeatherAdvisory]:
        """
        Fetch alerts filtered by event type.

        Args:
            event_type: Type of events to include

        Returns:
            FetchResult containing filtered advisories
        """
        result = self.fetch()
        filtered = [a for a in result.advisories if a.event_type == event_type]
        return FetchResult(
            advisories=filtered,
            fetch_time=result.fetch_time,
            source_url=result.source_url,
            source_path=result.source_path,
            errors=result.errors,
        )

    def fetch_by_message_type(
        self,
        message_type: MessageType,
    ) -> FetchResult[SpaceWeatherAdvisory]:
        """
        Fetch alerts filtered by message type.

        Args:
            message_type: Type of message to include (ALERT, WARNING, etc.)

        Returns:
            FetchResult containing filtered advisories
        """
        result = self.fetch()
        filtered = [a for a in result.advisories if a.message_type == message_type]
        return FetchResult(
            advisories=filtered,
            fetch_time=result.fetch_time,
            source_url=result.source_url,
            source_path=result.source_path,
            errors=result.errors,
        )

    def fetch_active_alerts(self) -> FetchResult[SpaceWeatherAdvisory]:
        """
        Fetch only ALERT type messages (real-time threshold crossings).

        Returns:
            FetchResult containing alert advisories
        """
        return self.fetch_by_message_type(MessageType.ALERT)

    def fetch_warnings(self) -> FetchResult[SpaceWeatherAdvisory]:
        """
        Fetch only WARNING type messages (predicted events).

        Returns:
            FetchResult containing warning advisories
        """
        return self.fetch_by_message_type(MessageType.WARNING)

    def fetch_watches(self) -> FetchResult[SpaceWeatherAdvisory]:
        """
        Fetch only WATCH type messages (potential events).

        Returns:
            FetchResult containing watch advisories
        """
        return self.fetch_by_message_type(MessageType.WATCH)

    @classmethod
    def from_json(cls, data: Union[str, list, dict]) -> FetchResult[SpaceWeatherAdvisory]:
        """
        Parse alerts from raw JSON data.

        Args:
            data: JSON string, list of alert dicts, or single alert dict

        Returns:
            FetchResult containing parsed advisories
        """
        parser = NOAAParser()

        if isinstance(data, str):
            data = json.loads(data)

        if isinstance(data, dict):
            data = [data]

        advisories = list(parser.parse_json(data))
        return FetchResult(
            advisories=advisories,
            fetch_time=datetime.now(timezone.utc),
        )


def _default_progress(message: str, current: int, total: int) -> None:
    """Default progress callback that prints to stderr."""
    if total > 0:
        print(f"\r{message} [{current}/{total}]", end="", file=sys.stderr, flush=True)
        if current >= total:
            print(file=sys.stderr)  # Newline at end
    else:
        print(f"{message}", file=sys.stderr, flush=True)


class NOAAArchiveFetcher(BaseFetcher[SpaceWeatherAdvisory]):
    """
    Fetch NOAA/SWPC alerts from the FTP archive.

    The SWPC maintains an FTP archive of historical alerts at:
    ftp://ftp.swpc.noaa.gov/pub/alerts/

    File naming conventions:
    - alerts_YYYY.zip: Yearly archives for 2002-2014 containing monthly HTML files
    - alerts_YYYYMM.html: Monthly files (2015 onwards)
    - archive_YYYYMMDD.html: Bi-weekly snapshots (1st and 16th of month)

    Usage:
        # Fetch a specific month from FTP (works for any year 2002-present)
        fetcher = NOAAArchiveFetcher()
        result = fetcher.fetch_month(2026, 1)  # Direct HTML file
        result = fetcher.fetch_month(2010, 6)  # Extracted from ZIP archive

        # Fetch an entire year (efficient for 2002-2014 ZIP archives)
        result = fetcher.fetch_year(2010)

        # Fetch with progress feedback
        result = fetcher.fetch_date_range(2013, 1, 2016, 12, on_progress=True)

        # Custom progress callback (e.g., for tqdm)
        def my_progress(msg, current, total):
            print(f"{msg}: {current}/{total}")
        result = fetcher.fetch_date_range(2013, 1, 2016, 12, on_progress=my_progress)

        # Fetch from a local directory of HTML files
        fetcher = NOAAArchiveFetcher(local_path="/path/to/archive")
        result = fetcher.fetch_month(2026, 1)

        # List available files on FTP
        files = fetcher.list_archive_files()
    """

    # Years available as ZIP archives (containing monthly HTML files)
    ZIP_ARCHIVE_YEARS = range(2002, 2015)  # 2002-2014

    def __init__(
        self,
        ftp_url: str = NOAA_FTP_ARCHIVE_URL,
        local_path: Optional[Union[str, Path]] = None,
        timeout: float = 30.0,
    ):
        """
        Initialize NOAA archive fetcher.

        Args:
            ftp_url: Base URL of the FTP archive
            local_path: Optional local directory containing HTML files (overrides FTP)
            timeout: FTP request timeout in seconds
        """
        self.ftp_url = ftp_url.rstrip("/") + "/"
        self.local_path = Path(local_path) if local_path else None
        self.timeout = timeout
        self._parser = NOAAParser()

    def fetch(self) -> FetchResult[SpaceWeatherAdvisory]:
        """
        Fetch all alerts from the configured source.

        For FTP, this fetches the most recent monthly file.
        For local path, this fetches all HTML files in the directory.

        Returns:
            FetchResult containing parsed SpaceWeatherAdvisory objects
        """
        if self.local_path:
            return self._fetch_all_local()
        else:
            # Fetch the most recent month
            now = datetime.now(timezone.utc)
            return self.fetch_month(now.year, now.month)

    def fetch_iter(self) -> Iterator[SpaceWeatherAdvisory]:
        """
        Fetch alerts as an iterator.

        Yields:
            SpaceWeatherAdvisory objects
        """
        result = self.fetch()
        yield from result.advisories

    def fetch_month(self, year: int, month: int) -> FetchResult[SpaceWeatherAdvisory]:
        """
        Fetch alerts for a specific month.

        For years 2002-2014, extracts from yearly ZIP archives.
        For years 2015+, fetches individual monthly HTML files.

        Args:
            year: Year (e.g., 2026)
            month: Month (1-12)

        Returns:
            FetchResult containing parsed advisories
        """
        filename = f"alerts_{year:04d}{month:02d}.html"

        if self.local_path:
            return self._fetch_local_file(filename)
        elif year in self.ZIP_ARCHIVE_YEARS:
            # Extract from yearly ZIP archive
            return self._fetch_month_from_zip(year, month)
        else:
            return self._fetch_ftp_file(filename)

    def fetch_date_range(
        self,
        start_year: int,
        start_month: int,
        end_year: int,
        end_month: int,
        on_progress: Optional[Union[bool, ProgressCallback]] = None,
    ) -> FetchResult[SpaceWeatherAdvisory]:
        """
        Fetch alerts for a range of months.

        Args:
            start_year: Start year
            start_month: Start month (1-12)
            end_year: End year
            end_month: End month (1-12)
            on_progress: Progress callback. Pass True for default output to stderr,
                or a callable(message, current, total) for custom handling.

        Returns:
            FetchResult containing parsed advisories from all months
        """
        # Resolve progress callback
        progress: Optional[ProgressCallback] = None
        if on_progress is True:
            progress = _default_progress
        elif callable(on_progress):
            progress = on_progress

        all_advisories = []
        all_errors = []

        # Build list of fetch tasks (optimize by fetching whole years from ZIP when possible)
        tasks = self._plan_fetch_tasks(start_year, start_month, end_year, end_month)
        total_tasks = len(tasks)

        for i, task in enumerate(tasks, 1):
            task_type, year, month = task

            if progress:
                if task_type == "year":
                    progress(f"Fetching year {year}", i, total_tasks)
                else:
                    progress(f"Fetching {year}-{month:02d}", i, total_tasks)

            if task_type == "year":
                result = self._fetch_year_from_zip(year)
            else:
                result = self.fetch_month(year, month)

            all_advisories.extend(result.advisories)
            all_errors.extend(result.errors)

        return FetchResult(
            advisories=all_advisories,
            fetch_time=datetime.now(timezone.utc),
            source_url=self.ftp_url if not self.local_path else None,
            source_path=str(self.local_path) if self.local_path else None,
            errors=all_errors,
        )

    def _plan_fetch_tasks(
        self,
        start_year: int,
        start_month: int,
        end_year: int,
        end_month: int,
    ) -> list[tuple[str, int, int]]:
        """
        Plan fetch tasks, optimizing for ZIP archives where possible.

        Returns list of (task_type, year, month) tuples where:
        - task_type is "year" for full year fetches or "month" for single months
        - month is 0 for year fetches
        """
        tasks = []
        year, month = start_year, start_month

        while (year, month) <= (end_year, end_month):
            # Check if we can fetch a full year from ZIP
            if (
                not self.local_path
                and year in self.ZIP_ARCHIVE_YEARS
                and month == 1
                and (year < end_year or (year == end_year and end_month == 12))
            ):
                # Fetch entire year
                tasks.append(("year", year, 0))
                year += 1
                month = 1
            else:
                # Fetch individual month
                tasks.append(("month", year, month))
                month += 1
                if month > 12:
                    month = 1
                    year += 1

        return tasks

    def list_archive_files(self) -> list[str]:
        """
        List available files in the FTP archive.

        Returns:
            List of filenames available on the FTP server
        """
        if self.local_path:
            return sorted(f.name for f in self.local_path.glob("*.html"))

        logger.info(f"Listing FTP directory: {self.ftp_url}")

        try:
            with urllib.request.urlopen(self.ftp_url, timeout=self.timeout) as response:
                content = response.read().decode("utf-8")
                # FTP directory listing is in detailed format:
                # -rw-rw-r--   1 ftp  ftp  432823 Apr 28  2015 alerts_2002.zip
                # Extract just the filename (last field)
                files = []
                for line in content.split("\n"):
                    line = line.strip()
                    if not line:
                        continue
                    # Split on whitespace and take the last field
                    parts = line.split()
                    if parts:
                        filename = parts[-1]
                        files.append(filename)
                return sorted(files)
        except Exception as e:
            logger.error(f"Failed to list FTP archive: {e}")
            return []

    def list_monthly_files(self) -> list[str]:
        """
        List available monthly files (alerts_YYYYMM.html).

        Returns:
            List of monthly filenames sorted chronologically
        """
        all_files = self.list_archive_files()
        monthly = [f for f in all_files if re.match(r"alerts_\d{6}\.html", f)]
        return sorted(monthly)

    def list_yearly_archives(self) -> list[str]:
        """
        List available yearly ZIP archives (alerts_YYYY.zip).

        Returns:
            List of yearly archive filenames sorted chronologically
        """
        all_files = self.list_archive_files()
        yearly = [f for f in all_files if re.match(r"alerts_\d{4}\.zip", f)]
        return sorted(yearly)

    def fetch_year(
        self,
        year: int,
        on_progress: Optional[Union[bool, ProgressCallback]] = None,
    ) -> FetchResult[SpaceWeatherAdvisory]:
        """
        Fetch all alerts for an entire year.

        For years 2002-2014, downloads the yearly ZIP archive and extracts
        all monthly files. For years 2015+, fetches each month individually.

        Args:
            year: Year (e.g., 2010)
            on_progress: Progress callback. Pass True for default output to stderr,
                or a callable(message, current, total) for custom handling.

        Returns:
            FetchResult containing parsed advisories for all months
        """
        # Resolve progress callback
        progress: Optional[ProgressCallback] = None
        if on_progress is True:
            progress = _default_progress
        elif callable(on_progress):
            progress = on_progress

        if self.local_path:
            # Fetch all months from local files
            return self.fetch_date_range(year, 1, year, 12, on_progress=on_progress)

        if year in self.ZIP_ARCHIVE_YEARS:
            if progress:
                progress(f"Downloading alerts_{year}.zip", 0, 0)
            return self._fetch_year_from_zip(year)
        else:
            # Fetch each month individually
            return self.fetch_date_range(year, 1, year, 12, on_progress=on_progress)

    def _fetch_year_from_zip(self, year: int) -> FetchResult[SpaceWeatherAdvisory]:
        """Fetch all months from a yearly ZIP archive."""
        zip_filename = f"alerts_{year}.zip"
        url = self.ftp_url + zip_filename
        logger.info(f"Fetching yearly archive from FTP: {url}")

        all_advisories = []
        errors = []

        try:
            # Download the ZIP file
            zip_data = self._download_zip(url)

            # Extract and parse all monthly HTML files
            with zipfile.ZipFile(io.BytesIO(zip_data)) as zf:
                # Find monthly files (alerts_YYYYMM.html)
                monthly_pattern = re.compile(rf"alerts_{year}\d{{2}}\.html")
                monthly_files = sorted(
                    name for name in zf.namelist()
                    if monthly_pattern.match(name)
                )

                logger.info(f"Found {len(monthly_files)} monthly files in {zip_filename}")

                for filename in monthly_files:
                    try:
                        content = zf.read(filename).decode("utf-8", errors="replace")
                        advisories = list(self._parser.parse_html(content))
                        all_advisories.extend(advisories)
                        logger.info(f"Parsed {len(advisories)} alerts from {filename}")
                    except Exception as e:
                        error_msg = f"Error processing {filename} from ZIP: {e}"
                        logger.error(error_msg)
                        errors.append(error_msg)

        except Exception as e:
            error_msg = f"Failed to fetch {url}: {e}"
            logger.error(error_msg)
            errors.append(error_msg)

        return FetchResult(
            advisories=all_advisories,
            fetch_time=datetime.now(timezone.utc),
            source_url=url,
            errors=errors,
        )

    def _fetch_month_from_zip(self, year: int, month: int) -> FetchResult[SpaceWeatherAdvisory]:
        """Fetch a single month from a yearly ZIP archive."""
        zip_filename = f"alerts_{year}.zip"
        html_filename = f"alerts_{year:04d}{month:02d}.html"
        url = self.ftp_url + zip_filename
        logger.info(f"Fetching {html_filename} from {zip_filename}")

        advisories = []
        errors = []

        try:
            # Download the ZIP file
            zip_data = self._download_zip(url)

            # Extract the specific monthly file
            with zipfile.ZipFile(io.BytesIO(zip_data)) as zf:
                if html_filename in zf.namelist():
                    content = zf.read(html_filename).decode("utf-8", errors="replace")
                    advisories = list(self._parser.parse_html(content))
                    logger.info(f"Parsed {len(advisories)} alerts from {html_filename}")
                else:
                    error_msg = f"File {html_filename} not found in {zip_filename}"
                    logger.error(error_msg)
                    errors.append(error_msg)

        except Exception as e:
            error_msg = f"Failed to fetch {html_filename} from {url}: {e}"
            logger.error(error_msg)
            errors.append(error_msg)

        return FetchResult(
            advisories=advisories,
            fetch_time=datetime.now(timezone.utc),
            source_url=url,
            errors=errors,
        )

    def _download_zip(self, url: str) -> bytes:
        """Download a ZIP file from FTP."""
        # Use a longer timeout for ZIP files which can be larger
        timeout = max(self.timeout, 60.0)
        with urllib.request.urlopen(url, timeout=timeout) as response:
            return response.read()

    def _fetch_ftp_file(self, filename: str) -> FetchResult[SpaceWeatherAdvisory]:
        """Fetch a single file from FTP."""
        url = self.ftp_url + filename
        logger.info(f"Fetching from FTP: {url}")

        advisories = []
        errors = []

        try:
            with urllib.request.urlopen(url, timeout=self.timeout) as response:
                content = response.read().decode("utf-8", errors="replace")

            advisories = list(self._parser.parse_html(content))
            logger.info(f"Parsed {len(advisories)} alerts from {filename}")

        except urllib.error.URLError as e:
            error_msg = f"Failed to fetch {url}: {e}"
            logger.error(error_msg)
            errors.append(error_msg)
        except Exception as e:
            error_msg = f"Error processing {filename}: {e}"
            logger.error(error_msg)
            errors.append(error_msg)

        return FetchResult(
            advisories=advisories,
            fetch_time=datetime.now(timezone.utc),
            source_url=url,
            errors=errors,
        )

    def _fetch_local_file(self, filename: str) -> FetchResult[SpaceWeatherAdvisory]:
        """Fetch a single file from local directory."""
        if not self.local_path:
            raise ValueError("No local path configured")

        filepath = self.local_path / filename
        logger.info(f"Loading from local file: {filepath}")

        advisories = []
        errors = []

        if not filepath.exists():
            error_msg = f"File not found: {filepath}"
            logger.error(error_msg)
            errors.append(error_msg)
        else:
            try:
                advisories = list(self._parser.parse_html_file(str(filepath)))
                logger.info(f"Parsed {len(advisories)} alerts from {filename}")
            except Exception as e:
                error_msg = f"Error processing {filepath}: {e}"
                logger.error(error_msg)
                errors.append(error_msg)

        return FetchResult(
            advisories=advisories,
            fetch_time=datetime.now(timezone.utc),
            source_path=str(filepath),
            errors=errors,
        )

    def _fetch_all_local(self) -> FetchResult[SpaceWeatherAdvisory]:
        """Fetch all HTML files from local directory."""
        if not self.local_path or not self.local_path.exists():
            raise FileNotFoundError(f"Directory not found: {self.local_path}")

        all_advisories = []
        all_errors = []

        for html_file in sorted(self.local_path.glob("*.html")):
            try:
                advisories = list(self._parser.parse_html_file(str(html_file)))
                all_advisories.extend(advisories)
                logger.info(f"Parsed {len(advisories)} alerts from {html_file.name}")
            except Exception as e:
                error_msg = f"Error processing {html_file}: {e}"
                logger.error(error_msg)
                all_errors.append(error_msg)

        return FetchResult(
            advisories=all_advisories,
            fetch_time=datetime.now(timezone.utc),
            source_path=str(self.local_path),
            errors=all_errors,
        )
