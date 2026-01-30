"""Geographic location models for space weather advisories."""

from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field, model_validator


class LatitudeBand(str, Enum):
    """ICAO latitude band codes."""

    HNH = "HNH"  # High Northern Hemisphere (60°N - 90°N)
    MNH = "MNH"  # Middle Northern Hemisphere (30°N - 60°N)
    EQN = "EQN"  # Equatorial Northern (0° - 30°N)
    EQS = "EQS"  # Equatorial Southern (0° - 30°S)
    MSH = "MSH"  # Middle Southern Hemisphere (30°S - 60°S)
    HSH = "HSH"  # High Southern Hemisphere (60°S - 90°S)


# Latitude band boundaries
LATITUDE_BAND_RANGES = {
    LatitudeBand.HNH: (60, 90),
    LatitudeBand.MNH: (30, 60),
    LatitudeBand.EQN: (0, 30),
    LatitudeBand.EQS: (-30, 0),
    LatitudeBand.MSH: (-60, -30),
    LatitudeBand.HSH: (-90, -60),
}


class GeographicRegion(BaseModel):
    """
    Geographic region affected by a space weather event.

    Supports both explicit lat/lon bounds and ICAO band notation.
    """

    lat_min: Optional[float] = Field(None, ge=-90, le=90)
    lat_max: Optional[float] = Field(None, ge=-90, le=90)
    lon_min: Optional[float] = Field(None, ge=-180, le=180)
    lon_max: Optional[float] = Field(None, ge=-180, le=180)

    # Original text representation
    text: Optional[str] = None

    # Parsed ICAO bands (None for polygon format, empty list for default)
    bands: Optional[list[LatitudeBand]] = Field(default_factory=list)

    # Special cases
    is_daylight_side: bool = False  # "DAYLIGHT SIDE" - follows the sun
    is_global: bool = False  # Affects entire globe
    is_no_impact: bool = False  # "NO SWX EXP" - no impact expected

    # Flight level (altitude) if specified
    above_flight_level: Optional[int] = None  # e.g., 250 for "ABV FL250"

    @model_validator(mode="after")
    def compute_bounds_from_bands(self) -> "GeographicRegion":
        """Compute lat bounds from ICAO bands if not explicitly set."""
        if self.bands and self.lat_min is None and self.lat_max is None:
            lats = []
            for band in self.bands:
                lat_range = LATITUDE_BAND_RANGES[band]
                lats.extend(lat_range)

            # Merge consecutive bands by removing duplicate boundaries
            lat_counts = {}
            for lat in lats:
                lat_counts[lat] = lat_counts.get(lat, 0) + 1

            # Keep only boundaries that appear once (outer edges)
            unique_lats = [lat for lat, count in lat_counts.items() if count == 1]

            if unique_lats:
                self.lat_min = min(unique_lats)
                self.lat_max = max(unique_lats)

        return self

    @property
    def is_defined(self) -> bool:
        """Check if location has any geographic definition."""
        return (
            self.lat_min is not None
            or self.is_daylight_side
            or self.is_global
            or self.is_no_impact
        )

    def to_polygon(self) -> Optional[list[tuple[float, float]]]:
        """
        Convert to polygon coordinates for mapping.

        Returns list of (lat, lon) tuples forming a closed polygon,
        or None if location is not a definable region.
        """
        if self.is_daylight_side or self.is_no_impact or not self.is_defined:
            return None

        if self.lat_min is None or self.lat_max is None:
            return None

        lon_min = self.lon_min if self.lon_min is not None else -180
        lon_max = self.lon_max if self.lon_max is not None else 180

        return [
            (self.lat_min, lon_min),
            (self.lat_max, lon_min),
            (self.lat_max, lon_max),
            (self.lat_min, lon_max),
            (self.lat_min, lon_min),  # Close polygon
        ]

    def __str__(self) -> str:
        """Human-readable representation."""
        if self.text:
            return self.text
        if self.is_daylight_side:
            return "DAYLIGHT SIDE"
        if self.is_no_impact:
            return "NO SWX EXP"
        if self.is_global:
            return "GLOBAL"
        if self.bands:
            return " ".join(b.value for b in self.bands)
        if self.lat_min is not None and self.lat_max is not None:
            return f"LAT {self.lat_min}° to {self.lat_max}°"
        return "UNDEFINED"
