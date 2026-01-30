# swx-advisories

A Python package for parsing and analyzing space weather advisories from ICAO and NOAA/SWPC sources.

## Features

- **ICAO Advisory Parsing**: Parse ICAO space weather advisories (fnxx01/fnxx02 files) with support for:
  - Blank-line and ZCZC/NNNN delimited formats
  - Latitude bands (HNH, MNH, EQN, EQS, MSH, HSH) and polygon coordinates
  - Event chain building via NR RPLC linking
  - HF COM and GNSS effect types with MOD/SEV severity

- **NOAA Alert Parsing**: Parse NOAA Space Weather Prediction Center alerts with:
  - Live API fetching from services.swpc.noaa.gov
  - G/S/R scale extraction (geomagnetic, solar radiation, radio blackout)
  - Message type classification (ALERT, WARNING, WATCH, SUMMARY)
  - K-index, X-ray class, and proton flux metrics

- **DataFrame Adapters**: Convert advisories to pandas DataFrames in multiple formats:
  - Flat format (one row per advisory/event)
  - Timeline format (time-indexed for visualization)
  - HAPI format (Heliophysics API compatible)

## Installation

```bash
pip install swx-advisories
```

Or install from source:

```bash
git clone https://gitlab.com/KNMI-OSS/spaceweather/swx-advisories.git
cd swx-advisories
pip install -e .
```

## Quick Start

### ICAO Advisories

```python
from swx_advisories import ICAOFetcher, to_dataframe

# Load advisories from a file or directory
fetcher = ICAOFetcher("/path/to/advisories/")
result = fetcher.fetch()

# Access advisories and events directly from the result
for advisory in result.advisories:
    print(f"{advisory.advisory_id}: {advisory.effect}")

for event in result.events:
    print(f"{event.event_id}: {event.effect} ({event.peak_severity})")
    print(f"  Duration: {event.duration}")
    print(f"  Advisories: {event.num_advisories}")

# Convert to DataFrames
df_advisories = to_dataframe(result.advisories)
df_events = to_dataframe(result.events)
```

### NOAA Alerts

```python
from swx_advisories import NOAAFetcher

# Fetch from live NOAA API
fetcher = NOAAFetcher()
result = fetcher.fetch()

for alert in result:
    print(f"{alert.advisory_id}: {alert.event_type.value}")
    print(f"  Scale: {alert.noaa_scale}")
    print(f"  Severity: {alert.severity}")
```

### Convert to DataFrame

```python
from swx_advisories import ICAOFetcher, to_dataframe

fetcher = ICAOFetcher("/path/to/advisories/")
result = fetcher.fetch()

# Get pandas DataFrames
df_advisories = to_dataframe(result.advisories, format="flat")
df_events = to_dataframe(result.events, format="flat")
print(df_events[["event_id", "effect", "peak_severity", "duration_hours"]])
```

## ICAO Advisories

ICAO space weather advisories are issued by designated Space Weather Centers (SWXCs) to warn aviation of space weather impacts on HF communications and GNSS navigation.

### Fetching Advisories

```python
from swx_advisories import ICAOFetcher

# From a single file
fetcher = ICAOFetcher("/path/to/fnxx01_advisory.txt")
result = fetcher.fetch()

# From a directory (searches for fnxx01*.txt and fnxx02*.txt)
fetcher = ICAOFetcher("/path/to/advisory_directory/")
result = fetcher.fetch()

# Access advisories
for advisory in result:
    print(f"{advisory.advisory_id}: {advisory.effect} - {advisory.severity}")

# Check for errors
if not result.success:
    print(f"Errors: {result.errors}")
```

### Building Event Chains

Advisories are linked via the `NR RPLC` field. The fetcher automatically builds these into event chains:

```python
from swx_advisories import ICAOFetcher

fetcher = ICAOFetcher("/path/to/advisories/")
result = fetcher.fetch()

# Events are automatically built and available on result.events
for event in result.events:
    print(f"\nEvent: {event.event_id}")
    print(f"  Effect: {event.effect}")
    print(f"  Peak severity: {event.peak_severity}")
    print(f"  Start: {event.issue_start}")
    print(f"  End: {event.issue_end}")
    print(f"  Duration: {event.duration}")
    print(f"  Centers: {', '.join(event.centers)}")
    print(f"  Advisories in chain: {event.num_advisories}")

# Skip event building if not needed
result = fetcher.fetch(build_events=False)
assert result.events is None
```

### Advisory Structure

Each `ICAOAdvisory` contains:

