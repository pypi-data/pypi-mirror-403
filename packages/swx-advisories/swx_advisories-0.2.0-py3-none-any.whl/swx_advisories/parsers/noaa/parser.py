"""Parse NOAA/SWPC space weather alerts."""

import json
import logging
import re
from datetime import datetime, timezone
from typing import Iterator, Optional

from swx_advisories.models.advisory import SpaceWeatherAdvisory
from swx_advisories.models.enums import EventType, MessageType, Severity, Source, Status

logger = logging.getLogger(__name__)


# Mapping of NOAA message codes to event types
MESSAGE_CODE_MAPPING = {
    # Geomagnetic (G-scale)
    "ALTK": EventType.GEOMAGNETIC_STORM,  # K-index alert
    "WATA": EventType.GEOMAGNETIC_STORM,  # Geomagnetic watch
    "WARK": EventType.GEOMAGNETIC_STORM,  # Geomagnetic warning
    "SUMK": EventType.GEOMAGNETIC_STORM,  # K-index summary
    "WARSUD": EventType.GEOMAGNETIC_STORM,  # Sudden impulse warning
    "SUMSUD": EventType.GEOMAGNETIC_STORM,  # Sudden impulse summary
    # Solar Radiation (S-scale)
    "ALTPX": EventType.SOLAR_RADIATION_STORM,  # Proton alert
    "WARPX": EventType.SOLAR_RADIATION_STORM,  # Proton warning
    "SUMPX": EventType.SOLAR_RADIATION_STORM,  # Proton summary
    "ALTEF": EventType.SOLAR_RADIATION_STORM,  # Electron flux alert
    "SUMEF": EventType.SOLAR_RADIATION_STORM,  # Electron flux summary
    # Radio Blackout (R-scale)
    "ALTXMF": EventType.RADIO_BLACKOUT,  # X-ray flux alert
    "SUMX": EventType.RADIO_BLACKOUT,  # X-ray summary
    # Solar activity
    "ALTTP": EventType.SOLAR_FLARE,  # Type II/IV radio emission
    "SUM10R": EventType.SOLAR_FLARE,  # 10cm radio burst
    "SUMCME": EventType.CME,  # CME summary
}

# NOAA scale to severity mapping
SCALE_SEVERITY_MAPPING = {
    # G-scale (Geomagnetic)
    "G1": Severity.MINOR,
    "G2": Severity.MODERATE,
    "G3": Severity.MODERATE,
    "G4": Severity.SEVERE,
    "G5": Severity.EXTREME,
    # S-scale (Solar Radiation)
    "S1": Severity.MINOR,
    "S2": Severity.MODERATE,
    "S3": Severity.MODERATE,
    "S4": Severity.SEVERE,
    "S5": Severity.EXTREME,
    # R-scale (Radio Blackout)
    "R1": Severity.MINOR,
    "R2": Severity.MODERATE,
    "R3": Severity.MODERATE,
    "R4": Severity.SEVERE,
    "R5": Severity.EXTREME,
}


