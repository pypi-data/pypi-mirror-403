"""Test DataFrame adapters."""

import pytest
import pandas as pd

from swx_advisories import (
    to_dataframe,
    icao_advisories_to_dataframe,
    icao_events_to_dataframe,
    noaa_alerts_to_dataframe,
)
from swx_advisories.adapters.dataframe import (
    icao_timeline_dataframe,
    noaa_timeline_dataframe,
    to_hapi_format,
)


class TestICAOAdvisoryDataFrame:
    """Tests for ICAO advisories to DataFrame conversion."""

    def test_returns_dataframe(self, icao_advisories):
        """Test that function returns a pandas DataFrame."""
        df = icao_advisories_to_dataframe(icao_advisories)

        assert isinstance(df, pd.DataFrame)
        assert len(df) == len(icao_advisories)

    def test_has_required_columns(self, icao_advisories):
        """Test that DataFrame has required columns."""
        df = icao_advisories_to_dataframe(icao_advisories)

        required_columns = [
            "advisory_id",
            "center",
            "effect",
            "severity",
            "issue_time",
            "obs_time",
        ]
        for col in required_columns:
            assert col in df.columns

    def test_datetime_columns(self, icao_advisories):
        """Test that datetime columns are properly typed."""
        df = icao_advisories_to_dataframe(icao_advisories)

        assert pd.api.types.is_datetime64_any_dtype(df["issue_time"])
        assert pd.api.types.is_datetime64_any_dtype(df["obs_time"])

    def test_forecast_columns(self, icao_advisories):
        """Test that forecast status columns are present."""
        df = icao_advisories_to_dataframe(icao_advisories)

        for hours in [6, 12, 18, 24]:
            assert f"fcst_{hours}h_active" in df.columns
            assert f"fcst_{hours}h_severity" in df.columns

    def test_location_columns(self, icao_advisories):
        """Test that location columns are present."""
        df = icao_advisories_to_dataframe(icao_advisories)

        location_columns = ["lat_min", "lat_max", "lon_min", "lon_max"]
        for col in location_columns:
            assert col in df.columns

    def test_empty_input(self):
        """Test handling of empty input."""
        df = icao_advisories_to_dataframe([])
        assert len(df) == 0


class TestICAOEventsDataFrame:
    """Tests for ICAO events to DataFrame conversion."""

    def test_returns_dataframe(self, icao_events):
        """Test that function returns a pandas DataFrame."""
        df = icao_events_to_dataframe(icao_events)

        assert isinstance(df, pd.DataFrame)
        assert len(df) == len(icao_events)

    def test_has_required_columns(self, icao_events):
        """Test that DataFrame has required columns."""
        df = icao_events_to_dataframe(icao_events)

        required_columns = [
            "event_id",
            "effect",
            "peak_severity",
            "num_advisories",
            "duration_hours",
        ]
        for col in required_columns:
            assert col in df.columns

    def test_datetime_columns(self, icao_events):
        """Test that datetime columns are properly typed."""
        df = icao_events_to_dataframe(icao_events)

        datetime_cols = ["issue_start", "issue_end", "obs_start", "obs_end"]
        for col in datetime_cols:
            assert col in df.columns
            # May have NaT values, but dtype should be datetime
            assert pd.api.types.is_datetime64_any_dtype(df[col])

    def test_duration_calculation(self, icao_events):
        """Test that duration is properly calculated."""
        df = icao_events_to_dataframe(icao_events)

        # Duration should be non-negative
        valid_durations = df["duration_hours"].dropna()
        assert (valid_durations >= 0).all()

    def test_empty_input(self):
        """Test handling of empty input."""
        df = icao_events_to_dataframe([])
        assert len(df) == 0


class TestICAOTimelineDataFrame:
    """Tests for ICAO timeline DataFrame."""

    def test_returns_dataframe(self, icao_events):
        """Test that function returns a pandas DataFrame."""
        df = icao_timeline_dataframe(icao_events)

        assert isinstance(df, pd.DataFrame)
        assert len(df) > 0

    def test_has_timeline_columns(self, icao_events):
        """Test that DataFrame has timeline columns."""
        df = icao_timeline_dataframe(icao_events)

        required_columns = ["time", "event_id", "effect", "severity"]
        for col in required_columns:
            assert col in df.columns

    def test_start_end_markers(self, icao_events):
        """Test that start/end markers are present."""
        df = icao_timeline_dataframe(icao_events)

        assert "is_start" in df.columns
        assert "is_end" in df.columns

        # Each event should have start and end
        assert df["is_start"].any()
        assert df["is_end"].any()

    def test_resampling(self, icao_events):
        """Test resampling option."""
        df_original = icao_timeline_dataframe(icao_events)
        df_resampled = icao_timeline_dataframe(icao_events, resample="1h")

        # Resampled should have more rows (filled in)
        assert len(df_resampled) >= len(df_original)

    def test_sorted_by_time(self, icao_events):
        """Test that output is sorted by time."""
        df = icao_timeline_dataframe(icao_events)

        if len(df) > 1:
            times = df["time"].tolist()
            assert times == sorted(times)

    def test_empty_input(self):
        """Test handling of empty input."""
        df = icao_timeline_dataframe([])
        assert len(df) == 0


