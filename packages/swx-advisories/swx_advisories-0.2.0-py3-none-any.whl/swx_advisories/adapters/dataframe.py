"""DataFrame adapters for space weather advisories."""

from datetime import datetime, timedelta
from typing import Literal, Optional, Union

import pandas as pd

from swx_advisories.models.advisory import (
    ICAOAdvisory,
    ICAOEvent,
    SpaceWeatherAdvisory,
)


def to_dataframe(
    data: Union[
        list[ICAOAdvisory],
        list[ICAOEvent],
        list[SpaceWeatherAdvisory],
    ],
    format: Literal["flat", "timeline", "hapi"] = "flat",
) -> pd.DataFrame:
    """
    Convert advisories or events to a pandas DataFrame.

    Args:
        data: List of advisories or events
        format: Output format
            - "flat": One row per advisory with all fields
            - "timeline": Time-indexed format for visualization
            - "hapi": HAPI-compatible format with start/stop times

    Returns:
        pandas DataFrame

    Example:
        >>> from swx_advisories import ICAOFetcher, to_dataframe
        >>> fetcher = ICAOFetcher("/path/to/advisories")
        >>> events = fetcher.fetch_events()
        >>> df = to_dataframe(events, format="timeline")
    """
    if not data:
        return pd.DataFrame()

    # Detect data type from first element
    first = data[0]

    if isinstance(first, ICAOEvent):
        if format == "timeline":
            return icao_timeline_dataframe(data)
        return icao_events_to_dataframe(data)

    elif isinstance(first, ICAOAdvisory):
        if format == "timeline":
            # Convert advisories to events first for timeline
            from swx_advisories.parsers.icao import ICAOEventBuilder
            builder = ICAOEventBuilder()
            events = builder.build_events(data)
            return icao_timeline_dataframe(events)
        return icao_advisories_to_dataframe(data)

    elif isinstance(first, SpaceWeatherAdvisory):
        if format == "timeline":
            return noaa_timeline_dataframe(data)
        return noaa_alerts_to_dataframe(data)

    else:
        raise TypeError(f"Unsupported data type: {type(first)}")


def icao_advisories_to_dataframe(
    advisories: list[ICAOAdvisory],
) -> pd.DataFrame:
    """
    Convert ICAO advisories to a flat DataFrame.

    Columns include:
    - advisory_id, center, effect, severity
    - issue_time, obs_time
    - lat_min, lat_max, lon_min, lon_max (from observation)
    - replaces_id, remark
    - fcst_6h_active, fcst_12h_active, fcst_18h_active, fcst_24h_active
    """
    rows = []

    for adv in advisories:
        obs_loc = adv.observation.location if adv.observation else None

        row = {
            "advisory_id": adv.advisory_id,
            "center": adv.center,
            "center_country": adv.center_country,
            "effect": adv.effect,
            "severity": adv.severity,
            "event_type": adv.event_type.value,
            "issue_time": adv.issue_time,
            "obs_time": adv.observation.time if adv.observation else None,
            "lat_min": obs_loc.lat_min if obs_loc else None,
            "lat_max": obs_loc.lat_max if obs_loc else None,
            "lon_min": obs_loc.lon_min if obs_loc else None,
            "lon_max": obs_loc.lon_max if obs_loc else None,
            "location_text": obs_loc.text if obs_loc else None,
            "is_no_impact": obs_loc.is_no_impact if obs_loc else False,
            "replaces_id": adv.replaces_id,
            "is_opening": adv.is_opening,
            "remark": adv.remark,
            "next_advisory": adv.next_advisory,
            "original_text": adv.original_text,
        }

        # Add forecast status
        for hours in [6, 12, 18, 24]:
            fcst = adv.get_forecast(hours)
            row[f"fcst_{hours}h_active"] = fcst.is_active if fcst else None
            row[f"fcst_{hours}h_severity"] = fcst.severity if fcst else None

        rows.append(row)

    df = pd.DataFrame(rows)

    # Convert time columns to datetime
    for col in ["issue_time", "obs_time"]:
        if col in df.columns:
            df[col] = pd.to_datetime(df[col], utc=True)

    return df