class NOAAParser:
    """
    Parse NOAA/SWPC space weather alerts.

    Supports:
    - JSON API: https://services.swpc.noaa.gov/products/alerts.json
    - Raw message text parsing

    Message types include:
    - ALERT: Threshold has been reached
    - WARNING: Conditions expected soon
    - WATCH: Conditions possible
    - SUMMARY: Event has ended, summary provided
    """

    def parse_json(self, data: list | str) -> Iterator[SpaceWeatherAdvisory]:
        """
        Parse NOAA alerts from JSON API response.

        Args:
            data: Either a list of alert dicts or a JSON string

        Yields:
            SpaceWeatherAdvisory objects
        """
        if isinstance(data, str):
            data = json.loads(data)

        for item in data:
            try:
                advisory = self._parse_json_item(item)
                if advisory:
                    yield advisory
            except Exception as e:
                logger.warning(f"Failed to parse NOAA alert: {e}")

    def parse_json_file(self, path: str) -> Iterator[SpaceWeatherAdvisory]:
        """Parse NOAA alerts from a JSON file."""
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
        yield from self.parse_json(data)

    def _parse_json_item(self, item: dict) -> Optional[SpaceWeatherAdvisory]:
        """Parse a single JSON alert item."""
        product_id = item.get("product_id", "")
        issue_datetime = item.get("issue_datetime", "")
        message = item.get("message", "")

        if not message:
            return None

        # Parse the message content
        parsed = self._parse_message(message)

        # Parse issue time
        issue_time = self._parse_datetime(issue_datetime)
        if not issue_time:
            # Fallback to issue time in message
            issue_time = parsed.get("issue_time") or datetime.now(timezone.utc)

        # Determine event type from message code
        message_code = parsed.get("message_code", "")
        event_type = self._get_event_type(message_code)

        # Determine message type (ALERT, WARNING, WATCH, SUMMARY)
        message_type = self._get_message_type(message_code, message)

        # Extract NOAA scale and map to severity
        noaa_scale = parsed.get("noaa_scale")
        severity = self._get_severity(noaa_scale)

        # Build advisory ID
        serial_number = parsed.get("serial_number")
        advisory_id = f"{message_code}-{serial_number}" if serial_number else product_id

        return SpaceWeatherAdvisory(
            advisory_id=advisory_id,
            source=Source.NOAA_SWPC,
            serial_number=serial_number,
            message_code=message_code or None,
            event_type=event_type,
            message_type=message_type,
            severity=severity,
            noaa_scale=noaa_scale,
            issue_time=issue_time,
            begin_time=parsed.get("begin_time"),
            end_time=parsed.get("end_time"),
            valid_from=parsed.get("valid_from"),
            valid_until=parsed.get("valid_to"),
            message=message,
            short_description=parsed.get("alert_type"),
            original_text=message,
            potential_impacts=parsed.get("potential_impacts"),
            status=Status.ACTIVE,
        )

    def _parse_message(self, message: str) -> dict:
        """
        Parse the text content of a NOAA alert message.

        Extracts key fields like message code, serial number, times, etc.
        """
        result = {}

        # Normalize line endings
        message = message.replace("\r\n", "\n").replace("\r", "\n")

        # Extract Message Code
        match = re.search(r"Space Weather Message Code:\s*(\w+)", message)
        if match:
            result["message_code"] = match.group(1)

        # Extract Serial Number
        match = re.search(r"Serial Number:\s*(\d+)", message)
        if match:
            result["serial_number"] = match.group(1)

        # Extract Issue Time
        match = re.search(r"Issue Time:\s*(\d{4}\s+\w+\s+\d+\s+\d+)\s*UTC", message)
        if match:
            result["issue_time"] = self._parse_noaa_datetime(match.group(1))

        # Extract alert/warning/watch type
        match = re.search(r"(ALERT|WARNING|WATCH|SUMMARY):\s*(.+?)(?:\n|$)", message)
        if match:
            result["alert_type"] = f"{match.group(1)}: {match.group(2).strip()}"

        # Extract NOAA Scale
        match = re.search(r"NOAA Scale:\s*([GRS]\d)\s*-\s*(\w+)", message)
        if match:
            result["noaa_scale"] = match.group(1)
            result["noaa_scale_desc"] = match.group(2)

        # Extract Begin Time
        match = re.search(r"Begin Time:\s*(\d{4}\s+\w+\s+\d+\s+\d+)\s*UTC", message)
        if match:
            result["begin_time"] = self._parse_noaa_datetime(match.group(1))

        # Extract End Time
        match = re.search(r"End Time:\s*(\d{4}\s+\w+\s+\d+\s+\d+)\s*UTC", message)
        if match:
            result["end_time"] = self._parse_noaa_datetime(match.group(1))

        # Extract Maximum Time
        match = re.search(r"Maximum Time:\s*(\d{4}\s+\w+\s+\d+\s+\d+)\s*UTC", message)
        if match:
            result["max_time"] = self._parse_noaa_datetime(match.group(1))

        # Extract Threshold Reached time
        match = re.search(r"Threshold Reached:\s*(\d{4}\s+\w+\s+\d+\s+\d+)\s*UTC", message)
        if match:
            result["threshold_time"] = self._parse_noaa_datetime(match.group(1))

        # Extract Valid From/To (for warnings)
        match = re.search(r"Valid From:\s*(\d{4}\s+\w+\s+\d+\s+\d+)\s*UTC", message)
        if match:
            result["valid_from"] = self._parse_noaa_datetime(match.group(1))

        match = re.search(r"Valid To:\s*(\d{4}\s+\w+\s+\d+\s+\d+)\s*UTC", message)
        if match:
            result["valid_to"] = self._parse_noaa_datetime(match.group(1))

        # Extract Potential Impacts
        match = re.search(r"Potential Impacts:\s*(.+?)(?:\n\n|\Z)", message, re.DOTALL)
        if match:
            result["potential_impacts"] = match.group(1).strip()

        # Extract specific metrics based on type
        # K-index
        match = re.search(r"K-index of (\d)", message)
        if match:
            result["k_index"] = int(match.group(1))

        # X-ray class
        match = re.search(r"X-ray Class:\s*([A-Z]\d+\.?\d*)", message)
        if match:
            result["xray_class"] = match.group(1)

        # Proton flux
        match = re.search(r"Maximum 10MeV Flux:\s*(\d+)\s*pfu", message)
        if match:
            result["proton_flux"] = int(match.group(1))

        # Electron flux
        match = re.search(r"2MeV Integral Flux exceeded (\d+)pfu", message)
        if match:
            result["electron_flux_threshold"] = int(match.group(1))

        # CME velocity
        match = re.search(r"Estimated Velocity:\s*(\d+)\s*km/s", message)
        if match:
            result["cme_velocity"] = int(match.group(1))

        return result

    def _parse_datetime(self, dt_str: str) -> Optional[datetime]:
        """Parse ISO-ish datetime string from JSON."""
        if not dt_str:
            return None

        # Try common formats
        formats = [
            "%Y-%m-%d %H:%M:%S.%f",
            "%Y-%m-%d %H:%M:%S",
            "%Y-%m-%dT%H:%M:%S.%f",
            "%Y-%m-%dT%H:%M:%S",
        ]

        for fmt in formats:
            try:
                return datetime.strptime(dt_str, fmt).replace(tzinfo=timezone.utc)
            except ValueError:
                continue

        logger.warning(f"Could not parse datetime: {dt_str}")
        return None

    def _parse_noaa_datetime(self, dt_str: str) -> Optional[datetime]:
        """
        Parse NOAA-style datetime string.

        Format: "2026 Jan 20 1856"
        """
        if not dt_str:
            return None

        try:
            # Format: "2026 Jan 20 1856"
            return datetime.strptime(dt_str.strip(), "%Y %b %d %H%M").replace(tzinfo=timezone.utc)
        except ValueError:
            try:
                # Try with full month name
                return datetime.strptime(dt_str.strip(), "%Y %B %d %H%M").replace(tzinfo=timezone.utc)
            except ValueError:
                logger.warning(f"Could not parse NOAA datetime: {dt_str}")
                return None

    def _get_event_type(self, message_code: str) -> EventType:
        """Determine event type from message code."""
        if not message_code:
            return EventType.OTHER

        # Try exact match first
        if message_code in MESSAGE_CODE_MAPPING:
            return MESSAGE_CODE_MAPPING[message_code]

        # Try prefix matches
        for prefix, event_type in MESSAGE_CODE_MAPPING.items():
            if message_code.startswith(prefix):
                return event_type

        # Fallback based on first letter
        if message_code.startswith("K") or message_code.startswith("WAT"):
            return EventType.GEOMAGNETIC_STORM
        elif message_code.startswith("X") or message_code.startswith("XM"):
            return EventType.RADIO_BLACKOUT
        elif message_code.startswith("P") or message_code.startswith("S"):
            return EventType.SOLAR_RADIATION_STORM

        return EventType.OTHER

    def _get_message_type(self, message_code: str, message: str) -> MessageType:
        """Determine message type from code and content."""
        message_upper = message.upper()

        if "ALERT:" in message_upper:
            return MessageType.ALERT
        elif "WARNING:" in message_upper:
            return MessageType.WARNING
        elif "WATCH:" in message_upper:
            return MessageType.WATCH
        elif "SUMMARY:" in message_upper:
            return MessageType.SUMMARY
        elif message_code.startswith("ALT"):
            return MessageType.ALERT
        elif message_code.startswith("WAR"):
            return MessageType.WARNING
        elif message_code.startswith("WAT"):
            return MessageType.WATCH
        elif message_code.startswith("SUM"):
            return MessageType.SUMMARY

        return MessageType.ALERT

    def _get_severity(self, noaa_scale: Optional[str]) -> Optional[Severity]:
        """Map NOAA scale to severity."""
        if not noaa_scale:
            return None
        return SCALE_SEVERITY_MAPPING.get(noaa_scale)

    # -------------------------------------------------------------------------
    # HTML Archive Parsing (FTP archive format)
    # -------------------------------------------------------------------------

    def parse_html(self, content: str) -> Iterator[SpaceWeatherAdvisory]:
        """
        Parse NOAA alerts from HTML archive format.

        The FTP archive at ftp://ftp.swpc.noaa.gov/pub/alerts/ contains HTML files
        with alerts separated by <hr> tags.

        Args:
            content: HTML content from archive file

        Yields:
            SpaceWeatherAdvisory objects
        """
        # Split on <hr> tags to get individual alerts
        # Each alert is wrapped in <p>...</p> blocks after the <hr>
        blocks = re.split(r"<hr\s*/?\s*>", content, flags=re.IGNORECASE)

        for block in blocks:
            block = block.strip()
            if not block:
                continue

            # Skip header/title blocks
            if "<title>" in block.lower() or "<h2>" in block.lower():
                continue

            # Convert HTML to plain text
            message = self._html_to_text(block)
            if not message:
                continue

            # Check if this looks like an alert (has required fields)
            if "Space Weather Message Code:" not in message:
                continue

            try:
                advisory = self._parse_html_message(message)
                if advisory:
                    yield advisory
            except Exception as e:
                logger.warning(f"Failed to parse HTML alert: {e}")

    def parse_html_file(self, path: str) -> Iterator[SpaceWeatherAdvisory]:
        """
        Parse NOAA alerts from a local HTML archive file.

        Args:
            path: Path to the HTML file

        Yields:
            SpaceWeatherAdvisory objects
        """
        with open(path, encoding="utf-8", errors="replace") as f:
            content = f.read()
        yield from self.parse_html(content)

    def _html_to_text(self, html: str) -> str:
        """
        Convert HTML alert block to plain text.

        Converts <br> to newlines, strips tags, and cleans up whitespace.
        """
        # Replace <br> tags with newlines
        text = re.sub(r"<br\s*/?\s*>", "\n", html, flags=re.IGNORECASE)

        # Remove <p> tags but keep content
        text = re.sub(r"</?p\s*>", "\n", text, flags=re.IGNORECASE)

        # Remove any remaining HTML tags
        text = re.sub(r"<[^>]+>", "", text)

        # Decode HTML entities
        text = text.replace("&lt;", "<")
        text = text.replace("&gt;", ">")
        text = text.replace("&amp;", "&")
        text = text.replace("&nbsp;", " ")
        text = text.replace("&#39;", "'")
        text = text.replace("&quot;", '"')

        # Clean up whitespace - collapse multiple newlines but preserve structure
        text = re.sub(r"\n\s*\n\s*\n+", "\n\n", text)
        text = text.strip()

        return text

    def _parse_html_message(self, message: str) -> Optional[SpaceWeatherAdvisory]:
        """
        Parse a single alert from HTML archive format.

        Similar to _parse_json_item but without the JSON wrapper.
        """
        # Parse the message content using shared parser
        parsed = self._parse_message(message)

        # Get issue time from parsed message
        issue_time = parsed.get("issue_time")
        if not issue_time:
            logger.warning("No issue time found in HTML alert")
            return None

        # Determine event type from message code
        message_code = parsed.get("message_code", "")
        if not message_code:
            logger.warning("No message code found in HTML alert")
            return None

        event_type = self._get_event_type(message_code)

        # Determine message type (ALERT, WARNING, WATCH, SUMMARY)
        message_type = self._get_message_type(message_code, message)

        # Extract NOAA scale and map to severity
        noaa_scale = parsed.get("noaa_scale")
        severity = self._get_severity(noaa_scale)

        # Build advisory ID
        serial_number = parsed.get("serial_number")
        advisory_id = f"{message_code}-{serial_number}" if serial_number else message_code

        return SpaceWeatherAdvisory(
            advisory_id=advisory_id,
            source=Source.NOAA_SWPC,
            serial_number=serial_number,
            message_code=message_code or None,
            event_type=event_type,
            message_type=message_type,
            severity=severity,
            noaa_scale=noaa_scale,
            issue_time=issue_time,
            begin_time=parsed.get("begin_time"),
            end_time=parsed.get("end_time"),
            valid_from=parsed.get("valid_from"),
            valid_until=parsed.get("valid_to"),
            message=message,
            short_description=parsed.get("alert_type"),
            original_text=message,
            potential_impacts=parsed.get("potential_impacts"),
            status=Status.ACTIVE,
        )
