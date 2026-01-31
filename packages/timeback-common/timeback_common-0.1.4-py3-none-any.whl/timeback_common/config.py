"""
Platform Configuration

Centralized platform endpoints and API path profiles for all Timeback services.
This is the single source of truth for platform URLs and paths.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

# ═══════════════════════════════════════════════════════════════════════════════
# TYPE DEFINITIONS
# ═══════════════════════════════════════════════════════════════════════════════

Platform = Literal["BEYOND_AI", "LEARNWITH_AI"]
Environment = Literal["staging", "production"]

DEFAULT_PLATFORM: Platform = "BEYOND_AI"

# ═══════════════════════════════════════════════════════════════════════════════
# BEYONDAI PLATFORM ENDPOINTS
# ═══════════════════════════════════════════════════════════════════════════════

BEYONDAI_TOKEN_URLS: dict[Environment, str] = {
    "staging": "https://staging-beyond-timeback-api-2-idp.auth.us-east-1.amazoncognito.com/oauth2/token",
    "production": "https://prod-beyond-timeback-api-2-idp.auth.us-east-1.amazoncognito.com/oauth2/token",
}

BEYONDAI_API_URLS: dict[Environment, str] = {
    "staging": "https://api.staging.alpha-1edtech.ai",
    "production": "https://api.alpha-1edtech.ai",
}

BEYONDAI_CALIPER_URLS: dict[Environment, str] = {
    "staging": "https://caliper.staging.alpha-1edtech.ai",
    "production": "https://caliper.alpha-1edtech.ai",
}

BEYONDAI_ENDPOINTS = {
    "api": BEYONDAI_API_URLS,
    "caliper": BEYONDAI_CALIPER_URLS,
    "token": BEYONDAI_TOKEN_URLS,
}

# ═══════════════════════════════════════════════════════════════════════════════
# LEARNWITHAI PLATFORM ENDPOINTS
# ═══════════════════════════════════════════════════════════════════════════════

LEARNWITHAI_TOKEN_URLS: dict[Environment, str] = {
    "staging": "https://platform.dev.timeback.com/auth/1.0/token",
    "production": "https://platform.timeback.com/auth/1.0/token",
}

LEARNWITHAI_API_URLS: dict[Environment, str] = {
    "staging": "https://platform.dev.timeback.com",
    "production": "https://platform.timeback.com",
}

LEARNWITHAI_CALIPER_URLS: dict[Environment, str] = {
    "staging": "https://platform.dev.timeback.com",
    "production": "https://platform.timeback.com",
}

LEARNWITHAI_ENDPOINTS = {
    "api": LEARNWITHAI_API_URLS,
    "caliper": LEARNWITHAI_CALIPER_URLS,
    "token": LEARNWITHAI_TOKEN_URLS,
}

# ═══════════════════════════════════════════════════════════════════════════════
# PLATFORM ENDPOINT MAP
# ═══════════════════════════════════════════════════════════════════════════════

PLATFORM_ENDPOINTS: dict[str, dict[str, dict[Environment, str]]] = {
    "BEYOND_AI": BEYONDAI_ENDPOINTS,
    "LEARNWITH_AI": LEARNWITHAI_ENDPOINTS,
}

# ═══════════════════════════════════════════════════════════════════════════════
# PATH PROFILE DATACLASSES
# ═══════════════════════════════════════════════════════════════════════════════


@dataclass
class CaliperPaths:
    """Caliper API path profiles."""

    send: str
    validate: str | None
    list: str | None
    get: str | None
    job_status: str | None


@dataclass
class OneRosterPaths:
    """OneRoster API path profiles."""

    rostering: str = "/ims/oneroster/rostering/v1p2"
    gradebook: str = "/ims/oneroster/gradebook/v1p2"
    resources: str = "/ims/oneroster/resources/v1p2"


@dataclass
class EdubridgePaths:
    """EduBridge API path profiles."""

    base: str = "/edubridge"


@dataclass
class PlatformPaths:
    """All service path profiles for a platform."""

    oneroster: OneRosterPaths
    edubridge: EdubridgePaths | None  # None means unsupported on platform
    caliper: CaliperPaths


# ═══════════════════════════════════════════════════════════════════════════════
# BEYONDAI PATHS
# ═══════════════════════════════════════════════════════════════════════════════

BEYONDAI_CALIPER_PATHS = CaliperPaths(
    send="/caliper/event",
    validate="/caliper/event/validate",
    list="/caliper/events",
    get="/caliper/events/{id}",
    job_status="/jobs/{id}/status",
)

BEYONDAI_ONEROSTER_PATHS = OneRosterPaths()

BEYONDAI_EDUBRIDGE_PATHS = EdubridgePaths()

BEYONDAI_PATHS = PlatformPaths(
    oneroster=BEYONDAI_ONEROSTER_PATHS,
    edubridge=BEYONDAI_EDUBRIDGE_PATHS,
    caliper=BEYONDAI_CALIPER_PATHS,
)

# ═══════════════════════════════════════════════════════════════════════════════
# LEARNWITHAI PATHS
# ═══════════════════════════════════════════════════════════════════════════════

LEARNWITHAI_CALIPER_PATHS = CaliperPaths(
    send="/events/1.0/",
    validate=None,
    list=None,
    get=None,
    job_status=None,
)

LEARNWITHAI_ONEROSTER_PATHS = OneRosterPaths(
    rostering="/rostering/1.0",
    gradebook="/gradebook/1.0",
    resources="/resources/1.0",
)

# EduBridge not supported on LearnWith.AI
LEARNWITHAI_EDUBRIDGE_PATHS = None

LEARNWITHAI_PATHS = PlatformPaths(
    oneroster=LEARNWITHAI_ONEROSTER_PATHS,
    edubridge=None,  # Not supported on LearnWith.AI
    caliper=LEARNWITHAI_CALIPER_PATHS,
)

# ═══════════════════════════════════════════════════════════════════════════════
# PLATFORM PATH MAP
# ═══════════════════════════════════════════════════════════════════════════════

PLATFORM_CALIPER_PATHS: dict[str, CaliperPaths] = {
    "BEYOND_AI": BEYONDAI_CALIPER_PATHS,
    "LEARNWITH_AI": LEARNWITHAI_CALIPER_PATHS,
}

PLATFORM_ONEROSTER_PATHS: dict[str, OneRosterPaths] = {
    "BEYOND_AI": BEYONDAI_ONEROSTER_PATHS,
    "LEARNWITH_AI": LEARNWITHAI_ONEROSTER_PATHS,
}

PLATFORM_PATHS: dict[str, PlatformPaths] = {
    "BEYOND_AI": BEYONDAI_PATHS,
    "LEARNWITH_AI": LEARNWITHAI_PATHS,
}


__all__ = [
    "BEYONDAI_API_URLS",
    "BEYONDAI_CALIPER_PATHS",
    "BEYONDAI_ONEROSTER_PATHS",
    "BEYONDAI_TOKEN_URLS",
    "DEFAULT_PLATFORM",
    "PLATFORM_CALIPER_PATHS",
    "PLATFORM_ENDPOINTS",
    "CaliperPaths",
    "EdubridgePaths",
    "Environment",
    "OneRosterPaths",
    "Platform",
    "PlatformPaths",
]