```python
advisory.advisory_id      # e.g., "2026/0042"
advisory.center           # e.g., "PECASUS", "ACFJ"
advisory.effect           # "HF COM" or "GNSS"
advisory.severity         # "MOD", "SEV", or None
advisory.issue_time       # datetime
advisory.observation      # TemporalObservation with time and location
advisory.forecasts        # List of 4 Forecast objects (+6h, +12h, +18h, +24h)
advisory.replaces_id      # ID of advisory this replaces, or None if opening
advisory.is_opening       # True if this starts a new event chain
advisory.remark           # Free-text remarks
```

### Parsing Raw Text

```python
from swx_advisories import ICAOFetcher

text = """FNXX01 EFKL 201549
SWX ADVISORY
DTG:              20260120/1549Z
SWXC:             PECASUS
SWX EFFECT:       GNSS
ADVISORY NR:      2026/99
OBS SWX:          20/1542Z SEV N55 E055 - N85 E055 - N85 E005 - N55 E005 - N55 E055
FCST SWX +6 HR:   20/2200Z NOT AVBL
FCST SWX +12 HR:  21/0400Z NOT AVBL
FCST SWX +18 HR:  21/1000Z NOT AVBL
FCST SWX +24 HR:  21/1600Z NOT AVBL
RMK:              SPACE WEATHER EVENT IN PROGRESS
NXT ADVISORY:     NO FURTHER ADVISORIES=
"""

result = ICAOFetcher.from_text(text)
for adv in result:
    print(f"{adv.advisory_id}: {adv.effect}")
```

## NOAA Alerts

NOAA Space Weather Prediction Center (SWPC) issues alerts, warnings, and watches for space weather events using the G/S/R scale system.

### Fetching from API

```python
from swx_advisories import NOAAFetcher

# Fetch all recent alerts from NOAA API
fetcher = NOAAFetcher()
result = fetcher.fetch()

print(f"Fetched {result.count} alerts")
for alert in result:
    print(f"{alert.advisory_id}: {alert.event_type.value} ({alert.noaa_scale})")
```

### Fetching from Local File

```python
from swx_advisories import NOAAFetcher

# Load from a local JSON file (same format as NOAA API)
fetcher = NOAAFetcher(from_file="/path/to/alerts.json")
result = fetcher.fetch()
```

### Filtering Alerts

```python
from swx_advisories import NOAAFetcher, EventType, MessageType

fetcher = NOAAFetcher()

# Filter by event type
geomag = fetcher.fetch_by_type(EventType.GEOMAGNETIC_STORM)
radio = fetcher.fetch_by_type(EventType.RADIO_BLACKOUT)

# Filter by message type
alerts = fetcher.fetch_active_alerts()    # ALERT messages only
warnings = fetcher.fetch_warnings()        # WARNING messages only
watches = fetcher.fetch_watches()          # WATCH messages only
```

### Alert Structure

Each `SpaceWeatherAdvisory` contains:

```python
alert.advisory_id        # e.g., "ALTK06-690"
alert.event_type         # EventType enum (GEOMAGNETIC_STORM, RADIO_BLACKOUT, etc.)
alert.message_type       # MessageType enum (ALERT, WARNING, WATCH, SUMMARY)
alert.severity           # Severity enum (MINOR, MODERATE, SEVERE, EXTREME)
alert.noaa_scale         # e.g., "G2", "S1", "R3"
alert.issue_time         # datetime
alert.begin_time         # datetime (if available)
alert.end_time           # datetime (if available)
alert.short_description  # Brief description of the event
alert.potential_impacts  # Description of potential impacts
```

### NOAA Scales

The package extracts NOAA space weather scales:

| Scale | Type | Levels |
|-------|------|--------|
| G | Geomagnetic Storm | G1 (Minor) to G5 (Extreme) |
| S | Solar Radiation Storm | S1 (Minor) to S5 (Extreme) |
| R | Radio Blackout | R1 (Minor) to R5 (Extreme) |

## DataFrame Adapters

Convert advisories and events to pandas DataFrames for analysis and visualization.

### Unified Interface

```python
from swx_advisories import ICAOFetcher, NOAAFetcher, to_dataframe

# ICAO advisories and events to DataFrame
icao = ICAOFetcher("/path/to/advisories/")
result = icao.fetch()
df_advisories = to_dataframe(result.advisories, format="flat")
df_events = to_dataframe(result.events, format="flat")

# NOAA alerts to DataFrame
noaa = NOAAFetcher()
alerts = noaa.fetch().advisories
df = to_dataframe(alerts, format="flat")
```

### Output Formats

**Flat format** - One row per advisory or event:

