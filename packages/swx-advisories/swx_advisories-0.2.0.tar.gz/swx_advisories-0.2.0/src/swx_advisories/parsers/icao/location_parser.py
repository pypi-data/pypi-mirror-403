"""Parse ICAO location codes from advisory text."""

import logging
import re
from collections import Counter
from dataclasses import dataclass
from typing import Optional

from swx_advisories.models.location import GeographicRegion, LatitudeBand

logger = logging.getLogger(__name__)


@dataclass
class ParsedObservation:
    """Parsed observation/forecast with severity and location extracted."""

    time_str: str
    severity: Optional[str]
    location: GeographicRegion


def parse_obs_or_fcst(text: str, dtg: str) -> ParsedObservation:
    """
    Parse OBS SWX or FCST SWX field that may contain severity.

    Real-world format examples:
        "20/1732Z SEV EQS EQN MNH MSH W180 - E180"
        "20/1542Z SEV N55 E055 - N85 E055 - N85 E005 - N55 E005 - N55 E055"
        "20/1517Z NO SWX EXP"
        "21/0000Z NOT AVBL"
        "20/0106Z MOD HNH MNH EQN EQS MSH HSH E000-W090"

    Args:
        text: Raw OBS SWX or FCST SWX field value
        dtg: Full DTG for date context

    Returns:
        ParsedObservation with time, severity, and location
    """
    text = text.strip()

    # Split on first whitespace to get time
    parts = text.split(None, 1)
    if not parts:
        return ParsedObservation(
            time_str="",
            severity=None,
            location=GeographicRegion(is_no_impact=True),
        )

    time_str = parts[0]
    rest = parts[1] if len(parts) > 1 else ""

    # Check for special cases
    if "NO SWX EXP" in rest.upper() or "NOT APPLICABLE" in rest.upper():
        return ParsedObservation(
            time_str=time_str,
            severity=None,
            location=GeographicRegion(text=rest, is_no_impact=True),
        )

    if "NOT AVBL" in rest.upper():
        return ParsedObservation(
            time_str=time_str,
            severity=None,
            location=GeographicRegion(text=rest, is_no_impact=True),
        )

    # Extract severity if present at start
    severity = None
    location_text = rest

    # Check if rest starts with SEV or MOD
    rest_upper = rest.upper().strip()
    if rest_upper.startswith("SEV ") or rest_upper.startswith("SEV\t"):
        severity = "SEV"
        location_text = rest[4:].strip()
    elif rest_upper.startswith("MOD ") or rest_upper.startswith("MOD\t"):
        severity = "MOD"
        location_text = rest[4:].strip()

    # Parse the location
    location = parse_location_code(location_text) if location_text else GeographicRegion()

    # If we didn't find severity at start, check if it's embedded in location
    if severity is None:
        if " SEV " in rest.upper() or rest.upper().startswith("SEV"):
            severity = "SEV"
        elif " MOD " in rest.upper() or rest.upper().startswith("MOD"):
            severity = "MOD"

    return ParsedObservation(
        time_str=time_str,
        severity=severity,
        location=location,
    )


