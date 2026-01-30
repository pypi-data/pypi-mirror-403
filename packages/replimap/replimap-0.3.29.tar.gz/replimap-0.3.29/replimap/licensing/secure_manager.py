"""
Secure License Manager for RepliMap.

Security Changes from original manager.py:
- REMOVED: is_dev_mode() environment variable bypass
- ADDED: Ed25519 signature verification
- ADDED: Time validation
- ADDED: Proper error handling and logging
- ADDED: Local lease cache with tamper protection
- ADDED: Grace period for offline usage
- ADDED: Rate limiting for force refresh

All license data comes from verified signatures only.
No local-only validation that can be bypassed.
"""

from __future__ import annotations

import logging
import os
import platform
import sqlite3
import sys
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import TYPE_CHECKING, Any

import httpx

from replimap.licensing.cache import LocalLeaseCache
from replimap.licensing.models import Feature, Plan, get_plan_features
from replimap.licensing.secure_models import (
    SECURE_PLAN_FEATURES,
    SECURE_PLAN_LIMITS,
    SecureLicenseData,
    SecureLicenseLimits,
)
from replimap.licensing.verifier import (
    LicenseExpiredError,
    LicenseVerificationError,
    LicenseVerifier,
)

if TYPE_CHECKING:
    from replimap.licensing.models import PlanFeatures

logger = logging.getLogger(__name__)

UTC = UTC


class SecureLicenseError(Exception):
    """Secure license operation error."""

    pass


# ═══════════════════════════════════════════════════════════════════════════
# RATE LIMITER
# ═══════════════════════════════════════════════════════════════════════════


