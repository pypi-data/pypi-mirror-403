"""
Local lease cache with tamper protection.

Security Model:
- Cache stores the ORIGINAL signed license blob from server
- Any modification invalidates the cache (signature verification fails)
- Time monotonicity check prevents clock manipulation attacks
- TTL is client-side optimization; server expiry is authoritative

Multi-Layer Defense:
1. Layer 1: time_validator.py checks global time integrity (>24h rollback blocked)
2. Layer 2: cache.py write_time check (catches "future" cache writes)
3. Layer 3: verifier.py exp check (license expiry is authoritative)

Usage:
    cache = LocalLeaseCache()

    # Write
    cache.set(license_blob, plan="pro")

    # Read (returns None if invalid/expired/tampered)
    result = cache.get()
    if result:
        blob, metadata = result
        # Caller MUST verify blob with LicenseVerifier
"""

from __future__ import annotations

import json
import logging
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    pass

logger = logging.getLogger(__name__)

# TTL by plan tier (seconds)
CACHE_TTL: dict[str, int] = {
    "community": 24 * 60 * 60,  # 24 hours - reduce API pressure for free tier
    "pro": 60 * 60,  # 1 hour - paid users get fresher data
    "team": 60 * 60,  # 1 hour
    "sovereign": 60 * 60,  # 1 hour
}

DEFAULT_TTL = 60 * 60  # 1 hour fallback

# Time drift tolerance for monotonicity check
# Allow up to 5 minutes of clock drift to handle NTP adjustments
TIME_DRIFT_TOLERANCE = timedelta(minutes=5)


class CacheError(Exception):
    """Cache operation error."""

    pass


class CacheTamperedError(CacheError):
    """Cache appears to be tampered with."""

    pass


class CacheTimeAnomalyError(CacheError):
    """System time anomaly detected."""

    pass