def icao_events_to_dataframe(
    events: list[ICAOEvent],
) -> pd.DataFrame:
    """
    Convert ICAO events to a DataFrame.

    One row per event with summary statistics.

    Columns include:
    - event_id, effect, peak_severity
    - num_advisories, centers
    - issue_start, issue_end, duration_hours
    - obs_start, obs_end
    """
    rows = []

    for event in events:
        duration = event.duration
        duration_hours = duration.total_seconds() / 3600 if duration else None

        row = {
            "event_id": event.event_id,
            "effect": event.effect,
            "event_type": event.opening.event_type.value if event.opening else None,
            "peak_severity": event.peak_severity,
            "num_advisories": event.num_advisories,
            "centers": ", ".join(event.centers),
            "issue_start": event.issue_start,
            "issue_end": event.issue_end,
            "duration_hours": duration_hours,
            "obs_start": event.observation_start,
            "obs_end": event.observation_end,
            "opening_id": event.opening.advisory_id if event.opening else None,
            "closing_id": event.closing.advisory_id if event.closing else None,
        }

        rows.append(row)

    df = pd.DataFrame(rows)

    # Convert time columns to datetime
    for col in ["issue_start", "issue_end", "obs_start", "obs_end"]:
        if col in df.columns:
            df[col] = pd.to_datetime(df[col], utc=True)

    return df


def noaa_alerts_to_dataframe(
    advisories: list[SpaceWeatherAdvisory],
) -> pd.DataFrame:
    """
    Convert NOAA alerts to a flat DataFrame.

    Columns include:
    - advisory_id, serial_number, message_code
    - event_type, message_type, severity, noaa_scale
    - issue_time, begin_time, end_time
    - short_description, potential_impacts
    """
    rows = []

    for adv in advisories:
        row = {
            "advisory_id": adv.advisory_id,
            "serial_number": adv.serial_number,
            "message_code": adv.message_code,
            "event_type": adv.event_type.value,
            "message_type": adv.message_type.value,
            "severity": adv.severity.value if adv.severity else None,
            "noaa_scale": adv.noaa_scale,
            "issue_time": adv.issue_time,
            "begin_time": adv.begin_time,
            "end_time": adv.end_time,
            "valid_from": adv.valid_from,
            "valid_until": adv.valid_until,
            "short_description": adv.short_description,
            "potential_impacts": adv.potential_impacts,
            "status": adv.status.value,
            "original_text": adv.original_text,
        }

        rows.append(row)

    df = pd.DataFrame(rows)

    # Convert time columns to datetime
    time_cols = ["issue_time", "begin_time", "end_time", "valid_from", "valid_until"]
    for col in time_cols:
        if col in df.columns:
            df[col] = pd.to_datetime(df[col], utc=True)

    return df


def icao_timeline_dataframe(
    events: list[ICAOEvent],
    resample: Optional[str] = None,
) -> pd.DataFrame:
    """
    Convert ICAO events to a timeline DataFrame for visualization.

    Creates time-indexed rows showing event activity over time.
    Useful for plotting event timelines and overlaps.

    Args:
        events: List of ICAOEvent objects
        resample: Optional pandas resample frequency (e.g., "1h", "30min")

    Returns:
        DataFrame with columns:
        - time (index)
        - event_id, effect, severity
        - is_active (True during event)

    For HAPI-compatible output, use columns: time, event_id, effect, severity
    """
    rows = []

    for event in events:
        if not event.issue_start or not event.issue_end:
            continue

        # Use observation times if available, otherwise issue times
        start = event.observation_start or event.issue_start
        end = event.observation_end or event.issue_end

        # Ensure end is after start
        if end <= start:
            end = start + timedelta(hours=1)

        # Create start and end rows
        rows.append({
            "time": start,
            "event_id": event.event_id,
            "effect": event.effect,
            "event_type": event.opening.event_type.value if event.opening else None,
            "severity": event.peak_severity,
            "is_start": True,
            "is_end": False,
        })

        rows.append({
            "time": end,
            "event_id": event.event_id,
            "effect": event.effect,
            "event_type": event.opening.event_type.value if event.opening else None,
            "severity": event.peak_severity,
            "is_start": False,
            "is_end": True,
        })

    if not rows:
        return pd.DataFrame()

    df = pd.DataFrame(rows)
    df["time"] = pd.to_datetime(df["time"], utc=True)
    df = df.sort_values("time")

    if resample:
        # Resample to regular intervals
        df = df.set_index("time")
        # Group by event and resample
        resampled = []
        for event_id, group in df.groupby("event_id"):
            start = group[group["is_start"]].index[0]
            end = group[group["is_end"]].index[0]
            effect = group["effect"].iloc[0]
            severity = group["severity"].iloc[0]
            event_type = group["event_type"].iloc[0]

            # Create rows at regular intervals
            times = pd.date_range(start, end, freq=resample)
            for t in times:
                resampled.append({
                    "time": t,
                    "event_id": event_id,
                    "effect": effect,
                    "event_type": event_type,
                    "severity": severity,
                    "is_active": True,
                })

        df = pd.DataFrame(resampled)
        if not df.empty:
            df = df.sort_values("time")

    return df


