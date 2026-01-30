"""Pytest fixtures for swx-advisories tests."""

import sys
from pathlib import Path

import pytest

# Add src to path for local testing
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from swx_advisories import (
    ICAOFetcher,
    NOAAFetcher,
    ICAOTextParser,
)
from swx_advisories.parsers.icao import ICAOEventBuilder
from swx_advisories.parsers.noaa import NOAAParser


@pytest.fixture
def fixtures_dir() -> Path:
    """Path to test fixtures directory."""
    return Path(__file__).parent / "fixtures"


@pytest.fixture
def sample_icao_file(fixtures_dir) -> Path:
    """Path to sample ICAO advisories file."""
    return fixtures_dir / "sample_icao_advisories.txt"


@pytest.fixture
def sample_noaa_file(fixtures_dir) -> Path:
    """Path to sample NOAA alerts file."""
    return fixtures_dir / "noaa_alerts_sample.json"


@pytest.fixture
def icao_parser() -> ICAOTextParser:
    """Create an ICAO text parser."""
    return ICAOTextParser()


@pytest.fixture
def icao_event_builder() -> ICAOEventBuilder:
    """Create an ICAO event builder."""
    return ICAOEventBuilder()


@pytest.fixture
def noaa_parser() -> NOAAParser:
    """Create a NOAA parser."""
    return NOAAParser()


@pytest.fixture
def icao_advisories(icao_parser, sample_icao_file):
    """Parse and return ICAO advisories from sample file."""
    return list(icao_parser.parse_file(sample_icao_file))


@pytest.fixture
def icao_events(icao_advisories, icao_event_builder):
    """Build and return ICAO events from sample advisories."""
    return icao_event_builder.build_events(icao_advisories)


@pytest.fixture
def noaa_alerts(noaa_parser, sample_noaa_file):
    """Parse and return NOAA alerts from sample file."""
    return list(noaa_parser.parse_json_file(sample_noaa_file))


@pytest.fixture
def icao_fetcher(sample_icao_file) -> ICAOFetcher:
    """Create an ICAO fetcher for sample file."""
    return ICAOFetcher(sample_icao_file)


@pytest.fixture
def noaa_fetcher(sample_noaa_file) -> NOAAFetcher:
    """Create a NOAA fetcher for sample file."""
    return NOAAFetcher(from_file=sample_noaa_file)