```python
from swx_advisories import icao_advisories_to_dataframe, icao_events_to_dataframe

# Advisories DataFrame
df = icao_advisories_to_dataframe(advisories)
# Columns: advisory_id, center, effect, severity, issue_time, obs_time,
#          lat_min, lat_max, lon_min, lon_max, replaces_id, ...

# Events DataFrame
df = icao_events_to_dataframe(events)
# Columns: event_id, effect, peak_severity, num_advisories, duration_hours,
#          issue_start, issue_end, centers, ...
```

**Timeline format** - Time-indexed for visualization:

```python
from swx_advisories.adapters.dataframe import icao_timeline_dataframe

df = icao_timeline_dataframe(events)
# Columns: time, event_id, effect, severity, is_start, is_end

# With resampling to regular intervals
df = icao_timeline_dataframe(events, resample="1h")
# Columns: time, event_id, effect, severity, is_active
```

**HAPI format** - Heliophysics API compatible:

```python
from swx_advisories.adapters.dataframe import to_hapi_format

df = to_hapi_format(events)
# Time-indexed DataFrame pivoted by event type
```

### NOAA DataFrames

```python
from swx_advisories import noaa_alerts_to_dataframe
from swx_advisories.adapters.dataframe import noaa_timeline_dataframe

# Flat format
df = noaa_alerts_to_dataframe(alerts)
# Columns: advisory_id, event_type, message_type, severity, noaa_scale,
#          issue_time, begin_time, end_time, short_description, ...

# Timeline format
df = noaa_timeline_dataframe(alerts)
# Columns: time, advisory_id, event_type, severity, noaa_scale, is_start, is_end
```

## Data Models

### Enums

```python
from swx_advisories import EventType, MessageType, Severity, Source

# Event types
EventType.HF_BLACKOUT           # ICAO HF COM
EventType.GNSS_DEGRADATION      # ICAO GNSS
EventType.GEOMAGNETIC_STORM     # NOAA G-scale
EventType.SOLAR_RADIATION_STORM # NOAA S-scale
EventType.RADIO_BLACKOUT        # NOAA R-scale
EventType.SOLAR_FLARE
EventType.CME

# Message types (NOAA)
MessageType.ALERT
MessageType.WARNING
MessageType.WATCH
MessageType.SUMMARY

# Severity levels
Severity.MINOR
Severity.MODERATE
Severity.SEVERE
Severity.EXTREME
```

### Location Models

```python
from swx_advisories import GeographicRegion, LatitudeBand

# Latitude bands used in ICAO advisories
LatitudeBand.HNH  # High Northern Hemisphere (60-90N)
LatitudeBand.MNH  # Middle Northern Hemisphere (30-60N)
LatitudeBand.EQN  # Equatorial Northern (0-30N)
LatitudeBand.EQS  # Equatorial Southern (0-30S)
LatitudeBand.MSH  # Middle Southern Hemisphere (30-60S)
LatitudeBand.HSH  # High Southern Hemisphere (60-90S)

# Geographic region with bounds
region = GeographicRegion(
    lat_min=-90, lat_max=90,
    lon_min=-180, lon_max=180,
    text="Global coverage"
)
```

## API Reference

### Fetchers

| Class | Description |
|-------|-------------|
| `ICAOFetcher(path)` | Load ICAO advisories from file or directory |
| `NOAAFetcher(from_file=None)` | Fetch NOAA alerts from API or local file |
| `FetchResult` | Container with advisories, metadata, and errors |

### Parsers

| Class | Description |
|-------|-------------|
| `ICAOTextParser` | Parse raw ICAO advisory text |
| `NOAAParser` | Parse NOAA JSON alert data |

### Adapters

| Function | Description |
|----------|-------------|
| `to_dataframe(data, format)` | Auto-detect and convert to DataFrame |
| `icao_advisories_to_dataframe(advisories)` | ICAO advisories to flat DataFrame |
| `icao_events_to_dataframe(events)` | ICAO events to flat DataFrame |
| `icao_timeline_dataframe(events, resample)` | ICAO events to timeline DataFrame |
| `noaa_alerts_to_dataframe(alerts)` | NOAA alerts to flat DataFrame |
| `noaa_timeline_dataframe(alerts)` | NOAA alerts to timeline DataFrame |
| `to_hapi_format(data)` | Convert to HAPI-compatible format |

## Development

### Running Tests

```bash
# Install dev dependencies
pip install -e ".[dev]"

# Run tests
pytest tests/ -v
```

### Test Coverage

The package includes 96 tests covering:
- ICAO text parsing and event building
- NOAA message parsing and alert extraction
- Fetcher functionality
- DataFrame adapter conversions

## License

MIT License - see LICENSE file for details.

## Acknowledgments

- ICAO for the space weather advisory format specification
- NOAA Space Weather Prediction Center for the alerts API