def noaa_timeline_dataframe(
    advisories: list[SpaceWeatherAdvisory],
    resample: Optional[str] = None,
) -> pd.DataFrame:
    """
    Convert NOAA alerts to a timeline DataFrame.

    For alerts with begin/end times, creates time-indexed rows.
    For alerts without end times, uses issue_time as a point event.

    Args:
        advisories: List of SpaceWeatherAdvisory objects
        resample: Optional pandas resample frequency

    Returns:
        DataFrame with timeline data
    """
    rows = []

    for adv in advisories:
        # Use begin/end times if available, otherwise issue time
        start = adv.begin_time or adv.valid_from or adv.issue_time
        end = adv.end_time or adv.valid_until

        if end and end > start:
            # Event with duration
            rows.append({
                "time": start,
                "advisory_id": adv.advisory_id,
                "event_type": adv.event_type.value,
                "message_type": adv.message_type.value,
                "severity": adv.severity.value if adv.severity else None,
                "noaa_scale": adv.noaa_scale,
                "is_start": True,
                "is_end": False,
            })
            rows.append({
                "time": end,
                "advisory_id": adv.advisory_id,
                "event_type": adv.event_type.value,
                "message_type": adv.message_type.value,
                "severity": adv.severity.value if adv.severity else None,
                "noaa_scale": adv.noaa_scale,
                "is_start": False,
                "is_end": True,
            })
        else:
            # Point event (no duration)
            rows.append({
                "time": start,
                "advisory_id": adv.advisory_id,
                "event_type": adv.event_type.value,
                "message_type": adv.message_type.value,
                "severity": adv.severity.value if adv.severity else None,
                "noaa_scale": adv.noaa_scale,
                "is_start": True,
                "is_end": True,
            })

    if not rows:
        return pd.DataFrame()

    df = pd.DataFrame(rows)
    df["time"] = pd.to_datetime(df["time"], utc=True)
    df = df.sort_values("time")

    return df


def to_hapi_format(
    data: Union[list[ICAOEvent], list[SpaceWeatherAdvisory]],
    parameter: str = "severity",
) -> pd.DataFrame:
    """
    Convert to HAPI-compatible format.

    HAPI (Heliophysics API) format requires:
    - Time column as index
    - Parameter columns with values

    Args:
        data: List of events or advisories
        parameter: Which parameter to use as the value column

    Returns:
        DataFrame with HAPI-compatible structure
    """
    if not data:
        return pd.DataFrame()

    first = data[0]

    if isinstance(first, ICAOEvent):
        df = icao_timeline_dataframe(data)
        # Pivot to have one column per event type
        if not df.empty and "effect" in df.columns:
            df = df.pivot_table(
                index="time",
                columns="effect",
                values="severity",
                aggfunc="first",
            )
    else:
        df = noaa_timeline_dataframe(data)
        if not df.empty and "event_type" in df.columns:
            df = df.pivot_table(
                index="time",
                columns="event_type",
                values=parameter,
                aggfunc="first",
            )

    return df
