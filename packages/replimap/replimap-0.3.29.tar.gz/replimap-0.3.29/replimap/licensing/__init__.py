"""
RepliMap Licensing Module - Public API.

Provides license validation, feature gating, and usage tracking
for the commercial tiers of RepliMap.

Gate Philosophy: Gate at OUTPUT, not at SCAN.
- Users experience full value first (unlimited scanning)
- Gating happens at export/download time

Core Principles:
- SCAN: Unlimited resources, frequency limited only
- GRAPH: Full viewing free, watermark on export
- CLONE: Full generation, download is paid
- AUDIT: Full scan, detailed findings are paid
- DRIFT: Fully paid feature

Security Note:
- Only high-level APIs are exported
- Internal implementation details (cache, verifier, crypto) are intentionally hidden
- This prevents external code from bypassing security checks
"""

# ═══════════════════════════════════════════════════════════════════════════
# HIGH-LEVEL API (Safe to use externally)
# ═══════════════════════════════════════════════════════════════════════════

# CI Detection - Safe to expose (read-only)
from replimap.licensing.ci_adapter import (
    CIEnvironment,
    detect_ci_environment,
    is_ci_environment,
)

# Feature Gating - Decorators and checks
from replimap.licensing.gates import (
    GateResult,
    check_audit_ci_mode_allowed,
    check_audit_export_allowed,
    check_audit_fix_allowed,
    check_blast_allowed,  # Deprecated: use check_deps_allowed
    check_clone_download_allowed,
    check_cost_allowed,
    check_deps_allowed,
    check_drift_allowed,
    check_drift_watch_allowed,
    check_graph_export_watermark,
    check_multi_account_allowed,
    check_output_format_allowed,
    check_scan_allowed,
    feature_gate,
    format_audit_findings,
    format_clone_output,
    get_audit_visible_findings,
    get_clone_preview_lines,
    get_scans_remaining,
    require_plan,
)

# Legacy License Manager (for backward compatibility)
from replimap.licensing.manager import LicenseManager, is_dev_mode

# Models - Data types for external use
from replimap.licensing.models import (
    Feature,
    License,
    LicenseStatus,
    LicenseValidationError,
    Plan,
    PlanFeatures,
    get_plan_features,
    get_plan_for_limit,
    get_upgrade_target,
    has_feature,
)

# Prompts - User-facing messages
from replimap.licensing.prompts import (
    format_audit_limited_prompt,
    format_clone_blocked_prompt,
    format_clone_preview_footer,
    format_multi_account_prompt,
    format_scan_limit_prompt,
    get_upgrade_prompt,
)

# Secure License Manager - Main entry point for v2 licensing
from replimap.licensing.secure_manager import (
    SecureLicenseError,
    SecureLicenseManager,
    get_secure_license_manager,
)

# Usage tracking
from replimap.licensing.tracker import UsageTracker

# ═══════════════════════════════════════════════════════════════════════════
# INTERNAL ONLY - DO NOT EXPORT (Security best practice)
# ═══════════════════════════════════════════════════════════════════════════
#
# The following are intentionally NOT exported to prevent bypass attacks:
# - LocalLeaseCache (cache.py) - Cache implementation details
# - LicenseVerifier (verifier.py) - Cryptographic internals
# - KeyRegistry (crypto/keys.py) - Key management internals
# - RateLimiter (secure_manager.py) - Rate limiting internals
# - get_machine_fingerprint (fingerprint.py) - Fingerprint generation details
#
# External code should use the high-level API:
# - get_secure_license_manager() for license operations
# - feature_gate() and require_plan() for access control
# - detect_ci_environment() for CI detection
# ═══════════════════════════════════════════════════════════════════════════

__all__ = [
    # Core models
    "Feature",
    "License",
    "LicenseManager",
    "LicenseStatus",
    "LicenseValidationError",
    "Plan",
    "PlanFeatures",
    "UsageTracker",
    # Secure License Manager (v2)
    "SecureLicenseManager",
    "SecureLicenseError",
    "get_secure_license_manager",
    # Gate result
    "GateResult",
    # Gate checks
    "check_audit_ci_mode_allowed",
    "check_audit_export_allowed",
    "check_audit_fix_allowed",
    "check_blast_allowed",  # Deprecated: use check_deps_allowed
    "check_clone_download_allowed",
    "check_cost_allowed",
    "check_deps_allowed",
    "check_drift_allowed",
    "check_drift_watch_allowed",
    "check_graph_export_watermark",
    "check_multi_account_allowed",
    "check_output_format_allowed",
    "check_scan_allowed",
    # Gate formatters
    "format_audit_findings",
    "format_clone_output",
    "get_audit_visible_findings",
    "get_clone_preview_lines",
    "get_scans_remaining",
    # Decorators
    "feature_gate",
    "require_plan",
    # Helpers
    "get_plan_features",
    "get_plan_for_limit",
    "get_upgrade_target",
    "has_feature",
    "is_dev_mode",
    # Prompts
    "get_upgrade_prompt",
    "format_audit_limited_prompt",
    "format_clone_blocked_prompt",
    "format_clone_preview_footer",
    "format_multi_account_prompt",
    "format_scan_limit_prompt",
    # CI Detection (read-only, safe)
    "CIEnvironment",
    "detect_ci_environment",
    "is_ci_environment",
]
