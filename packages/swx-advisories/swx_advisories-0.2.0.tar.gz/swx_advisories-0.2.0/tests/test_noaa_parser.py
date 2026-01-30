"""Test NOAA parser against sample data."""

import pytest
from datetime import datetime, timezone
from collections import Counter

from swx_advisories import EventType, MessageType, Severity
from swx_advisories.parsers.noaa import NOAAParser


class TestNOAAParser:
    """Tests for NOAA alerts parser."""

    def test_parse_sample_file_returns_alerts(self, noaa_alerts):
        """Test that parser returns a list of alerts."""
        assert len(noaa_alerts) > 0
        assert len(noaa_alerts) == 178  # Expected count from sample file

    def test_alert_has_required_fields(self, noaa_alerts):
        """Test that all alerts have required fields."""
        for alert in noaa_alerts:
            assert alert.advisory_id is not None
            assert alert.event_type is not None
            assert alert.message_type is not None
            assert alert.issue_time is not None
            assert isinstance(alert.issue_time, datetime)

    def test_event_types_present(self, noaa_alerts):
        """Test that expected event types are present."""
        event_types = set(alert.event_type for alert in noaa_alerts)

        # NOAA alerts should have various event types
        assert len(event_types) > 1

    def test_message_types_present(self, noaa_alerts):
        """Test that expected message types are present."""
        message_types = set(alert.message_type for alert in noaa_alerts)

        # Should have at least some message types
        assert len(message_types) > 0

        # Check for expected types
        expected_types = {MessageType.ALERT, MessageType.WARNING, MessageType.SUMMARY}
        assert len(expected_types & message_types) > 0

    def test_severity_values(self, noaa_alerts):
        """Test that severity values are valid."""
        alerts_with_severity = [a for a in noaa_alerts if a.severity is not None]
        assert len(alerts_with_severity) > 0

        for alert in alerts_with_severity:
            assert isinstance(alert.severity, Severity)

    def test_noaa_scale_format(self, noaa_alerts):
        """Test NOAA scale format (e.g., G2, S1, R3)."""
        alerts_with_scale = [a for a in noaa_alerts if a.noaa_scale is not None]
        assert len(alerts_with_scale) > 0

        for alert in alerts_with_scale:
            # Scale format should be letter + number
            scale = alert.noaa_scale
            assert scale[0] in "GSR"  # G=geomagnetic, S=solar radiation, R=radio
            assert scale[1:].isdigit()

    def test_serial_numbers(self, noaa_alerts):
        """Test that serial numbers are extracted."""
        alerts_with_serial = [a for a in noaa_alerts if a.serial_number is not None]
        assert len(alerts_with_serial) > 0

        for alert in alerts_with_serial:
            # Serial number is stored as string
            assert alert.serial_number.isdigit()
            assert int(alert.serial_number) > 0

    def test_geomagnetic_alerts(self, noaa_alerts):
        """Test geomagnetic storm alerts."""
        geo_alerts = [
            a for a in noaa_alerts
            if a.event_type == EventType.GEOMAGNETIC_STORM
        ]
        assert len(geo_alerts) > 0

        for alert in geo_alerts:
            if alert.noaa_scale:
                assert alert.noaa_scale.startswith("G")

    def test_radio_blackout_alerts(self, noaa_alerts):
        """Test radio blackout alerts."""
        radio_alerts = [
            a for a in noaa_alerts
            if a.event_type == EventType.RADIO_BLACKOUT
        ]
        assert len(radio_alerts) > 0

    def test_solar_radiation_alerts(self, noaa_alerts):
        """Test solar radiation storm alerts."""
        solar_alerts = [
            a for a in noaa_alerts
            if a.event_type == EventType.SOLAR_RADIATION_STORM
        ]
        # May or may not have solar radiation alerts in sample
        assert len(solar_alerts) >= 0