class TestNOAAAlertsDataFrame:
    """Tests for NOAA alerts to DataFrame conversion."""

    def test_returns_dataframe(self, noaa_alerts):
        """Test that function returns a pandas DataFrame."""
        df = noaa_alerts_to_dataframe(noaa_alerts)

        assert isinstance(df, pd.DataFrame)
        assert len(df) == len(noaa_alerts)

    def test_has_required_columns(self, noaa_alerts):
        """Test that DataFrame has required columns."""
        df = noaa_alerts_to_dataframe(noaa_alerts)

        required_columns = [
            "advisory_id",
            "event_type",
            "message_type",
            "severity",
            "noaa_scale",
            "issue_time",
        ]
        for col in required_columns:
            assert col in df.columns

    def test_datetime_columns(self, noaa_alerts):
        """Test that datetime columns are properly typed."""
        df = noaa_alerts_to_dataframe(noaa_alerts)

        assert pd.api.types.is_datetime64_any_dtype(df["issue_time"])

    def test_optional_time_columns(self, noaa_alerts):
        """Test that optional time columns are present."""
        df = noaa_alerts_to_dataframe(noaa_alerts)

        optional_time_cols = ["begin_time", "end_time", "valid_from", "valid_until"]
        for col in optional_time_cols:
            assert col in df.columns

    def test_empty_input(self):
        """Test handling of empty input."""
        df = noaa_alerts_to_dataframe([])
        assert len(df) == 0


class TestNOAATimelineDataFrame:
    """Tests for NOAA timeline DataFrame."""

    def test_returns_dataframe(self, noaa_alerts):
        """Test that function returns a pandas DataFrame."""
        df = noaa_timeline_dataframe(noaa_alerts)

        assert isinstance(df, pd.DataFrame)
        assert len(df) > 0

    def test_has_timeline_columns(self, noaa_alerts):
        """Test that DataFrame has timeline columns."""
        df = noaa_timeline_dataframe(noaa_alerts)

        required_columns = ["time", "advisory_id", "event_type", "severity"]
        for col in required_columns:
            assert col in df.columns

    def test_empty_input(self):
        """Test handling of empty input."""
        df = noaa_timeline_dataframe([])
        assert len(df) == 0


class TestUnifiedToDataFrame:
    """Tests for unified to_dataframe function."""

    def test_icao_advisories_flat(self, icao_advisories):
        """Test converting ICAO advisories with flat format."""
        df = to_dataframe(icao_advisories, format="flat")

        assert isinstance(df, pd.DataFrame)
        assert len(df) == len(icao_advisories)
        assert "advisory_id" in df.columns

    def test_icao_events_flat(self, icao_events):
        """Test converting ICAO events with flat format."""
        df = to_dataframe(icao_events, format="flat")

        assert isinstance(df, pd.DataFrame)
        assert len(df) == len(icao_events)
        assert "event_id" in df.columns

    def test_icao_events_timeline(self, icao_events):
        """Test converting ICAO events with timeline format."""
        df = to_dataframe(icao_events, format="timeline")

        assert isinstance(df, pd.DataFrame)
        assert "time" in df.columns

    def test_noaa_alerts_flat(self, noaa_alerts):
        """Test converting NOAA alerts with flat format."""
        df = to_dataframe(noaa_alerts, format="flat")

        assert isinstance(df, pd.DataFrame)
        assert len(df) == len(noaa_alerts)

    def test_noaa_alerts_timeline(self, noaa_alerts):
        """Test converting NOAA alerts with timeline format."""
        df = to_dataframe(noaa_alerts, format="timeline")

        assert isinstance(df, pd.DataFrame)
        assert "time" in df.columns

    def test_empty_input(self):
        """Test handling of empty input."""
        df = to_dataframe([], format="flat")
        assert len(df) == 0


class TestHAPIFormat:
    """Tests for HAPI-compatible format."""

    def test_returns_dataframe(self, icao_events):
        """Test that function returns a pandas DataFrame."""
        df = to_hapi_format(icao_events)

        assert isinstance(df, pd.DataFrame)

    def test_pivoted_by_effect(self, icao_events):
        """Test that output is pivoted by effect type."""
        df = to_hapi_format(icao_events)

        # Should have effect types as columns
        if not df.empty:
            # Column names should be effect types or event types
            assert len(df.columns) > 0

    def test_time_indexed(self, icao_events):
        """Test that output has time index."""
        df = to_hapi_format(icao_events)

        if not df.empty:
            # Index should be datetime
            assert isinstance(df.index, pd.DatetimeIndex)

    def test_empty_input(self):
        """Test handling of empty input."""
        df = to_hapi_format([])
        assert len(df) == 0
