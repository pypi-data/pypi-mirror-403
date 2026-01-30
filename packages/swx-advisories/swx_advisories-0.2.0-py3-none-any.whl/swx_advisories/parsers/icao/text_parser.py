"""Parse ICAO space weather advisories from raw text files."""

import logging
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterator, Optional, Union

from swx_advisories.models.advisory import Forecast, ICAOAdvisory, TemporalObservation
from swx_advisories.models.enums import Source, Status
from swx_advisories.models.location import GeographicRegion
from swx_advisories.parsers.icao.location_parser import (
    parse_location_code,
    parse_obs_or_fcst,
    parse_partial_datetime,
)

logger = logging.getLogger(__name__)


class ParseError(Exception):
    """Error parsing ICAO advisory."""

    pass


class ICAOTextParser:
    """
    Parse raw ICAO fnxx01*.txt advisory files.

    ICAO advisories are transmitted as text messages with a standard format:

        ZCZC                            <- Start of message
        FNXX01 EFKL 151200              <- Header: type, station, time
        SWX ADVISORY
        STATUS: (empty or TEST)
        DTG: 20240315/1200Z             <- Date/Time Group (issue time)
        SWXC: PECASUS                   <- Space Weather Center
        ADVISORY NR: 2024/0042
        NR RPLC: VOID                   <- Advisory being replaced
        SWX EFFECT: HF COM MOD          <- Effect + Severity
        OBS SWX: 15/1045Z HNH MNH E000-W180
        FCST SWX +6 HR: 15/1800Z HNH MNH EQN E000-W180
        FCST SWX +12 HR: ...
        FCST SWX +18 HR: ...
        FCST SWX +24 HR: ...
        RMK: Remarks text...
        NXT ADVISORY: BY 20240315/1800Z=
        NNNN                            <- End of message
    """

    # Known ICAO center codes
    KNOWN_STATIONS = {"YMMC", "LFPW", "ZBBB", "UUAG", "EFKL", "EGRR", "KWNP", "RJTD", "CWAO"}

    def parse_directory(self, path: Union[str, Path]) -> Iterator[ICAOAdvisory]:
        """
        Parse all ICAO text files in a directory.

        Args:
            path: Directory containing fnxx01*.txt files

        Yields:
            ICAOAdvisory objects
        """
        path = Path(path)
        if not path.is_dir():
            raise ValueError(f"Not a directory: {path}")

        for txt_file in sorted(path.glob("fnxx01*.txt")):
            logger.debug(f"Parsing {txt_file}")
            try:
                yield from self.parse_file(txt_file)
            except Exception as e:
                logger.error(f"Error parsing {txt_file}: {e}")

    def parse_file(self, path: Union[str, Path]) -> Iterator[ICAOAdvisory]:
        """
        Parse a single ICAO text file.

        A file may contain multiple advisories, each delimited by ZCZC...NNNN.

        Args:
            path: Path to the text file

        Yields:
            ICAOAdvisory objects
        """
        path = Path(path)
        content = path.read_text(encoding="utf-8", errors="replace")
        yield from self.parse_text(content)

    def parse_text(self, content: str) -> Iterator[ICAOAdvisory]:
        """
        Parse ICAO advisory text content.

        Supports two formats:
        1. ZCZC/NNNN delimited (traditional GTS format)
        2. Blank-line delimited (common in web/archive formats)

        Args:
            content: Raw text content (may contain multiple advisories)

        Yields:
            ICAOAdvisory objects
        """
        # Check which format we have
        if "ZCZC" in content:
            # Traditional GTS format with ZCZC/NNNN delimiters
            yield from self._parse_zczc_format(content)
        else:
            # Blank-line delimited format
            yield from self._parse_blank_line_format(content)

    def _parse_zczc_format(self, content: str) -> Iterator[ICAOAdvisory]:
        """Parse ZCZC/NNNN delimited messages."""
        messages = re.split(r"ZCZC\s*", content)

        for message in messages:
            if not message.strip():
                continue
            if "NNNN" not in message:
                continue

            # Extract just the message part (before NNNN)
            message = message.split("NNNN")[0]

            try:
                advisory = self._parse_message(message)
                if advisory and not advisory.is_test:
                    yield advisory
            except ParseError as e:
                logger.warning(f"Failed to parse message: {e}")
            except Exception as e:
                logger.error(f"Unexpected error parsing message: {e}")

    def _parse_blank_line_format(self, content: str) -> Iterator[ICAOAdvisory]:
        """
        Parse blank-line delimited messages.

        Format: Each advisory starts with FNXX header and ends with blank line.
        May have timestamp lines before some advisories (e.g., "2026-01-19 23:59:00")
        """
        lines = content.split("\n")
        current_message_lines = []
        in_message = False

        for line in lines:
            stripped = line.strip()

            # Skip timestamp lines that precede some advisories
            if re.match(r"^\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}$", stripped):
                continue

            # Check for start of new message
            if stripped.startswith("FNXX"):
                # If we were already building a message, process it
                if current_message_lines:
                    message = "\n".join(current_message_lines)
                    try:
                        advisory = self._parse_message(message)
                        if advisory and not advisory.is_test:
                            yield advisory
                    except ParseError as e:
                        logger.warning(f"Failed to parse message: {e}")
                    except Exception as e:
                        logger.error(f"Unexpected error parsing message: {e}")

                # Start new message
                current_message_lines = [line]
                in_message = True
                continue

            # Blank line marks end of message
            if not stripped and in_message and current_message_lines:
                message = "\n".join(current_message_lines)
                try:
                    advisory = self._parse_message(message)
                    if advisory and not advisory.is_test:
                        yield advisory
                except ParseError as e:
                    logger.warning(f"Failed to parse message: {e}")
                except Exception as e:
                    logger.error(f"Unexpected error parsing message: {e}")

                current_message_lines = []
                in_message = False
                continue

            # Add line to current message
            if in_message:
                current_message_lines.append(line)

        # Don't forget last message if file doesn't end with blank line
        if current_message_lines:
            message = "\n".join(current_message_lines)
            try:
                advisory = self._parse_message(message)
                if advisory and not advisory.is_test:
                    yield advisory
            except ParseError as e:
                logger.warning(f"Failed to parse message: {e}")
            except Exception as e:
                logger.error(f"Unexpected error parsing message: {e}")

    def _parse_message(self, message: str) -> Optional[ICAOAdvisory]:
        """Parse a single ICAO advisory message."""
        lines = message.strip().split("\n")

        fields = {}
        fields["_original_text"] = message.strip()
        current_field = None

        for line in lines:
            line_stripped = line.strip()

            # Skip empty lines
            if not line_stripped:
                continue

            # Header line: FNXX01 EFKL 151200 or FNXX02 EFLK 201739
            if line_stripped.startswith("FNXX"):
                parts = line_stripped.split()
                fields["header_type"] = parts[0] if len(parts) > 0 else None
                fields["header_center"] = parts[1] if len(parts) > 1 else None
                fields["header_time"] = parts[2] if len(parts) > 2 else None
                continue

            # Skip "SWX ADVISORY" line
            if "SWX ADVISORY" in line_stripped:
                continue

            # Field: Value lines
            # Check if line contains a colon and looks like a field
            if ":" in line_stripped:
                # Split on first colon only
                key, _, value = line_stripped.partition(":")
                key = key.strip()
                value = value.strip()

                # Check if this is a known field or looks like one
                # (avoids treating continuation lines with colons as new fields)
                known_fields = {
                    "DTG", "SWXC", "SWX EFFECT", "ADVISORY NR", "NR RPLC",
                    "OBS SWX", "RMK", "NXT ADVISORY", "STATUS",
                }
                is_fcst = key.startswith("FCST SWX")
                is_known = key in known_fields or is_fcst

                if is_known:
                    # Remove trailing = from last field
                    if value.endswith("="):
                        value = value[:-1].strip()

                    fields[key] = value
                    current_field = key
                    continue

            # Continuation line - append to current field
            # These can be indented or not, but follow a field line
            if current_field and current_field in fields:
                # Append with space
                fields[current_field] += " " + line_stripped
                # Remove any trailing = that may have been added
                if fields[current_field].endswith("="):
                    fields[current_field] = fields[current_field][:-1].strip()

        return self._fields_to_advisory(fields)

    def _fields_to_advisory(self, fields: dict) -> Optional[ICAOAdvisory]:
        """Convert parsed fields to ICAOAdvisory model."""
        # Check for required fields
        required = ["DTG", "SWXC", "ADVISORY NR", "SWX EFFECT", "OBS SWX"]
        missing = [f for f in required if not fields.get(f)]
        if missing:
            raise ParseError(f"Missing required fields: {missing}")

        # Check for TEST status
        is_test = fields.get("STATUS", "").upper() == "TEST"
        if "TEST" in fields.get("RMK", "").upper():
            is_test = True

        # Parse DTG (issue time)
        dtg = fields["DTG"]
        try:
            issue_time = self._parse_dtg(dtg)
        except Exception as e:
            raise ParseError(f"Cannot parse DTG '{dtg}': {e}")

        # Parse OBS SWX (observation) - now includes severity extraction
        obs_text = fields["OBS SWX"]
        try:
            parsed_obs = parse_obs_or_fcst(obs_text, dtg)
            observation = self._build_observation(parsed_obs, dtg)
        except Exception as e:
            raise ParseError(f"Cannot parse OBS SWX '{obs_text}': {e}")

        # Parse effect and severity
        # Effect type is in SWX EFFECT field (e.g., "HF COM", "GNSS")
        # Severity may be in SWX EFFECT or in OBS SWX field
        effect_text = fields["SWX EFFECT"]
        effect, effect_severity = self._parse_effect(effect_text)

        # Use severity from OBS SWX if available, otherwise from SWX EFFECT
        severity = parsed_obs.severity or effect_severity

        # Parse forecasts
        forecasts = []
        for hours in [6, 12, 18, 24]:
            # Handle both "FCST SWX +6 HR" and "FCST SWX  +6 HR" (double space)
            fcst_key = None
            for key in fields:
                if f"+{hours} HR" in key and "FCST" in key:
                    fcst_key = key
                    break

            if fcst_key:
                fcst_text = fields[fcst_key]
                try:
                    forecast = self._parse_forecast(fcst_text, dtg, hours)
                    forecasts.append(forecast)
                except Exception as e:
                    logger.warning(f"Cannot parse {fcst_key}: {e}")

        # Parse replaces field
        replaces_id = fields.get("NR RPLC", "").strip()
        if replaces_id.upper() == "VOID" or not replaces_id:
            replaces_id = None

        # Determine source from center
        center = fields["SWXC"].strip()
        center_country = fields.get("header_center", "")
        source = self._determine_source(center, center_country)

        return ICAOAdvisory(
            advisory_id=fields["ADVISORY NR"].strip(),
            center=center,
            center_country=center_country,
            source=source,
            effect=effect,
            severity=severity,
            issue_time=issue_time,
            observation=observation,
            forecasts=forecasts,
            replaces_id=replaces_id,
            remark=fields.get("RMK", "").strip() or None,
            next_advisory=fields.get("NXT ADVISORY", "").strip() or None,
            is_test=is_test,
            status=Status.TEST if is_test else Status.ACTIVE,
            original_text=fields.get("_original_text"),
        )

    def _build_observation(self, parsed: "ParsedObservation", dtg: str) -> TemporalObservation:
        """Build TemporalObservation from parsed observation data."""
        from swx_advisories.parsers.icao.location_parser import ParsedObservation

        # Parse time
        if "/" in parsed.time_str:
            iso_time = parse_partial_datetime(dtg, parsed.time_str)
            obs_time = datetime.fromisoformat(iso_time.replace("Z", "+00:00"))
        else:
            # Fallback: use DTG time
            obs_time = self._parse_dtg(dtg)

        return TemporalObservation(
            time=obs_time,
            hours_ahead=0,
            location=parsed.location,
        )

    def _parse_dtg(self, dtg: str) -> datetime:
        """Parse Date/Time Group to datetime."""
        # Format: 20240315/1200Z or 20240315/1200
        dtg = dtg.strip().rstrip("Z")

        if "/" in dtg:
            date_part, time_part = dtg.split("/")
        else:
            # Try to split by length
            date_part = dtg[:8]
            time_part = dtg[8:]

        year = int(date_part[:4])
        month = int(date_part[4:6])
        day = int(date_part[6:8])
        hour = int(time_part[:2])
        minute = int(time_part[2:4]) if len(time_part) >= 4 else 0

        return datetime(year, month, day, hour, minute, 0, tzinfo=timezone.utc)

    def _parse_forecast(self, fcst_text: str, dtg: str, hours: int) -> Forecast:
        """
        Parse FCST SWX field.

        Format variations:
        - "15/1800Z HNH MNH EQN E000-W180"
        - "20/2200Z SEV EQS EQN MNH MSH W180 - E180"
        - "21/0000Z NOT AVBL"
        - "20/1300Z NO SWX EXP"
        """
        # Use the unified parser that handles severity extraction
        parsed = parse_obs_or_fcst(fcst_text, dtg)

        # Parse time
        if "/" in parsed.time_str:
            iso_time = parse_partial_datetime(dtg, parsed.time_str)
            fcst_time = datetime.fromisoformat(iso_time.replace("Z", "+00:00"))
        else:
            # Fallback
            fcst_time = self._parse_dtg(dtg)

        return Forecast(
            hours_ahead=hours,
            time=fcst_time,
            location=parsed.location,
            severity=parsed.severity,
        )

    def _parse_effect(self, effect_text: str) -> tuple[str, Optional[str]]:
        """
        Parse SWX EFFECT field into effect and severity.

        Format variations:
        - "HF COM MOD" -> effect="HF COM", severity="MOD"
        - "GNSS SEV" -> effect="GNSS", severity="SEV"
        - "HF COM" -> effect="HF COM", severity=None (severity in OBS field)
        - "GNSS" -> effect="GNSS", severity=None
        """
        parts = effect_text.strip().split()
        if not parts:
            raise ParseError(f"Cannot parse SWX EFFECT: {effect_text}")

        # Check if last word is severity
        if parts[-1] in ("MOD", "SEV"):
            severity = parts[-1]
            effect = " ".join(parts[:-1])
            return effect, severity

        # Check if MOD/SEV is embedded somewhere
        if "MOD" in effect_text:
            severity = "MOD"
            effect = effect_text.replace("MOD", "").strip()
            return effect, severity
        elif "SEV" in effect_text:
            severity = "SEV"
            effect = effect_text.replace("SEV", "").strip()
            return effect, severity

        # No severity in this field - it's in OBS SWX instead
        return effect_text.strip(), None

    def _determine_source(self, center: str, center_country: str) -> Source:
        """Determine source enum from center codes."""
        center_upper = center.upper()

        if "PECASUS" in center_upper:
            return Source.ICAO_PECASUS
        elif "SWPC" in center_upper or center_country == "KWNP":
            return Source.ICAO_SWPC
        elif "ACFJ" in center_upper:
            return Source.ICAO_ACFJ

        # Try to match by country code
        country_map = {
            "EFKL": Source.ICAO_EFKL,
            "EGRR": Source.ICAO_EGRR,
            "LFPW": Source.ICAO_LFPW,
            "KWNP": Source.ICAO_KWNP,
            "CWAO": Source.ICAO_CWAO,
            "YMMC": Source.ICAO_YMMC,
            "RJTD": Source.ICAO_RJTD,
            "ZBBB": Source.ICAO_ZBBB,
        }

        return country_map.get(center_country, Source.ICAO_PECASUS)
