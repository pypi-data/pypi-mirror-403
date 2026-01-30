# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.2.0] - 2025-01-26

### Added
- `FetchResult.events` property for ICAO fetcher - events are now built automatically during `fetch()` and available via `result.events`
- `build_events` parameter to `ICAOFetcher.fetch()` and `from_text()` to optionally disable event building
- `message_code` field to NOAA advisories (e.g., "ALTK06", "WATA50")
- `original_text` field to preserve raw advisory text
- `NOAAArchiveFetcher` for fetching from NOAA HTML and FTP archives
- Progress callbacks for long-running fetch operations
- All datetimes are now timezone-aware (UTC)
- Comprehensive documentation in README

### Changed
- ICAO events are now built eagerly during `fetch()` instead of requiring separate `fetch_events()` call
- `ICAOEventBuilder` is no longer part of the public API (use `result.events` instead)

### Removed
- `ICAOFetcher.fetch_events()` method (use `result.events` instead)
- `ICAOFetcher.build_events()` public method (now private `_build_events()`)

## [0.1.0] - 2025-01-20

### Added
- Initial release
- ICAO advisory parsing (fnxx01/fnxx02 files)
- NOAA alert parsing from SWPC API
- Event chain building for ICAO advisories
- DataFrame adapters (flat, timeline, HAPI formats)
- Support for latitude bands and polygon coordinates
- G/S/R scale extraction for NOAA alerts
