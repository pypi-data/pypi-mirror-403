"""
Security update check mechanism for RepliMap CLI v4.0.4.

For security/compliance tools, we need a way to notify users
of critical updates, especially SOVEREIGN offline customers.

Methods:
1. DNS TXT record (fastest, privacy-friendly)
2. HTTPS endpoint (more detailed info)
3. Offline: Check during Request File generation
"""

from __future__ import annotations

import json
import logging
import sqlite3
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

from replimap import __version__

logger = logging.getLogger(__name__)

# Configuration
VERSION_DNS_RECORD = "_version.replimap.com"
VERSION_HTTPS_URL = "https://api.replimap.io/v1/version"
CHECK_INTERVAL_HOURS = 24
DEFAULT_CACHE_DIR = Path.home() / ".replimap"


@dataclass
class VersionInfo:
    """Version information from server."""

    min_safe_version: str  # Minimum version without known vulnerabilities
    latest_version: str  # Latest available version
    security_advisory: str | None = None  # CVE or security notice
    advisory_url: str | None = None  # URL for more info
    checked_at: datetime | None = None

    def is_current_safe(self) -> bool:
        """Check if current version is safe."""
        from packaging import version

        try:
            return version.parse(__version__) >= version.parse(self.min_safe_version)
        except Exception:
            # If we can't parse versions, assume safe
            return True

    def is_update_available(self) -> bool:
        """Check if a newer version is available."""
        from packaging import version

        try:
            return version.parse(__version__) < version.parse(self.latest_version)
        except Exception:
            return False

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "min_safe_version": self.min_safe_version,
            "latest_version": self.latest_version,
            "security_advisory": self.security_advisory,
            "advisory_url": self.advisory_url,
            "checked_at": self.checked_at.isoformat() if self.checked_at else None,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> VersionInfo:
        """Create VersionInfo from dictionary."""
        return cls(
            min_safe_version=data["min_safe_version"],
            latest_version=data["latest_version"],
            security_advisory=data.get("security_advisory"),
            advisory_url=data.get("advisory_url"),
            checked_at=(
                datetime.fromisoformat(data["checked_at"])
                if data.get("checked_at")
                else None
            ),
        )


def check_for_updates(force: bool = False) -> VersionInfo | None:
    """
    Check for critical security updates.

    Flow:
    1. Check cache - skip if checked recently
    2. Try DNS TXT record (fastest)
    3. Fallback to HTTPS endpoint
    4. Cache result

    Args:
        force: Bypass cache and check immediately

    Returns:
        VersionInfo if check successful, None otherwise
    """
    # Check cache
    if not force:
        cached = _get_cached_version_info()
        if cached:
            return cached

    # Try DNS first (fastest, privacy-friendly)
    version_info = _check_via_dns()

    # Fallback to HTTPS
    if version_info is None:
        version_info = _check_via_https()

    # Cache result
    if version_info:
        _cache_version_info(version_info)

    return version_info


def _check_via_dns() -> VersionInfo | None:
    """
    Check version via DNS TXT record.

    DNS record format:
    v=1 min=4.0.4 latest=4.0.5 advisory=CVE-2026-XXXX
    """
    try:
        import dns.resolver

        answers = dns.resolver.resolve(VERSION_DNS_RECORD, "TXT")
        for rdata in answers:
            txt = str(rdata).strip('"')
            return _parse_dns_txt(txt)
    except ImportError:
        logger.debug("dnspython not installed, skipping DNS version check")
    except Exception as e:
        logger.debug(f"DNS version check failed: {e}")
    return None


def _parse_dns_txt(txt: str) -> VersionInfo | None:
    """Parse DNS TXT record into VersionInfo."""
    parts = {}
    for part in txt.split():
        if "=" in part:
            key, value = part.split("=", 1)
            parts[key] = value

    if "min" not in parts or "latest" not in parts:
        return None

    return VersionInfo(
        min_safe_version=parts["min"],
        latest_version=parts["latest"],
        security_advisory=parts.get("advisory"),
        advisory_url=parts.get("url"),
        checked_at=datetime.now(UTC),
    )


def _check_via_https() -> VersionInfo | None:
    """
    Check version via HTTPS endpoint.

    JSON format:
    {
        "min_safe_version": "4.0.4",
        "latest_version": "4.0.5",
        "security_advisory": "CVE-2026-XXXX",
        "advisory_url": "https://..."
    }
    """
    try:
        import httpx

        response = httpx.get(VERSION_HTTPS_URL, timeout=5)
        response.raise_for_status()
        data = response.json()

        return VersionInfo(
            min_safe_version=data["min_safe_version"],
            latest_version=data["latest_version"],
            security_advisory=data.get("security_advisory"),
            advisory_url=data.get("advisory_url"),
            checked_at=datetime.now(UTC),
        )
    except Exception as e:
        logger.debug(f"HTTPS version check failed: {e}")
    return None


