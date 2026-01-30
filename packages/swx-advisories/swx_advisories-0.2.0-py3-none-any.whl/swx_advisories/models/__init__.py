"""Data models for space weather advisories."""

from swx_advisories.models.enums import (
    EventType,
    MessageType,
    Severity,
    Source,
    Status,
)
from swx_advisories.models.location import GeographicRegion, LatitudeBand
from swx_advisories.models.advisory import (
    SpaceWeatherAdvisory,
    ICAOAdvisory,
    ICAOEvent,
    Forecast,
    TemporalObservation,
)

__all__ = [
    # Enums
    "EventType",
    "MessageType",
    "Severity",
    "Source",
    "Status",
    # Location
    "GeographicRegion",
    "LatitudeBand",
    # Advisory models
    "SpaceWeatherAdvisory",
    "ICAOAdvisory",
    "ICAOEvent",
    "Forecast",
    "TemporalObservation",
]
