"""Test fetchers for ICAO and NOAA data sources."""

import pytest
from datetime import datetime

from swx_advisories import ICAOFetcher, NOAAFetcher, FetchResult, EventType, MessageType


class TestICAOFetcher:
    """Tests for ICAO data fetcher."""

    def test_fetch_returns_result(self, icao_fetcher):
        """Test that fetch returns a FetchResult."""
        result = icao_fetcher.fetch()

        assert isinstance(result, FetchResult)
        assert result.success is True
        assert result.count > 0

    def test_fetch_result_has_advisories(self, icao_fetcher):
        """Test that fetch result contains advisories."""
        result = icao_fetcher.fetch()

        assert result.advisories is not None
        assert len(result.advisories) == result.count

    def test_fetch_result_has_metadata(self, icao_fetcher):
        """Test that fetch result has metadata."""
        result = icao_fetcher.fetch()

        assert result.fetch_time is not None
        assert isinstance(result.fetch_time, datetime)
        assert result.source_path is not None

    def test_fetch_includes_events(self, icao_fetcher):
        """Test that fetch() automatically builds events."""
        result = icao_fetcher.fetch()

        assert result.events is not None
        assert isinstance(result.events, list)
        assert len(result.events) > 0
        # Each event should have advisories
        for event in result.events:
            assert event.num_advisories > 0

    def test_fetch_with_build_events_false(self, icao_fetcher):
        """Test that fetch(build_events=False) returns None for events."""
        result = icao_fetcher.fetch(build_events=False)

        assert result.events is None
        # Advisories should still be populated
        assert len(result.advisories) > 0

    def test_from_text_class_method(self, sample_icao_file):
        """Test parsing from raw text by reading actual fixture."""
        # Read actual sample file and test from_text
        content = sample_icao_file.read_text()
        result = ICAOFetcher.from_text(content)

        assert result.success is True
        assert result.count > 0
        # Should parse same as file
        assert result.advisories[0].advisory_id is not None

    def test_from_text_returns_fetch_result(self):
        """Test that from_text returns a FetchResult even if empty."""
        result = ICAOFetcher.from_text("")

        assert isinstance(result, FetchResult)
        assert result.success is True  # No errors
        assert result.count == 0

    def test_iterable_result(self, icao_fetcher):
        """Test that FetchResult is iterable."""
        result = icao_fetcher.fetch()

        count = 0
        for advisory in result:
            count += 1
            assert advisory.advisory_id is not None

        assert count == result.count


class TestNOAAFetcher:
    """Tests for NOAA data fetcher."""

    def test_fetch_from_file_returns_result(self, noaa_fetcher):
        """Test that fetch from file returns a FetchResult."""
        result = noaa_fetcher.fetch()

        assert isinstance(result, FetchResult)
        assert result.success is True
        assert result.count > 0

    def test_fetch_result_has_alerts(self, noaa_fetcher):
        """Test that fetch result contains alerts."""
        result = noaa_fetcher.fetch()

        assert result.advisories is not None
        assert len(result.advisories) == result.count

    def test_fetch_by_event_type(self, noaa_fetcher):
        """Test filtering by event type."""
        geomag = noaa_fetcher.fetch_by_type(EventType.GEOMAGNETIC_STORM)

        assert geomag.success is True
        assert geomag.count > 0

        for alert in geomag.advisories:
            assert alert.event_type == EventType.GEOMAGNETIC_STORM

    def test_fetch_active_alerts(self, noaa_fetcher):
        """Test fetching active alerts."""
        alerts = noaa_fetcher.fetch_active_alerts()

        for alert in alerts.advisories:
            assert alert.message_type == MessageType.ALERT

    def test_fetch_warnings(self, noaa_fetcher):
        """Test fetching warnings."""
        warnings = noaa_fetcher.fetch_warnings()

        for warning in warnings.advisories:
            assert warning.message_type == MessageType.WARNING

    def test_fetch_watches(self, noaa_fetcher):
        """Test fetching watches."""
        watches = noaa_fetcher.fetch_watches()

        for watch in watches.advisories:
            assert watch.message_type == MessageType.WATCH

    def test_from_json_class_method(self):
        """Test parsing from raw JSON."""
        sample_json = [
            {
                "product_id": "K05A",
                "issue_datetime": "2026-01-20 12:00:00",
                "message": "Space Weather Message Code: ALTK05\nSerial Number: 999\nIssue Time: 2026 Jan 20 1200 UTC\n\nALERT: Geomagnetic K-index of 5\nNOAA Scale: G1 - Minor"
            }
        ]
        result = NOAAFetcher.from_json(sample_json)

        assert result.success is True
        assert result.count == 1

        alert = result.advisories[0]
        # Advisory ID is formatted as message_code-serial_number
        assert "ALTK05" in alert.advisory_id
        assert alert.noaa_scale == "G1"

    def test_iterable_result(self, noaa_fetcher):
        """Test that FetchResult is iterable."""
        result = noaa_fetcher.fetch()

        count = 0
        for alert in result:
            count += 1
            assert alert.advisory_id is not None

        assert count == result.count


class TestFetchResult:
    """Tests for FetchResult container."""

    def test_empty_result(self):
        """Test empty FetchResult."""
        result = FetchResult(advisories=[])

        assert result.count == 0
        assert len(list(result)) == 0
        assert result.success is True  # No errors means success

    def test_result_with_errors(self):
        """Test FetchResult with errors."""
        result = FetchResult(
            advisories=[],
            errors=["Connection failed", "Timeout"],
        )

        assert result.success is False  # Errors means not success
        assert len(result.errors) == 2

    def test_result_metadata(self, icao_fetcher):
        """Test FetchResult metadata fields."""
        result = icao_fetcher.fetch()

        assert result.fetch_time is not None
        # Source should be set based on fetcher type
        assert result.source_path is not None or result.source_url is not None


@pytest.mark.skip(reason="Requires network access")
class TestNOAAFetcherAPI:
    """Tests for NOAA live API fetching (optional)."""

    def test_fetch_from_api(self):
        """Test fetching from live NOAA API."""
        fetcher = NOAAFetcher()
        result = fetcher.fetch()

        assert result.success is True
        assert result.source_url is not None

    def test_api_returns_alerts(self):
        """Test that API returns valid alerts."""
        fetcher = NOAAFetcher()
        result = fetcher.fetch()

        if result.count > 0:
            alert = result.advisories[0]
            assert alert.advisory_id is not None
            assert alert.issue_time is not None