def _get_db_path() -> Path:
    """Get the path to the version check database."""
    cache_dir = DEFAULT_CACHE_DIR
    cache_dir.mkdir(parents=True, exist_ok=True)
    return cache_dir / "version_check.db"


def _get_db_connection() -> sqlite3.Connection:
    """Get a database connection for version check caching."""
    db_path = _get_db_path()
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row

    # Create table if not exists
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS version_check (
            id INTEGER PRIMARY KEY DEFAULT 1,
            min_safe_version TEXT NOT NULL,
            latest_version TEXT NOT NULL,
            security_advisory TEXT,
            advisory_url TEXT,
            checked_at TEXT NOT NULL
        )
        """
    )
    conn.commit()
    return conn


def _get_cached_version_info() -> VersionInfo | None:
    """Get cached version info if still valid."""
    try:
        conn = _get_db_connection()
        row = conn.execute("SELECT * FROM version_check WHERE id = 1").fetchone()
        conn.close()

        if row is None:
            return None

        checked_at = datetime.fromisoformat(row["checked_at"])
        if datetime.now(UTC) - checked_at > timedelta(hours=CHECK_INTERVAL_HOURS):
            return None

        return VersionInfo(
            min_safe_version=row["min_safe_version"],
            latest_version=row["latest_version"],
            security_advisory=row["security_advisory"],
            advisory_url=row["advisory_url"],
            checked_at=checked_at,
        )
    except Exception as e:
        logger.debug(f"Failed to get cached version info: {e}")
        return None


def _cache_version_info(info: VersionInfo) -> None:
    """Cache version info."""
    try:
        conn = _get_db_connection()
        conn.execute(
            """
            INSERT OR REPLACE INTO version_check
            (id, min_safe_version, latest_version, security_advisory, advisory_url, checked_at)
            VALUES (1, ?, ?, ?, ?, ?)
            """,
            (
                info.min_safe_version,
                info.latest_version,
                info.security_advisory,
                info.advisory_url,
                info.checked_at.isoformat()
                if info.checked_at
                else datetime.now(UTC).isoformat(),
            ),
        )
        conn.commit()
        conn.close()
    except Exception as e:
        logger.debug(f"Failed to cache version info: {e}")


def check_offline_version(request_file: Path) -> VersionInfo:
    """
    Check version for offline (SOVEREIGN) customers.

    When generating offline activation request, embed version check.
    This ensures SOVEREIGN customers are notified of security updates
    even in air-gap environments.

    Args:
        request_file: Path to the offline request file

    Returns:
        VersionInfo with embedded check results
    """
    # For offline customers, we embed the check in the request flow
    # When they upload the request file to the portal, they'll see
    # any security advisories

    request_data = json.loads(request_file.read_text())
    request_data["cli_version"] = __version__
    request_data["version_check_requested"] = True

    request_file.write_text(json.dumps(request_data, indent=2))

    logger.info(f"Version check embedded in offline request: {__version__}")
    return VersionInfo(
        min_safe_version=__version__,  # Will be updated by portal
        latest_version=__version__,
        checked_at=datetime.now(UTC),
    )


def get_current_version() -> str:
    """Get the current CLI version."""
    return __version__


def format_version_banner(version_info: VersionInfo) -> str:
    """
    Format a version status banner for CLI display.

    Returns:
        Formatted banner string or empty string if no banner needed
    """
    if version_info is None:
        return ""

    if not version_info.is_current_safe():
        # CRITICAL: Security update required
        banner = f"""
[bold red]CRITICAL SECURITY UPDATE REQUIRED[/bold red]

Your version: {__version__}
Minimum safe: {version_info.min_safe_version}
"""
        if version_info.security_advisory:
            banner += f"Advisory: {version_info.security_advisory}\n"
        if version_info.advisory_url:
            banner += f"Details: {version_info.advisory_url}\n"
        banner += """
[bold]Please update immediately:[/bold]
  pip install --upgrade replimap
"""
        return banner

    elif version_info.is_update_available():
        # INFO: Update available (non-critical)
        return f"[dim]Update available: {version_info.latest_version} (current: {__version__})[/dim]"

    return ""


def should_show_version_warning() -> bool:
    """
    Check if we should show a version warning.

    Returns True if current version has known security issues.
    """
    version_info = check_for_updates()
    if version_info is None:
        return False
    return not version_info.is_current_safe()
