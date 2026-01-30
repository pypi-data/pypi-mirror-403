"""Enumerations for space weather advisory classification."""

from enum import Enum


class Source(str, Enum):
    """Advisory issuing organization/center."""

    # ICAO Space Weather Centers
    ICAO_PECASUS = "icao_pecasus"  # Finland-led consortium (FMI)
    ICAO_SWPC = "icao_swpc"  # NOAA Space Weather Prediction Center
    ICAO_ACFJ = "icao_acfj"  # Australia, Canada, France, Japan consortium

    # Individual ICAO center codes (for header identification)
    ICAO_EFKL = "icao_efkl"  # Finland
    ICAO_EGRR = "icao_egrr"  # UK Met Office
    ICAO_LFPW = "icao_lfpw"  # France (Meteo-France)
    ICAO_KWNP = "icao_kwnp"  # USA (NOAA/SWPC)
    ICAO_CWAO = "icao_cwao"  # Canada
    ICAO_YMMC = "icao_ymmc"  # Australia
    ICAO_RJTD = "icao_rjtd"  # Japan
    ICAO_ZBBB = "icao_zbbb"  # China

    # Non-ICAO sources
    NOAA_SWPC = "noaa_swpc"  # NOAA alerts (not ICAO format)
    MOSWOC = "moswoc"  # UK Met Office Space Weather (future)


class EventType(str, Enum):
    """Unified event type classification."""

    # Solar origin
    SOLAR_FLARE = "solar_flare"  # General solar flare
    X_RAY_FLARE = "x_ray_flare"  # X-ray flare specifically
    RADIO_BURST = "radio_burst"  # Solar radio burst
    CME = "cme"  # Coronal Mass Ejection

    # Particle events
    PROTON_EVENT = "proton_event"
    ELECTRON_FLUX = "electron_flux"
    SOLAR_RADIATION_STORM = "solar_radiation_storm"  # NOAA S-scale

    # Geomagnetic
    GEOMAGNETIC_STORM = "geomagnetic_storm"  # NOAA G-scale
    GEOMAGNETIC_SUDDEN_IMPULSE = "geomagnetic_sudden_impulse"

    # Ionospheric / Communication (ICAO effects)
    HF_BLACKOUT = "hf_blackout"  # ICAO "HF COM"
    RADIO_BLACKOUT = "radio_blackout"  # NOAA R-scale
    GNSS_DEGRADATION = "gnss_degradation"  # ICAO "GNSS"

    # Radiation
    RADIATION_STORM = "radiation_storm"  # ICAO "RAD"

    # Atmospheric
    STRATOSPHERIC_WARMING = "stratospheric_warming"

    # Catch-all
    OTHER = "other"


class Severity(str, Enum):
    """Normalized severity levels."""

    MINOR = "minor"  # NOAA scale 1, below ICAO threshold
    MODERATE = "moderate"  # NOAA scale 2-3, ICAO MOD
    SEVERE = "severe"  # NOAA scale 4, ICAO SEV
    EXTREME = "extreme"  # NOAA scale 5


class MessageType(str, Enum):
    """Type of advisory message."""

    ALERT = "alert"  # Real-time threshold crossing
    WARNING = "warning"  # Predicted event
    WATCH = "watch"  # Potential for event
    SUMMARY = "summary"  # Event summary/recap
    ADVISORY = "advisory"  # ICAO-style advisory
    CANCELLATION = "cancellation"  # Cancels previous message


class Status(str, Enum):
    """Advisory lifecycle status."""

    ACTIVE = "active"
    CANCELLED = "cancelled"
    SUPERSEDED = "superseded"  # Replaced by newer advisory
    EXPIRED = "expired"
    TEST = "test"  # Test message, not operational


# ICAO center code to country/organization mapping
ICAO_CENTER_NAMES = {
    "EFKL": "Finland (FMI)",
    "EGRR": "United Kingdom (Met Office)",
    "LFPW": "France (Météo-France)",
    "KWNP": "United States (NOAA/SWPC)",
    "CWAO": "Canada (ECCC)",
    "YMMC": "Australia (BoM)",
    "RJTD": "Japan (JMA)",
    "ZBBB": "China (CMA)",
}

# NOAA Space Weather Message Code patterns
NOAA_SWMC_PATTERNS = {
    # Electron flux
    "ALTEF": (EventType.ELECTRON_FLUX, MessageType.ALERT),
    # Geomagnetic
    "ALTK": (EventType.GEOMAGNETIC_STORM, MessageType.ALERT),
    "SUMK": (EventType.GEOMAGNETIC_STORM, MessageType.SUMMARY),
    "WARK": (EventType.GEOMAGNETIC_STORM, MessageType.WARNING),
    "WATA": (EventType.GEOMAGNETIC_STORM, MessageType.WATCH),
    "SUD": (EventType.GEOMAGNETIC_SUDDEN_IMPULSE, MessageType.WARNING),
    # Proton
    "ALTPC": (EventType.PROTON_EVENT, MessageType.ALERT),
    "ALTPX": (EventType.PROTON_EVENT, MessageType.ALERT),
    "SUMPC": (EventType.PROTON_EVENT, MessageType.SUMMARY),
    "SUMPX": (EventType.PROTON_EVENT, MessageType.SUMMARY),
    "WARPC": (EventType.PROTON_EVENT, MessageType.WARNING),
    "WARPX": (EventType.PROTON_EVENT, MessageType.WARNING),
    # Radio
    "ALTTP": (EventType.RADIO_BURST, MessageType.ALERT),
    "SUM10R": (EventType.RADIO_BURST, MessageType.SUMMARY),
    # Stratospheric
    "ALTSTR": (EventType.STRATOSPHERIC_WARMING, MessageType.ALERT),
    # X-ray
    "ALTXMF": (EventType.X_RAY_FLARE, MessageType.ALERT),
    "SUMX": (EventType.X_RAY_FLARE, MessageType.SUMMARY),
}

# ICAO effect to EventType mapping
ICAO_EFFECT_MAPPING = {
    "HF COM": EventType.HF_BLACKOUT,
    "GNSS": EventType.GNSS_DEGRADATION,
    "RAD": EventType.RADIATION_STORM,
}
