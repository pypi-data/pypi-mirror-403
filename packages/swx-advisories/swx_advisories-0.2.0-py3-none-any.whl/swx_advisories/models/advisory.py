"""Advisory data models."""

from datetime import datetime, timedelta
from typing import Optional

from pydantic import BaseModel, Field, computed_field

from swx_advisories.models.enums import (
    EventType,
    MessageType,
    Severity,
    Source,
    Status,
)
from swx_advisories.models.location import GeographicRegion


class TemporalObservation(BaseModel):
    """A point in time with associated geographic location."""

    time: datetime
    hours_ahead: int = 0  # 0=observation, 6/12/18/24=forecast
    location: GeographicRegion = Field(default_factory=GeographicRegion)

    @property
    def is_observation(self) -> bool:
        return self.hours_ahead == 0

    @property
    def is_forecast(self) -> bool:
        return self.hours_ahead > 0


class Forecast(BaseModel):
    """Forecast for a future time period (ICAO-style)."""

    hours_ahead: int  # 6, 12, 18, 24
    time: datetime
    location: GeographicRegion = Field(default_factory=GeographicRegion)
    severity: Optional[str] = None  # "MOD", "SEV", or None if not specified

    @property
    def is_active(self) -> bool:
        """Check if forecast predicts continued impact."""
        return not self.location.is_no_impact


class SpaceWeatherAdvisory(BaseModel):
    """
    Unified advisory model for NOAA alerts.

    This is the base model for non-ICAO advisories (NOAA/SWPC alerts).
    For ICAO advisories with full temporal-spatial structure, use ICAOAdvisory.
    """

    # Identity
    advisory_id: str
    source: Source
    serial_number: Optional[str] = None
    message_code: Optional[str] = None  # e.g., "ALTK06", "WATA20", "SUMXMF"

    # Classification
    event_type: EventType
    message_type: MessageType = MessageType.ALERT
    severity: Optional[Severity] = None
    noaa_scale: Optional[str] = None  # Original R1-R5, G1-G5, S1-S5

    # Timing
    issue_time: datetime
    begin_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    valid_from: Optional[datetime] = None
    valid_until: Optional[datetime] = None

    # Content
    message: str = ""
    short_description: Optional[str] = None
    original_text: Optional[str] = None
    potential_impacts: Optional[str] = None

    # Status
    status: Status = Status.ACTIVE
    replaces_id: Optional[str] = None
    replaced_by_id: Optional[str] = None
    cancel_serial_number: Optional[str] = None

    # Metadata
    fetched_at: Optional[datetime] = None


class ICAOAdvisory(BaseModel):
    """
    Single ICAO space weather advisory.

    ICAO advisories have a rich temporal-spatial structure with:
    - An observation (current conditions with location)
    - Four forecasts (+6h, +12h, +18h, +24h) each with their own location
    - Linkage to previous/next advisories in an event chain
    """

    # Identity
    advisory_id: str  # e.g., "2024/0042"
    center: str  # SWXC code, e.g., "PECASUS"
    center_country: str  # Header center code, e.g., "EFKL"
    source: Source = Source.ICAO_PECASUS

    # Classification
    effect: str  # "HF COM", "GNSS", "RAD"
    severity: Optional[str] = None  # "MOD", "SEV", or None (closing/ended advisories)

    @computed_field
    @property
    def event_type(self) -> EventType:
        """Map ICAO effect to unified EventType."""
        from swx_advisories.models.enums import ICAO_EFFECT_MAPPING

        return ICAO_EFFECT_MAPPING.get(self.effect, EventType.HF_BLACKOUT)

    @computed_field
    @property
    def normalized_severity(self) -> Optional[Severity]:
        """Map ICAO severity to normalized Severity."""
        if self.severity == "SEV":
            return Severity.SEVERE
        elif self.severity == "MOD":
            return Severity.MODERATE
        return None  # For closing advisories with no current impact

    # Timing
    issue_time: datetime

    # Observation (current conditions)
    observation: TemporalObservation

    # Forecasts
    forecasts: list[Forecast] = Field(default_factory=list)

    # Linkage
    replaces_id: Optional[str] = None  # Advisory number this replaces
    status: Status = Status.ACTIVE

    # Content
    remark: Optional[str] = None
    next_advisory: Optional[str] = None  # e.g., "BY 20240315/1800Z"

    # Metadata
    is_test: bool = False
    original_text: Optional[str] = None

    @computed_field
    @property
    def latency(self) -> Optional[timedelta]:
        """Time between observation and issue."""
        if self.observation and self.observation.time:
            return self.issue_time - self.observation.time
        return None

    @property
    def is_opening(self) -> bool:
        """Check if this is the first advisory in an event chain."""
        return self.replaces_id is None or self.replaces_id.upper() == "VOID"

    def get_forecast(self, hours: int) -> Optional[Forecast]:
        """Get forecast for specific hours ahead."""
        for f in self.forecasts:
            if f.hours_ahead == hours:
                return f
        return None


class ICAOEvent(BaseModel):
    """
    Chain of related ICAO advisories forming a complete event.

    An event starts with an opening advisory (replaces_id=None or 'VOID')
    and includes all subsequent advisories that replace it, tracking
    the evolution of the space weather phenomenon.
    """

    event_id: str  # Derived from opening advisory, e.g., "evt_2024_0042"
    effect: str  # "HF COM", "GNSS", "RAD"
    advisories: list[ICAOAdvisory] = Field(default_factory=list)

    @property
    def opening(self) -> Optional[ICAOAdvisory]:
        """First advisory in the chain."""
        return self.advisories[0] if self.advisories else None

    @property
    def closing(self) -> Optional[ICAOAdvisory]:
        """Last advisory in the chain."""
        return self.advisories[-1] if self.advisories else None

    @property
    def num_advisories(self) -> int:
        """Number of advisories in the chain."""
        return len(self.advisories)

    @computed_field
    @property
    def peak_severity(self) -> Optional[str]:
        """Maximum severity across the event chain."""
        if not self.advisories:
            return None
        severities = {"MOD": 1, "SEV": 2}
        # Filter to advisories that have severity
        with_severity = [a for a in self.advisories if a.severity]
        if not with_severity:
            return None
        return max(with_severity, key=lambda a: severities.get(a.severity or "MOD", 0)).severity

    @computed_field
    @property
    def issue_start(self) -> Optional[datetime]:
        """When first advisory was issued."""
        return self.opening.issue_time if self.opening else None

    @computed_field
    @property
    def issue_end(self) -> Optional[datetime]:
        """When last advisory was issued."""
        return self.closing.issue_time if self.closing else None

    @computed_field
    @property
    def observation_start(self) -> Optional[datetime]:
        """First observation time."""
        return self.opening.observation.time if self.opening else None

    @computed_field
    @property
    def observation_end(self) -> Optional[datetime]:
        """Last observation time."""
        return self.closing.observation.time if self.closing else None

    @property
    def duration(self) -> Optional[timedelta]:
        """Duration from first to last issue time."""
        if self.issue_start and self.issue_end:
            return self.issue_end - self.issue_start
        return None

    @property
    def centers(self) -> list[str]:
        """All centers that issued advisories for this event."""
        return list(dict.fromkeys(a.center for a in self.advisories))