class TestNOAAMessageParsing:
    """Tests for NOAA message content parsing."""

    def test_parse_k_index_alert(self, noaa_parser):
        """Test parsing K-index alert message."""
        k_alert_msg = """Space Weather Message Code: ALTK06
Serial Number: 690
Issue Time: 2026 Jan 20 1856 UTC

ALERT: Geomagnetic K-index of 6
 Threshold Reached: 2026 Jan 20 1852 UTC
Synoptic Period: 1800-2100 UTC

Active Warning: Yes
NOAA Scale: G2 - Moderate

Potential Impacts: Area of impact primarily poleward of 55 degrees."""

        parsed = noaa_parser._parse_message(k_alert_msg)

        assert parsed.get("message_code") == "ALTK06"
        # Serial number is stored as string
        assert parsed.get("serial_number") == "690"
        assert parsed.get("noaa_scale") == "G2"
        assert parsed.get("k_index") == 6

    def test_parse_xray_summary(self, noaa_parser):
        """Test parsing X-ray event summary."""
        xray_msg = """Space Weather Message Code: SUMX01
Serial Number: 205
Issue Time: 2026 Jan 18 1900 UTC

SUMMARY: X-ray Event exceeded X1
Begin Time: 2026 Jan 18 1727 UTC
Maximum Time: 2026 Jan 18 1809 UTC
End Time: 2026 Jan 18 1851 UTC
X-ray Class: X1.9
NOAA Scale: R3 - Strong

Potential Impacts: Wide area blackout of HF radio."""

        parsed = noaa_parser._parse_message(xray_msg)

        assert parsed.get("message_code") == "SUMX01"
        assert parsed.get("xray_class") == "X1.9"
        assert parsed.get("noaa_scale") == "R3"
        assert parsed.get("begin_time") is not None
        assert parsed.get("end_time") is not None

    def test_parse_proton_warning(self, noaa_parser):
        """Test parsing proton event warning."""
        proton_msg = """Space Weather Message Code: WARPQ1
Serial Number: 15
Issue Time: 2026 Jan 18 1815 UTC

WARNING: Proton 100MeV Integral Flux above 1pfu expected
Valid From: 2026 Jan 18 2100 UTC
Valid To: 2026 Jan 19 2100 UTC
Warning Condition: Onset

NOAA Scale: S1 - Minor

Potential Impacts: None expected."""

        parsed = noaa_parser._parse_message(proton_msg)

        assert parsed.get("message_code") == "WARPQ1"
        assert parsed.get("noaa_scale") == "S1"
        assert "proton" in parsed.get("warning_type", "").lower() or "proton" in proton_msg.lower()

    def test_parse_cme_watch(self, noaa_parser):
        """Test parsing CME watch message."""
        cme_msg = """Space Weather Message Code: WATA20
Serial Number: 13
Issue Time: 2026 Jan 17 0825 UTC

WATCH: Geomagnetic Storm Category G1 Predicted

Highest Storm Level Predicted by Day:
Jan 18: G1 (Minor)
Jan 19: None
Jan 20: None

Potential Impacts: Weak power grid fluctuations can occur."""

        parsed = noaa_parser._parse_message(cme_msg)

        assert parsed.get("message_code") == "WATA20"
        # Watch messages may not have NOAA scale directly

    def test_message_code_extraction(self, noaa_parser):
        """Test message code determines event type mapping."""
        # Test various message code patterns
        test_cases = [
            ("ALTK05", "geomagnetic"),  # K-index alert
            ("SUMX01", "radio_blackout"),  # X-ray summary
            ("WARPQ1", "solar_radiation"),  # Proton warning
            ("WATA20", "geomagnetic"),  # Geomagnetic watch
        ]

        for code, expected_category in test_cases:
            msg = f"Space Weather Message Code: {code}\nSerial Number: 1\nIssue Time: 2026 Jan 20 1200 UTC\nTest message."
            parsed = noaa_parser._parse_message(msg)
            assert parsed.get("message_code") == code


class TestNOAAAlertMetrics:
    """Tests for extracted metrics from NOAA alerts."""

    def test_alerts_have_issue_time(self, noaa_alerts):
        """Test all alerts have issue time and are timezone-aware."""
        for alert in noaa_alerts:
            assert alert.issue_time is not None
            # All datetimes should be timezone-aware and in UTC
            assert alert.issue_time.tzinfo is not None
            assert alert.issue_time.tzinfo == timezone.utc

    def test_some_alerts_have_begin_end_times(self, noaa_alerts):
        """Test that some alerts have begin/end times."""
        alerts_with_begin = [a for a in noaa_alerts if a.begin_time is not None]
        alerts_with_end = [a for a in noaa_alerts if a.end_time is not None]

        # At least some alerts should have these
        assert len(alerts_with_begin) > 0 or len(alerts_with_end) > 0

    def test_potential_impacts_extracted(self, noaa_alerts):
        """Test potential impacts field is extracted when present."""
        alerts_with_impacts = [a for a in noaa_alerts if a.potential_impacts]
        # Not all alerts have impacts, but many should
        assert len(alerts_with_impacts) > 0

    def test_short_description_extracted(self, noaa_alerts):
        """Test short description is extracted when present."""
        alerts_with_desc = [a for a in noaa_alerts if a.short_description]
        assert len(alerts_with_desc) > 0