class RateLimiter:
    """
    Simple rate limiter using SQLite for persistence.

    Tracks action counts within sliding time windows.

    Usage:
        limiter = RateLimiter()

        allowed, remaining = limiter.check_and_increment(
            action="force_refresh",
            max_count=10,
            window_seconds=3600
        )

        if not allowed:
            raise RateLimitError("Too many requests")
    """

    DB_FILE = Path.home() / ".replimap" / "rate_limits.db"

    def __init__(self, db_file: Path | None = None):
        """
        Initialize rate limiter.

        Args:
            db_file: Custom database file path (for testing)
        """
        self.db_file = db_file or self.DB_FILE
        self._init_db()

    def _init_db(self) -> None:
        """Initialize database schema."""
        try:
            self.db_file.parent.mkdir(parents=True, exist_ok=True)
            conn = sqlite3.connect(str(self.db_file))
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS rate_limits (
                    action TEXT PRIMARY KEY,
                    count INTEGER DEFAULT 0,
                    window_start TEXT NOT NULL
                )
            """
            )
            conn.commit()
            conn.close()
        except (sqlite3.Error, OSError) as e:
            logger.warning(f"Could not initialize rate limiter DB: {e}")

    def check_and_increment(
        self,
        action: str,
        max_count: int,
        window_seconds: int,
    ) -> tuple[bool, int]:
        """
        Check rate limit and increment counter if allowed.

        Args:
            action: Action identifier (e.g., "force_refresh")
            max_count: Maximum allowed calls in window
            window_seconds: Window size in seconds

        Returns:
            Tuple of (allowed, remaining_count)
            - allowed: True if action is permitted
            - remaining_count: Number of calls remaining in window
        """
        try:
            conn = sqlite3.connect(str(self.db_file))
            cursor = conn.cursor()

            now = datetime.now(UTC)
            window_start_threshold = now - timedelta(seconds=window_seconds)

            cursor.execute(
                "SELECT count, window_start FROM rate_limits WHERE action = ?",
                (action,),
            )
            row = cursor.fetchone()

            if row is None:
                # First call ever
                cursor.execute(
                    "INSERT INTO rate_limits (action, count, window_start) VALUES (?, 1, ?)",
                    (action, now.isoformat()),
                )
                conn.commit()
                conn.close()
                return True, max_count - 1

            count, window_start_str = row
            window_start = datetime.fromisoformat(window_start_str)

            # Ensure timezone awareness
            if window_start.tzinfo is None:
                window_start = window_start.replace(tzinfo=UTC)

            if window_start < window_start_threshold:
                # Window expired, reset counter
                cursor.execute(
                    "UPDATE rate_limits SET count = 1, window_start = ? WHERE action = ?",
                    (now.isoformat(), action),
                )
                conn.commit()
                conn.close()
                return True, max_count - 1

            if count >= max_count:
                # Rate limited
                conn.close()
                return False, 0

            # Increment counter
            cursor.execute(
                "UPDATE rate_limits SET count = count + 1 WHERE action = ?",
                (action,),
            )
            conn.commit()
            conn.close()
            return True, max_count - count - 1

        except (sqlite3.Error, OSError) as e:
            logger.warning(f"Rate limiter error: {e}")
            # Fail open - allow the action if we can't check
            return True, max_count

    def reset(self, action: str) -> None:
        """Reset counter for an action (for testing)."""
        try:
            conn = sqlite3.connect(str(self.db_file))
            conn.execute("DELETE FROM rate_limits WHERE action = ?", (action,))
            conn.commit()
            conn.close()
        except (sqlite3.Error, OSError):
            pass


class SecureLicenseManager:
    """
    Manages license activation, verification, and feature access.

    Usage:
        manager = SecureLicenseManager()

        # Check current plan
        plan = manager.current_plan

        # Check feature access
        if manager.has_feature(Feature.AUDIT_EXPORT_PDF):
            export_pdf()

        # Activate license
        license_data = manager.activate("RM-PRO1-2345-6789-ABCD")

        # Force refresh (rate limited)
        success, message = manager.force_refresh()

        # Deactivate
        manager.deactivate()

    Security Model:
        - License comes from server (signed blob)
        - Verification uses Ed25519 (public key only)
        - No environment variable bypasses
        - Time validation prevents manipulation
        - Local cache with tamper protection
        - Grace period for offline usage

    Multi-Layer Defense:
        1. time_validator.py: Detects clock rollback > 24h
        2. cache.py: Detects "future" write timestamps
        3. verifier.py: Validates license expiration
    """

    LICENSE_FILE = Path.home() / ".replimap" / "license.key"
    GRACE_FILE = Path.home() / ".replimap" / ".last_online_validation"
    API_BASE_URL = "https://api.replimap.io/v1"
    API_TIMEOUT = 30.0

    # In-memory cache settings (short-lived)
    CACHE_DURATION = timedelta(minutes=5)

    # Rate limiting for force refresh
    FORCE_REFRESH_LIMIT = 10  # Max calls per hour
    FORCE_REFRESH_WINDOW = 3600  # 1 hour in seconds

    def __init__(
        self,
        license_file: Path | None = None,
        api_base_url: str | None = None,
        verifier: LicenseVerifier | None = None,
        cache: LocalLeaseCache | None = None,
    ) -> None:
        """
        Initialize license manager.

        Args:
            license_file: Custom license file path (for testing)
            api_base_url: Custom API URL (for testing)
            verifier: Custom verifier (for testing)
            cache: Custom cache (for testing)
        """
        self.license_file = license_file or self.LICENSE_FILE
        self.api_base_url = api_base_url or os.environ.get(
            "REPLIMAP_LICENSE_API", self.API_BASE_URL
        )
        self._verifier = verifier or LicenseVerifier()
        self._cache = cache or LocalLeaseCache()
        self._rate_limiter = RateLimiter()

        # In-memory cache (short-lived, for within-session performance)
        self._cached_license: SecureLicenseData | None = None
        self._cache_time: datetime | None = None

        # Grace period tracking
        self._grace_file = self.GRACE_FILE

    # ═══════════════════════════════════════════════════════════════════════
    # PUBLIC API
    # ═══════════════════════════════════════════════════════════════════════

    @property
    def current_plan(self) -> Plan:
        """
        Get current subscription plan.

        Returns FREE if:
        - No license file
        - License invalid or expired
        - Verification fails

        SECURITY: No environment variable bypasses.
        """
        license_data = self._get_verified_license()

        if license_data is None:
            return Plan.COMMUNITY

        return license_data.plan

    @property
    def current_license(self) -> SecureLicenseData | None:
        """Get current verified license data, or None."""
        return self._get_verified_license()

    @property
    def current_features(self) -> PlanFeatures:
        """Get the features for the current plan (legacy compatibility)."""
        return get_plan_features(self.current_plan)

    def has_feature(self, feature: Feature) -> bool:
        """
        Check if current license grants a feature.

        Args:
            feature: Feature to check

        Returns:
            True if feature is available
        """
        license_data = self._get_verified_license()

        if license_data:
            return license_data.has_feature(feature)

        # Fall back to FREE plan features
        return feature in SECURE_PLAN_FEATURES.get(Plan.COMMUNITY, set())

    def get_limits(self) -> SecureLicenseLimits:
        """Get current license limits."""
        license_data = self._get_verified_license()

        if license_data:
            return license_data.limits

        return SECURE_PLAN_LIMITS.get(Plan.COMMUNITY, SecureLicenseLimits())

    def check_limit(self, limit_name: str, value: int) -> bool:
        """
        Check if a value is within license limits.

        Args:
            limit_name: Name of limit (e.g., 'max_accounts')
            value: Current value to check

        Returns:
            True if within limits
        """
        limits = self.get_limits()
        return limits.check_limit(limit_name, value)

    def activate(self, license_key: str) -> SecureLicenseData:
        """
        Activate a license.

        Contacts server, retrieves signed blob, verifies, and saves.

        Args:
            license_key: License key (e.g., "RM-PRO1-2345-6789-ABCD")

        Returns:
            Verified SecureLicenseData

        Raises:
            SecureLicenseError: Activation failed
        """
        logger.info(f"Activating license: {license_key[:10]}...")

        try:
            response = httpx.post(
                f"{self.api_base_url}/license/activate",
                json={
                    "license_key": license_key.upper().strip(),
                    "machine_info": self._get_machine_info(),
                    "cli_version": self._get_cli_version(),
                },
                timeout=self.API_TIMEOUT,
            )

            if response.status_code == 200:
                data = response.json()
                license_blob = data.get("license_blob")

                if not license_blob:
                    raise SecureLicenseError("Server response missing license_blob")

                # Verify the blob before saving
                license_data = self._verifier.verify(license_blob)

                # Save to disk
                self._save_license_blob(license_blob)

                # Update cache
                self._cached_license = license_data
                self._cache_time = datetime.now(UTC)

                logger.info(f"License activated: {license_data.plan.value}")
                return license_data

            elif response.status_code == 400:
                error = response.json().get("error", "Invalid request")
                raise SecureLicenseError(f"Activation failed: {error}")

            elif response.status_code == 401:
                raise SecureLicenseError("Invalid license key")

            elif response.status_code == 403:
                error = response.json().get("error", "License not valid")
                raise SecureLicenseError(f"License rejected: {error}")

            elif response.status_code == 429:
                raise SecureLicenseError("Too many activation attempts. Please wait.")

            else:
                raise SecureLicenseError(
                    f"Activation failed: HTTP {response.status_code}"
                )

        except httpx.RequestError as e:
            raise SecureLicenseError(f"Network error: {e}") from e
        except LicenseVerificationError as e:
            raise SecureLicenseError(f"License verification failed: {e}") from e

    def deactivate(self) -> None:
        """
        Deactivate current license.

        Removes license file and clears cache.
        """
        if self.license_file.exists():
            self.license_file.unlink()
            logger.info("License file removed")

        self._cached_license = None
        self._cache_time = None

        logger.info("License deactivated")

    def refresh(self) -> SecureLicenseData | None:
        """
        Refresh license from server.

        Useful for checking updated limits or features.

        Returns:
            Updated license data, or None if no license
        """
        license_data = self._get_verified_license()

        if license_data is None:
            return None

        # Re-activate with existing key
        try:
            return self.activate(license_data.license_key)
        except SecureLicenseError as e:
            logger.warning(f"License refresh failed: {e}")
            return license_data

    def status(self) -> dict[str, Any]:
        """
        Get license status summary.

        Returns:
            Status dictionary for display
        """
        license_data = self._get_verified_license()

        if license_data is None:
            return {
                "status": "community",
                "plan": "Community",
                "message": "No license active. Using community tier.",
            }

        days_left = license_data.days_until_expiry()

        status: dict[str, Any] = {
            "status": "active",
            "plan": license_data.plan.value.title(),
            "email": license_data.email,
            "organization": license_data.organization,
            "license_key": self._mask_key(license_data.license_key),
            "expires_at": (
                license_data.expires_at.isoformat()
                if license_data.expires_at
                else "Never"
            ),
            "days_remaining": days_left,
        }

        if days_left is not None and days_left <= 30:
            status["warning"] = f"License expires in {days_left} days"

        return status

    def validate(self) -> tuple[str, str]:
        """
        Validate the current license.

        Returns:
            Tuple of (status, message)
        """
        license_data = self._get_verified_license()

        if license_data is None:
            return "valid", "Using free tier"

        if license_data.is_expired():
            return "expired", f"License expired at {license_data.expires_at}"

        return "valid", f"{license_data.plan.value} plan active"

    def force_refresh(self) -> tuple[bool, str]:
        """
        Force refresh license, bypassing cache.

        Rate limited: max 10 calls/hour to prevent API abuse.

        Returns:
            Tuple of (success, message)
        """
        # Check rate limit
        allowed, remaining = self._rate_limiter.check_and_increment(
            "force_refresh",
            self.FORCE_REFRESH_LIMIT,
            self.FORCE_REFRESH_WINDOW,
        )

        if not allowed:
            return False, (
                "Rate limit exceeded for force refresh. "
                f"Please try again in up to {self.FORCE_REFRESH_WINDOW // 60} minutes."
            )

        # Invalidate all caches
        self._cache.invalidate()
        self._cached_license = None
        self._cache_time = None

        # Re-validate online
        try:
            license_data = self._validate_online()
            if license_data:
                self._record_online_validation()
                return (
                    True,
                    f"License refreshed successfully. {remaining} refreshes remaining this hour.",
                )
            else:
                return False, "License validation failed."
        except SecureLicenseError as e:
            return False, f"Refresh failed: {e}"

    # ═══════════════════════════════════════════════════════════════════════
    # GRACE PERIOD SUPPORT
    # ═══════════════════════════════════════════════════════════════════════

    def _record_online_validation(self) -> None:
        """Record successful online validation timestamp for grace period."""
        try:
            self._grace_file.parent.mkdir(parents=True, exist_ok=True)
            self._grace_file.write_text(datetime.now(UTC).isoformat())
            logger.debug("Recorded online validation timestamp")
        except OSError as e:
            logger.warning(f"Could not record validation timestamp: {e}")

    def _get_last_online_validation(self) -> datetime | None:
        """Get timestamp of last successful online validation."""
        if not self._grace_file.exists():
            return None

        try:
            timestamp_str = self._grace_file.read_text().strip()
            timestamp = datetime.fromisoformat(timestamp_str)
            # Ensure timezone awareness
            if timestamp.tzinfo is None:
                timestamp = timestamp.replace(tzinfo=UTC)
            return timestamp
        except (ValueError, OSError) as e:
            logger.warning(f"Could not read validation timestamp: {e}")
            return None

    def _is_within_grace_period(self, grace_days: int) -> bool:
        """
        Check if within offline grace period.

        Args:
            grace_days: Number of grace days allowed (from license limits)

        Returns:
            True if within grace period, False otherwise
        """
        if grace_days <= 0:
            return False

        last_validation = self._get_last_online_validation()
        if last_validation is None:
            return False

        grace_deadline = last_validation + timedelta(days=grace_days)
        now = datetime.now(UTC)

        if now < grace_deadline:
            remaining = (grace_deadline - now).days
            logger.info(f"Within grace period ({remaining} days remaining)")
            return True

        return False

    def _get_grace_remaining_days(self, grace_days: int) -> int:
        """Get remaining days in grace period."""
        last_validation = self._get_last_online_validation()
        if last_validation is None:
            return 0

        grace_deadline = last_validation + timedelta(days=grace_days)
        now = datetime.now(UTC)
        remaining = (grace_deadline - now).days
        return max(0, remaining)

    def _show_grace_period_warning(self, remaining_days: int) -> None:
        """
        Display user-friendly warning about grace period status.

        This is critical for user experience - users should know they're
        in a degraded state and need to reconnect soon.
        """
        try:
            from rich.console import Console

            console = Console(stderr=True)

            if remaining_days <= 1:
                # Urgent warning
                console.print(
                    f"[bold red]Warning: Offline mode expires in {remaining_days} day(s)![/bold red]\n"
                    "[yellow]Please connect to the internet to verify your license.[/yellow]",
                )
            elif remaining_days <= 3:
                # Warning
                console.print(
                    f"[yellow]Warning: Running in Offline Mode. "
                    f"Please verify your license within {remaining_days} days.[/yellow]",
                )
            else:
                # Info
                console.print(
                    f"[dim]Info: Offline mode: {remaining_days} days remaining until verification required.[/dim]",
                )

        except ImportError:
            # Fallback if rich not available - use sys.stderr.write
            if remaining_days <= 1:
                sys.stderr.write(
                    f"Warning: Offline mode expires in {remaining_days} day(s)! "
                    "Please connect to the internet to verify your license.\n"
                )
            elif remaining_days <= 3:
                sys.stderr.write(
                    f"Warning: Running in Offline Mode. "
                    f"Please verify your license within {remaining_days} days.\n"
                )
            else:
                sys.stderr.write(
                    f"Info: Offline mode: {remaining_days} days remaining until verification required.\n"
                )

    # ═══════════════════════════════════════════════════════════════════════
    # INTERNAL METHODS
    # ═══════════════════════════════════════════════════════════════════════

    def _get_verified_license(self) -> SecureLicenseData | None:
        """
        Get verified license data with cache and grace period support.

        Flow:
        1. Check in-memory cache (fastest)
        2. Check local file cache (with signature verification)
        3. Try online validation
        4. Fall back to grace period if offline (with user warning)

        Returns:
            SecureLicenseData if valid license, None otherwise
        """
        # Step 1: In-memory cache (within session)
        if self._is_cache_valid():
            return self._cached_license

        # Step 2: Local file cache (persistent, with signature verification)
        cache_result = self._cache.get()
        if cache_result:
            blob, metadata = cache_result
            try:
                # Verify signature (tamper protection)
                license_data = self._verifier.verify(blob)

                # Check if expired
                if license_data.is_expired():
                    logger.debug("Cached license expired")
                    self._cache.invalidate()
                else:
                    # Update in-memory cache
                    self._cached_license = license_data
                    self._cache_time = datetime.now(UTC)
                    return license_data

            except LicenseVerificationError as e:
                logger.warning(f"Cache verification failed: {e}")
                self._cache.invalidate()

        # Step 3: Load from license file and try online validation
        if not self.license_file.exists():
            return None

        try:
            # Try to verify the local license file
            license_blob = self.license_file.read_text().strip()
            license_data = self._verifier.verify(license_blob)

            # License is valid locally, try to update from server
            try:
                online_data = self._validate_online()
                if online_data:
                    self._record_online_validation()
                    self._cached_license = online_data
                    self._cache_time = datetime.now(UTC)
                    return online_data
            except SecureLicenseError as e:
                # Online validation failed, use local data with grace period
                logger.warning(f"Online validation failed: {e}")

                grace_days = license_data.limits.offline_grace_days
                if self._is_within_grace_period(grace_days):
                    remaining_days = self._get_grace_remaining_days(grace_days)

                    # Show warning to user
                    self._show_grace_period_warning(remaining_days)

                    # Use local license data
                    self._cached_license = license_data
                    self._cache_time = datetime.now(UTC)
                    return license_data
                else:
                    logger.warning("Grace period expired, online validation required")
                    return None

            # No online validation needed or succeeded
            self._cached_license = license_data
            self._cache_time = datetime.now(UTC)
            return license_data

        except LicenseExpiredError:
            logger.info("License has expired")
            return None
        except LicenseVerificationError as e:
            logger.warning(f"License verification failed: {e}")
            return None

    def _validate_online(self) -> SecureLicenseData | None:
        """
        Validate license with online API.

        Returns:
            SecureLicenseData if valid, None otherwise

        Raises:
            SecureLicenseError: Network or validation error
        """
        # Read stored license key from license file
        if not self.license_file.exists():
            return None

        try:
            license_blob = self.license_file.read_text().strip()
            # Parse the blob to get the license key for activation
            license_data = self._verifier.verify(license_blob)
            license_key = license_data.license_key
        except (OSError, LicenseVerificationError):
            return None

        if not license_key:
            return None

        # Get machine fingerprint
        from replimap.licensing.fingerprint import get_machine_fingerprint

        fingerprint = get_machine_fingerprint()

        # Call API
        try:
            response = httpx.post(
                f"{self.api_base_url}/license/activate",
                json={
                    "license_key": license_key,
                    "machine_fingerprint": fingerprint,
                    "machine_info": self._get_machine_info(),
                    "cli_version": self._get_cli_version(),
                },
                timeout=self.API_TIMEOUT,
            )

            if response.status_code == 200:
                data = response.json()
                blob = data.get("license_blob")

                if blob:
                    # Verify and parse
                    new_license_data = self._verifier.verify(blob)

                    # Cache the blob
                    self._cache.set(blob, new_license_data.plan.value)

                    # Also update the license file with fresh blob
                    self._save_license_blob(blob)

                    return new_license_data

            elif response.status_code >= 400:
                error = response.json().get("error", "Validation failed")
                raise SecureLicenseError(f"Server rejected license: {error}")

        except httpx.RequestError as e:
            raise SecureLicenseError(f"Network error: {e}") from e

        return None

    def _is_cache_valid(self) -> bool:
        """Check if in-memory cache is still valid."""
        if self._cached_license is None or self._cache_time is None:
            return False

        age = datetime.now(UTC) - self._cache_time
        if age > self.CACHE_DURATION:
            return False

        # Also check expiration
        if self._cached_license.is_expired():
            return False

        return True

    def _save_license_blob(self, blob: str) -> None:
        """Save license blob to disk."""
        self.license_file.parent.mkdir(parents=True, exist_ok=True)
        self.license_file.write_text(blob)

        # Secure permissions (owner read/write only)
        try:
            os.chmod(self.license_file, 0o600)
        except OSError:
            pass  # Windows may not support

    def _get_machine_info(self) -> dict[str, str]:
        """Get machine info for activation request."""
        return {
            "platform": platform.system(),
            "platform_version": platform.version(),
            "platform_release": platform.release(),
            "python_version": platform.python_version(),
            "hostname": platform.node(),
            "machine": platform.machine(),
        }

    def _get_cli_version(self) -> str:
        """Get CLI version."""
        try:
            from replimap import __version__

            return __version__
        except ImportError:
            return "unknown"

    @staticmethod
    def _mask_key(key: str) -> str:
        """Mask license key for display."""
        if len(key) <= 8:
            return "*" * len(key)
        return key[:4] + "*" * (len(key) - 8) + key[-4:]


# ═══════════════════════════════════════════════════════════════════════════
# SINGLETON INSTANCE
# ═══════════════════════════════════════════════════════════════════════════

_secure_license_manager: SecureLicenseManager | None = None


def get_secure_license_manager() -> SecureLicenseManager:
    """Get singleton SecureLicenseManager instance."""
    global _secure_license_manager
    if _secure_license_manager is None:
        _secure_license_manager = SecureLicenseManager()
    return _secure_license_manager


def set_secure_license_manager(manager: SecureLicenseManager) -> None:
    """Set the global secure license manager instance (for testing)."""
    global _secure_license_manager
    _secure_license_manager = manager


def require_feature(feature: Feature):
    """
    Decorator to require a feature for a function.

    Usage:
        @require_feature(Feature.AUDIT_EXPORT_PDF)
        def export_pdf():
            ...
    """

    def decorator(func):
        def wrapper(*args, **kwargs):
            manager = get_secure_license_manager()
            if not manager.has_feature(feature):
                plan = manager.current_plan
                raise SecureLicenseError(
                    f"Feature '{feature.value}' requires a higher plan. "
                    f"Current plan: {plan.value}"
                )
            return func(*args, **kwargs)

        return wrapper

    return decorator


def require_plan(min_plan: Plan):
    """
    Decorator to require a minimum plan.

    Usage:
        @require_plan(Plan.TEAM)
        def team_only_feature():
            ...
    """
    plan_order = [Plan.COMMUNITY, Plan.PRO, Plan.TEAM, Plan.SOVEREIGN]

    def decorator(func):
        def wrapper(*args, **kwargs):
            manager = get_secure_license_manager()
            current = manager.current_plan

            current_idx = plan_order.index(current)
            required_idx = plan_order.index(min_plan)

            if current_idx < required_idx:
                raise SecureLicenseError(
                    f"This feature requires {min_plan.value} plan or higher. "
                    f"Current plan: {current.value}"
                )
            return func(*args, **kwargs)

        return wrapper

    return decorator