class LocalLeaseCache:
    """
    Manages local license lease caching with tamper protection.

    The cache stores:
    - Original signed license blob (tamper-evident via Ed25519)
    - Cache metadata (cached_at, plan for TTL lookup)
    - Write timestamp for time monotonicity check

    Security Properties:
    - Blob is verified by LicenseVerifier before use (caller responsibility)
    - Time monotonicity check detects clock manipulation
    - File modification detected via signature verification failure

    The cache file format is JSON with the following structure:
    {
        "version": 2,
        "blob": "payload.signature",
        "plan": "pro",
        "cached_at": "2025-01-20T10:00:00+00:00",
        "write_time": "2025-01-20T10:00:00+00:00",
        "metadata": { ... optional extra data ... }
    }
    """

    CACHE_FILE = Path.home() / ".replimap" / "license.lease"
    CACHE_VERSION = 2  # Increment when format changes

    def __init__(self, cache_file: Path | None = None) -> None:
        """
        Initialize cache.

        Args:
            cache_file: Custom cache file path (for testing)
        """
        self.cache_file = cache_file or self.CACHE_FILE

    def get(self) -> tuple[str, dict[str, Any]] | None:
        """
        Read cached license blob if valid.

        Returns:
            Tuple of (license_blob, metadata) if cache exists and valid,
            None otherwise.

        Security Notes:
            - Caller MUST verify the blob signature with LicenseVerifier
            - This method only checks TTL and time monotonicity
            - Returns None (not raises) for invalid cache to allow fallback
        """
        if not self.cache_file.exists():
            logger.debug("Cache file does not exist")
            return None

        try:
            data = json.loads(self.cache_file.read_text())

            # Validate cache version
            if data.get("version", 1) != self.CACHE_VERSION:
                logger.info("Cache version mismatch, invalidating")
                self.invalidate()
                return None

            # Check required fields
            required_fields = ["blob", "cached_at", "write_time"]
            if not all(field in data for field in required_fields):
                logger.warning("Cache missing required fields")
                return None

            # Time monotonicity check (anti-clock-manipulation)
            # This is Layer 2 of multi-layer defense
            write_time_str = data["write_time"]
            write_time = datetime.fromisoformat(write_time_str)

            # Ensure timezone awareness
            if write_time.tzinfo is None:
                write_time = write_time.replace(tzinfo=UTC)

            now = datetime.now(UTC)

            # If current time is BEFORE write_time minus tolerance,
            # the clock has been rolled back or cache is from the "future"
            if now < write_time - TIME_DRIFT_TOLERANCE:
                logger.warning(
                    f"Time anomaly detected: now={now.isoformat()}, "
                    f"write_time={write_time.isoformat()}. "
                    "Cache invalidated, requiring online verification."
                )
                self.invalidate()
                return None

            # Check TTL expiry (client-side optimization)
            cached_at_str = data["cached_at"]
            cached_at = datetime.fromisoformat(cached_at_str)

            # Ensure timezone awareness
            if cached_at.tzinfo is None:
                cached_at = cached_at.replace(tzinfo=UTC)

            plan = data.get("plan", "community").lower()
            ttl = CACHE_TTL.get(plan, DEFAULT_TTL)

            age = now.timestamp() - cached_at.timestamp()
            if age > ttl:
                logger.debug(
                    f"Cache expired (age: {age:.0f}s, TTL: {ttl}s, plan: {plan})"
                )
                return None

            if age < 0:
                # cached_at is in the future - another time anomaly
                logger.warning(
                    f"Cache timestamp in future: cached_at={cached_at.isoformat()}, "
                    f"now={now.isoformat()}. Invalidating cache."
                )
                self.invalidate()
                return None

            logger.debug(f"Cache hit (age: {age:.0f}s, TTL: {ttl}s, plan: {plan})")
            return data["blob"], data

        except json.JSONDecodeError as e:
            logger.warning(f"Cache JSON decode error: {e}")
            return None
        except (ValueError, KeyError) as e:
            logger.warning(f"Cache read error: {e}")
            return None
        except OSError as e:
            logger.warning(f"Cache file read error: {e}")
            return None

    def set(
        self,
        license_blob: str,
        plan: str,
        metadata: dict[str, Any] | None = None,
    ) -> bool:
        """
        Cache a license blob.

        The blob should be the original signed blob from the server.
        Do NOT modify the blob before caching - any modification will
        cause signature verification to fail on read.

        Args:
            license_blob: The original signed blob from server
            plan: License plan (for TTL calculation)
            metadata: Optional additional metadata to store

        Returns:
            True if cache was written successfully, False otherwise
        """
        try:
            self.cache_file.parent.mkdir(parents=True, exist_ok=True)

            now = datetime.now(UTC)

            cache_data = {
                "version": self.CACHE_VERSION,
                "blob": license_blob,
                "plan": plan.lower(),
                "cached_at": now.isoformat(),
                "write_time": now.isoformat(),  # For time monotonicity check
            }

            if metadata:
                cache_data["metadata"] = metadata

            # Write atomically to prevent corruption
            temp_file = self.cache_file.with_suffix(".tmp")
            temp_file.write_text(json.dumps(cache_data, indent=2))
            temp_file.replace(self.cache_file)

            logger.debug(f"License cached (plan: {plan})")
            return True

        except OSError as e:
            logger.warning(f"Could not write cache: {e}")
            return False

    def invalidate(self) -> bool:
        """
        Remove cached license.

        Returns:
            True if cache was removed or didn't exist, False on error
        """
        try:
            if self.cache_file.exists():
                self.cache_file.unlink()
                logger.debug("Cache invalidated")
            return True
        except OSError as e:
            logger.warning(f"Could not invalidate cache: {e}")
            return False

    def is_valid(self) -> bool:
        """
        Quick check if cache exists and is not expired.

        Note: Does not verify blob signature.
        """
        return self.get() is not None

    def get_age_seconds(self) -> float | None:
        """Get cache age in seconds, or None if no valid cache."""
        result = self.get()
        if result is None:
            return None

        _, data = result
        cached_at_str = data["cached_at"]
        cached_at = datetime.fromisoformat(cached_at_str)

        # Ensure timezone awareness
        if cached_at.tzinfo is None:
            cached_at = cached_at.replace(tzinfo=UTC)

        return datetime.now(UTC).timestamp() - cached_at.timestamp()

    def get_info(self) -> dict[str, Any] | None:
        """
        Get cache information without returning the blob.

        Useful for diagnostics and status display.

        Returns:
            Dictionary with cache info, or None if no valid cache
        """
        result = self.get()
        if result is None:
            return None

        _, data = result
        age = self.get_age_seconds()

        return {
            "plan": data.get("plan"),
            "cached_at": data.get("cached_at"),
            "age_seconds": age,
            "ttl_remaining": CACHE_TTL.get(data.get("plan", "community"), DEFAULT_TTL)
            - (age or 0),
        }


def get_ttl_for_plan(plan: str) -> int:
    """
    Get cache TTL in seconds for a plan.

    Args:
        plan: Plan name (community, pro, team, sovereign)

    Returns:
        TTL in seconds
    """
    return CACHE_TTL.get(plan.lower(), DEFAULT_TTL)
