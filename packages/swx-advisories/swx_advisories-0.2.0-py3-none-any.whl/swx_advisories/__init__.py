"""
swx-advisories: Space Weather Advisory Parser

Parse and analyze ICAO and NOAA space weather advisories.

Example usage:
    from swx_advisories import ICAOFetcher, NOAAFetcher, to_dataframe

    # Fetch ICAO advisories from files
    icao = ICAOFetcher("/path/to/advisories")
    result = icao.fetch()
    df_events = to_dataframe(result.events)

    # Fetch NOAA alerts from API
    noaa = NOAAFetcher()
    result = noaa.fetch()
"""

from swx_advisories.models.advisory import (
    Forecast,
    ICAOAdvisory,
    ICAOEvent,
    SpaceWeatherAdvisory,
    TemporalObservation,
)
from swx_advisories.models.enums import (
    EventType,
    MessageType,
    Severity,
    Source,
    Status,
)
from swx_advisories.models.location import GeographicRegion, LatitudeBand
from swx_advisories.parsers.icao import ICAOTextParser
from swx_advisories.parsers.noaa import NOAAParser
from swx_advisories.fetchers import (
    ICAOFetcher,
    NOAAArchiveFetcher,
    NOAAFetcher,
    FetchResult,
    ProgressCallback,
)
from swx_advisories.adapters import (
    to_dataframe,
    icao_advisories_to_dataframe,
    icao_events_to_dataframe,
    noaa_alerts_to_dataframe,
)

__version__ = "0.2.0"

__all__ = [
    # Models
    "ICAOAdvisory",
    "ICAOEvent",
    "SpaceWeatherAdvisory",
    "Forecast",
    "TemporalObservation",
    "GeographicRegion",
    "LatitudeBand",
    # Enums
    "EventType",
    "MessageType",
    "Severity",
    "Source",
    "Status",
    # Parsers
    "ICAOTextParser",
    "NOAAParser",
    # Fetchers
    "ICAOFetcher",
    "NOAAArchiveFetcher",
    "NOAAFetcher",
    "FetchResult",
    "ProgressCallback",
    # Adapters
    "to_dataframe",
    "icao_advisories_to_dataframe",
    "icao_events_to_dataframe",
    "noaa_alerts_to_dataframe",
]
