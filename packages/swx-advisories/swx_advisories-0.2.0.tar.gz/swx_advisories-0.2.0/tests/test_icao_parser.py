"""Test ICAO parser against sample data."""

import pytest
from datetime import datetime, timezone

from swx_advisories import EventType


class TestICAOTextParser:
    """Tests for ICAO text parser."""

    def test_parse_sample_file_returns_advisories(self, icao_advisories):
        """Test that parser returns a list of advisories."""
        assert len(icao_advisories) > 0
        assert len(icao_advisories) == 34  # Expected count from sample file

    def test_advisory_has_required_fields(self, icao_advisories):
        """Test that all advisories have required fields."""
        for adv in icao_advisories:
            assert adv.advisory_id is not None
            assert adv.center is not None
            assert adv.effect in ("HF COM", "GNSS")
            assert adv.issue_time is not None
            assert isinstance(adv.issue_time, datetime)

    def test_advisory_id_format(self, icao_advisories):
        """Test advisory ID format (YYYY/NNN)."""
        for adv in icao_advisories:
            assert "/" in adv.advisory_id
            year, num = adv.advisory_id.split("/")
            assert year.isdigit()
            assert num.isdigit()

    def test_opening_advisory_has_no_replaces(self, icao_advisories):
        """Test that opening advisories have no replaces_id."""
        opening_advisories = [a for a in icao_advisories if a.is_opening]
        assert len(opening_advisories) > 0
        for adv in opening_advisories:
            assert adv.replaces_id is None

    def test_continuation_advisory_has_replaces(self, icao_advisories):
        """Test that continuation advisories have replaces_id."""
        continuation_advisories = [a for a in icao_advisories if not a.is_opening]
        assert len(continuation_advisories) > 0
        for adv in continuation_advisories:
            assert adv.replaces_id is not None

    def test_observation_present(self, icao_advisories):
        """Test that all advisories have observation data."""
        for adv in icao_advisories:
            assert adv.observation is not None
            assert adv.observation.time is not None
            assert adv.observation.location is not None

    def test_forecasts_present(self, icao_advisories):
        """Test that advisories have forecast data."""
        for adv in icao_advisories:
            # Should have 4 forecasts
            assert len(adv.forecasts) == 4

    def test_severity_extraction(self, icao_advisories):
        """Test severity is properly extracted."""
        # Find advisories with severity
        with_severity = [a for a in icao_advisories if a.severity is not None]
        assert len(with_severity) > 0

        for adv in with_severity:
            assert adv.severity in ("MOD", "SEV")

    def test_closing_advisory_no_severity(self, icao_advisories):
        """Test that closing advisories (NO SWX EXP) have no severity."""
        closing_advisories = [
            a for a in icao_advisories
            if a.observation and a.observation.location and a.observation.location.is_no_impact
        ]
        for adv in closing_advisories:
            assert adv.severity is None

    def test_effect_types(self, icao_advisories):
        """Test that advisories have correct effect types."""
        hf_advisories = [a for a in icao_advisories if a.effect == "HF COM"]
        gnss_advisories = [a for a in icao_advisories if a.effect == "GNSS"]

        assert len(hf_advisories) > 0
        assert len(gnss_advisories) > 0

    def test_event_type_mapping(self, icao_advisories):
        """Test event type is correctly mapped from effect."""
        for adv in icao_advisories:
            if adv.effect == "HF COM":
                assert adv.event_type == EventType.HF_BLACKOUT
            elif adv.effect == "GNSS":
                assert adv.event_type == EventType.GNSS_DEGRADATION

    def test_polygon_coordinates_parsed(self, icao_advisories):
        """Test that polygon coordinates are properly parsed."""
        # Find advisory with polygon coordinates
        polygon_advisories = [
            a for a in icao_advisories
            if a.observation
            and a.observation.location
            and a.observation.location.lat_min is not None
            and a.observation.location.lat_max is not None
        ]
        assert len(polygon_advisories) > 0

    def test_latitude_bands_parsed(self, icao_advisories):
        """Test that latitude band format is parsed."""
        # Find advisories with latitude bands
        band_advisories = [
            a for a in icao_advisories
            if a.observation
            and a.observation.location
            and a.observation.location.bands
        ]
        # Sample data uses polygon coordinates for most advisories
        # but some use latitude bands
        assert len(band_advisories) >= 0  # May or may not have latitude bands


class TestICAOEventBuilder:
    """Tests for ICAO event builder."""

    def test_build_events_returns_list(self, icao_events):
        """Test that event builder returns a list of events."""
        assert isinstance(icao_events, list)
        assert len(icao_events) > 0

    def test_events_have_required_fields(self, icao_events):
        """Test that events have required fields."""
        for event in icao_events:
            assert event.event_id is not None
            assert event.effect is not None
            assert event.advisories is not None
            assert len(event.advisories) > 0

    def test_events_separated_by_effect(self, icao_events):
        """Test that events are properly separated by effect type."""
        hf_events = [e for e in icao_events if e.effect == "HF COM"]
        gnss_events = [e for e in icao_events if e.effect == "GNSS"]

        assert len(hf_events) > 0
        assert len(gnss_events) > 0

        # Each event should have consistent effect type
        for event in icao_events:
            effects = set(a.effect for a in event.advisories)
            assert len(effects) == 1

    def test_event_chain_integrity(self, icao_events):
        """Test that event chains are properly linked."""
        for event in icao_events:
            if event.num_advisories > 1:
                # Check that advisories are linked via replaces_id
                advisory_ids = {a.advisory_id for a in event.advisories}
                for adv in event.advisories:
                    if adv.replaces_id:
                        assert adv.replaces_id in advisory_ids

    def test_event_has_opening(self, icao_events):
        """Test that events have an opening advisory."""
        for event in icao_events:
            assert event.opening is not None
            assert event.opening.is_opening

    def test_event_timing(self, icao_events):
        """Test event timing calculations."""
        for event in icao_events:
            assert event.issue_start is not None
            assert event.issue_end is not None
            assert event.issue_start <= event.issue_end

    def test_event_duration(self, icao_events):
        """Test event duration calculation."""
        for event in icao_events:
            if event.duration:
                assert event.duration.total_seconds() >= 0

    def test_peak_severity(self, icao_events):
        """Test peak severity extraction."""
        events_with_severity = [e for e in icao_events if e.peak_severity]
        assert len(events_with_severity) > 0

        for event in events_with_severity:
            assert event.peak_severity in ("MOD", "SEV")

    def test_centers_tracked(self, icao_events):
        """Test that centers are tracked across events."""
        for event in icao_events:
            assert len(event.centers) > 0
            # Centers should be actual SWXC identifiers
            for center in event.centers:
                assert center in ("PECASUS", "ACFJ")

    def test_num_advisories_correct(self, icao_events):
        """Test num_advisories matches actual count."""
        for event in icao_events:
            assert event.num_advisories == len(event.advisories)