def parse_location_code(text: str) -> GeographicRegion:
    """
    Parse ICAO location code from OBS SWX or FCST SWX text.

    ICAO location format:
    - Latitude bands: HNH, MNH, EQN, EQS, MSH, HSH
    - Longitude range: E000-W180, W045-E090, etc.
    - Polygon coordinates: N55 E055 - N85 E055 - N85 E005 - N55 E005
    - Special: "DAYLIGHT SIDE", "NO SWX EXP", "NOT AVBL"
    - Multiple regions with severity: "SEV N55... SEV S90..."

    Examples:
        "HNH MNH E000-W180" -> lat [30, 90], lon [-180, 0]
        "HNH MNH EQN EQS MSH" -> lat [-60, 90] (merged bands)
        "N55 E055 - N85 E055 - N85 E005 - N55 E005" -> polygon
        "DAYLIGHT SIDE" -> is_daylight_side=True
        "NO SWX EXP" -> is_no_impact=True

    Args:
        text: Location text from OBS SWX or FCST SWX field

    Returns:
        GeographicRegion with parsed coordinates
    """
    if not text:
        return GeographicRegion()

    original_text = text
    text = text.strip().upper()

    # Check for special cases
    if "DAYLIGHT SIDE" in text:
        return GeographicRegion(text=original_text, is_daylight_side=True)

    if "NO SWX EXP" in text or "NOT APPLICABLE" in text or "NOT AVBL" in text:
        return GeographicRegion(text=original_text, is_no_impact=True)

    # Remove embedded severity markers for location parsing
    # They may appear multiple times for multiple regions
    text_for_parsing = re.sub(r"\bSEV\b", " ", text)
    text_for_parsing = re.sub(r"\bMOD\b", " ", text_for_parsing)
    text_for_parsing = " ".join(text_for_parsing.split())  # Normalize whitespace

    # Check if this is polygon format (contains N/S followed by digits for latitude)
    # Pattern: N55 or S90 etc. (latitude coordinates)
    polygon_lat_pattern = r"[NS]\d{1,2}"
    has_polygon_coords = bool(re.search(polygon_lat_pattern, text_for_parsing))

    # Parse latitude bands (only if not polygon format)
    bands = []
    band_codes = ["HNH", "MNH", "EQN", "EQS", "MSH", "HSH"]

    # Check for latitude bands - they should appear as whole words
    for code in band_codes:
        # Match as whole word
        if re.search(rf"\b{code}\b", text_for_parsing):
            bands.append(LatitudeBand(code))

    # Parse longitude values
    # Pattern: E/W followed by 2-3 digits
    east_matches = re.findall(r"E(\d{2,3})", text_for_parsing)
    west_matches = re.findall(r"W(\d{2,3})", text_for_parsing)

    lons = []
    for lon_str in east_matches:
        lons.append(float(lon_str))
    for lon_str in west_matches:
        lons.append(-float(lon_str))

    # Parse latitude values from polygon coordinates
    # Pattern: N/S followed by 2 digits
    north_matches = re.findall(r"N(\d{1,2})", text_for_parsing)
    south_matches = re.findall(r"S(\d{1,2})", text_for_parsing)

    polygon_lats = []
    for lat_str in north_matches:
        polygon_lats.append(float(lat_str))
    for lat_str in south_matches:
        polygon_lats.append(-float(lat_str))

    lon_min = min(lons) if lons else None
    lon_max = max(lons) if lons else None

    # Parse flight level if present
    above_fl = None
    fl_match = re.search(r"ABV FL(\d+)", text)
    if fl_match:
        above_fl = int(fl_match.group(1))

    # Compute latitude bounds
    lat_min = None
    lat_max = None

    if polygon_lats:
        # Use polygon latitude coordinates
        lat_min = min(polygon_lats)
        lat_max = max(polygon_lats)
    elif bands:
        # Use latitude bands
        band_ranges = {
            LatitudeBand.HNH: (60, 90),
            LatitudeBand.MNH: (30, 60),
            LatitudeBand.EQN: (0, 30),
            LatitudeBand.EQS: (-30, 0),
            LatitudeBand.MSH: (-60, -30),
            LatitudeBand.HSH: (-90, -60),
        }

        lats = []
        for band in bands:
            lat_range = band_ranges[band]
            lats.extend(lat_range)

        # If a latitude appears twice, it's an internal boundary - remove it
        lat_counts = Counter(lats)
        unique_lats = [lat for lat, count in lat_counts.items() if count == 1]

        if unique_lats:
            lat_min = min(unique_lats)
            lat_max = max(unique_lats)
        elif lats:
            # Fallback: use all boundaries
            lat_min = min(lats)
            lat_max = max(lats)

    # Validate we got something
    if not bands and not polygon_lats and lon_min is None and not above_fl:
        logger.warning(f"Could not parse location from: {original_text!r}")

    return GeographicRegion(
        lat_min=lat_min,
        lat_max=lat_max,
        lon_min=lon_min,
        lon_max=lon_max,
        text=original_text,
        bands=bands if bands else None,
        above_flight_level=above_fl,
    )


def parse_partial_datetime(dtg: str, partial_dt: str) -> str:
    """
    Reconstruct full datetime from partial date/time.

    ICAO advisories use partial dates like "15/1045Z" which need
    to be combined with the DTG (Date/Time Group) to get the full date.

    Args:
        dtg: Full DTG string, e.g., "20240315/1200Z"
        partial_dt: Partial date/time, e.g., "15/1045Z"

    Returns:
        ISO format datetime string
    """
    import pandas as pd

    timestamp_dtg = pd.to_datetime(dtg)
    day_of_month_dtg = timestamp_dtg.day
    month_dtg = timestamp_dtg.month
    year_dtg = timestamp_dtg.year

    # Parse partial date
    partial_day_str, partial_time = partial_dt.split("/")
    partial_day = int(partial_day_str)

    # Handle month boundary crossing
    # If partial day is very low (1-2) and DTG day is very high (26+),
    # we've crossed into a new month
    if partial_day < 3 and day_of_month_dtg > 26:
        partial_month = month_dtg + 1
        partial_year = year_dtg
        if partial_month == 13:  # December to January
            partial_month = 1
            partial_year = year_dtg + 1
    else:
        partial_month = month_dtg
        partial_year = year_dtg

    # Remove 'Z' suffix if present
    partial_time = partial_time.rstrip("Z")

    # Build datetime string
    timestring = f"{partial_year}-{partial_month:02d}-{partial_day:02d}T{partial_time[:2]}:{partial_time[2:]}:00Z"

    return timestring
