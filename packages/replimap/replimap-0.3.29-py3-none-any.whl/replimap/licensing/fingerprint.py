"""
Multi-factor machine fingerprint generation for RepliMap CLI v4.0.4.

Fingerprint validation levels:
- "none": No validation (COMMUNITY)
- "basic": Basic fingerprint (PRO, TEAM)
- "strict": Multi-factor fingerprint (SOVEREIGN)

The fingerprint is used to:
1. Bind licenses to specific machines
2. Detect environment changes
3. Prevent license abuse (copying licenses across machines)

Environment-aware fingerprinting:
- Normal machines: Hardware-based fingerprint (MAC, hostname, etc.)
- CI environments: Repository-based fingerprint (stable across ephemeral runners)
- Container environments: Volume UUID or workspace ID (stable across rebuilds)
"""

from __future__ import annotations

import hashlib
import logging
import os
import platform
import subprocess
import uuid
from dataclasses import dataclass
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


# ═══════════════════════════════════════════════════════════════════════════
# CONTAINER ENVIRONMENT SUPPORT
# ═══════════════════════════════════════════════════════════════════════════


def is_container_environment() -> bool:
    """
    Detect if running in a container environment.

    Checks for:
    - Docker containers
    - VS Code DevContainers
    - GitHub Codespaces
    - Gitpod workspaces
    - Podman containers
    - Kubernetes pods

    Returns:
        True if running in a container environment
    """
    indicators = [
        Path("/.dockerenv").exists(),  # Docker
        os.environ.get("REMOTE_CONTAINERS") is not None,  # VS Code DevContainer
        os.environ.get("CODESPACES") is not None,  # GitHub Codespaces
        os.environ.get("GITPOD_WORKSPACE_ID") is not None,  # Gitpod
        Path("/run/.containerenv").exists(),  # Podman
        os.environ.get("KUBERNETES_SERVICE_HOST") is not None,  # Kubernetes
    ]
    return any(indicators)


def get_container_type() -> str | None:
    """
    Get the type of container environment.

    Returns:
        Container type string or None if not in container
    """
    if os.environ.get("CODESPACES"):
        return "codespaces"
    if os.environ.get("GITPOD_WORKSPACE_ID"):
        return "gitpod"
    if os.environ.get("REMOTE_CONTAINERS"):
        return "devcontainer"
    if os.environ.get("KUBERNETES_SERVICE_HOST"):
        return "kubernetes"
    if Path("/.dockerenv").exists():
        return "docker"
    if Path("/run/.containerenv").exists():
        return "podman"
    return None


def get_container_fingerprint() -> str:
    """
    Generate a stable fingerprint for container environments.

    Priority:
    1. Persistent volume UUID file (most stable)
    2. Workspace ID (Codespaces/Gitpod)
    3. Fallback to CI-style repo fingerprint

    The fingerprint is prefixed with the source type for debugging.

    Returns:
        A 32-character hex fingerprint
    """
    # Priority 1: Persistent volume UUID
    volume_paths = [
        Path("/workspace/.replimap/.device_id"),  # Common mount point
        Path.home() / ".replimap" / ".device_id",  # Home directory (if persistent)
        Path("/workspaces/.replimap/.device_id"),  # Codespaces mount
    ]

    for path in volume_paths:
        try:
            if path.exists():
                device_id = path.read_text().strip()
                if device_id:
                    logger.debug(f"Container fingerprint from volume: {path}")
                    return _hash_fingerprint(f"volume:{device_id}")
            elif path.parent.exists():
                # Create new device ID in persistent location
                device_id = str(uuid.uuid4())
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text(device_id)
                logger.info(f"Created container device ID: {path}")
                return _hash_fingerprint(f"volume:{device_id}")
        except (OSError, PermissionError) as e:
            logger.debug(f"Could not use volume path {path}: {e}")
            continue

    # Priority 2: Workspace ID (cloud IDEs)
    if workspace_id := os.environ.get("CODESPACE_NAME"):
        logger.debug("Container fingerprint from Codespaces name")
        return _hash_fingerprint(f"codespaces:{workspace_id}")

    if workspace_id := os.environ.get("GITPOD_WORKSPACE_ID"):
        logger.debug("Container fingerprint from Gitpod workspace ID")
        return _hash_fingerprint(f"gitpod:{workspace_id}")

    # Priority 3: Fallback to CI-style fingerprint (repo-based)
    logger.debug("Container fingerprint fallback to CI-style")
    return get_ci_fingerprint()


def _hash_fingerprint(source: str) -> str:
    """Hash a fingerprint source to 32-char hex string."""
    return hashlib.sha256(source.encode()).hexdigest()[:32]


def get_fingerprint_environment() -> dict[str, Any]:
    """
    Get information about the current fingerprint environment.

    Useful for debugging and diagnostics.

    Returns:
        Dictionary with environment details
    """
    # Import here to avoid circular imports
    from replimap.licensing.ci_adapter import detect_ci_environment

    ci_env = detect_ci_environment()

    return {
        "is_ci": is_ci_environment(),
        "is_container": is_container_environment(),
        "container_type": get_container_type(),
        "ci_provider": ci_env.provider if ci_env else None,
        "fingerprint_source": (
            "container"
            if is_container_environment()
            else "ci"
            if is_ci_environment()
            else "machine"
        ),
    }


@dataclass
class FingerprintComponents:
    """Components used to generate a fingerprint."""

    hostname: str
    machine: str  # Architecture
    system: str  # OS
    mac_address: str | None
    cpu_info: str | None
    disk_serial: str | None
    username: str | None

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for inspection."""
        return {
            "hostname": self.hostname,
            "machine": self.machine,
            "system": self.system,
            "mac_address": self.mac_address,
            "cpu_info": self.cpu_info,
            "disk_serial": self.disk_serial,
            "username": self.username,
        }


def get_machine_fingerprint(level: str = "basic") -> str:
    """
    Generate a machine fingerprint at the specified level.

    Environment-aware:
    - Container environments: Use container-stable fingerprint
    - CI environments: Use repo-based fingerprint
    - Normal machines: Use hardware-based fingerprint

    Args:
        level: Validation level ("none", "basic", "strict")

    Returns:
        A 32-character hex fingerprint
    """
    if level == "none":
        # No fingerprint - return a fixed value
        return "0" * 32

    # Container environment takes precedence (DevContainers, Codespaces, etc.)
    if is_container_environment():
        logger.debug(f"Container environment detected: {get_container_type()}")
        return get_container_fingerprint()

    # CI environment
    if is_ci_environment():
        logger.debug("CI environment detected")
        return get_ci_fingerprint()

    # Normal machine environment - hardware-based fingerprint
    components = _collect_components()

    if level == "basic":
        # Basic fingerprint: hostname + machine + system + MAC
        parts = [
            components.hostname,
            components.machine,
            components.system,
        ]
        if components.mac_address:
            parts.append(components.mac_address)

    else:  # strict
        # Strict fingerprint: all available components
        parts = [
            components.hostname,
            components.machine,
            components.system,
        ]
        if components.mac_address:
            parts.append(components.mac_address)
        if components.cpu_info:
            parts.append(components.cpu_info)
        if components.disk_serial:
            parts.append(components.disk_serial)

    fingerprint_string = "|".join(parts)
    return hashlib.sha256(fingerprint_string.encode()).hexdigest()[:32]


def get_ci_fingerprint() -> str:
    """
    Generate a fingerprint suitable for CI/CD environments.

    CI environments have ephemeral machines, so we use
    repository-based identification instead.

    Returns:
        A 32-character hex fingerprint based on repo info
    """
    # Collect CI-specific identifiers
    parts = []

    # GitHub Actions
    if os.environ.get("GITHUB_REPOSITORY"):
        parts.append(f"github:{os.environ['GITHUB_REPOSITORY']}")

    # GitLab CI
    elif os.environ.get("CI_PROJECT_PATH"):
        parts.append(f"gitlab:{os.environ['CI_PROJECT_PATH']}")

    # CircleCI
    elif os.environ.get("CIRCLE_PROJECT_REPONAME"):
        parts.append(f"circleci:{os.environ['CIRCLE_PROJECT_REPONAME']}")

    # Jenkins
    elif os.environ.get("JOB_NAME"):
        parts.append(f"jenkins:{os.environ['JOB_NAME']}")

    # Azure DevOps
    elif os.environ.get("BUILD_REPOSITORY_NAME"):
        parts.append(f"azure:{os.environ['BUILD_REPOSITORY_NAME']}")

    # Bitbucket Pipelines
    elif os.environ.get("BITBUCKET_REPO_SLUG"):
        parts.append(f"bitbucket:{os.environ['BITBUCKET_REPO_SLUG']}")

    # AWS CodeBuild
    elif os.environ.get("CODEBUILD_SOURCE_REPO_URL"):
        parts.append(f"codebuild:{os.environ['CODEBUILD_SOURCE_REPO_URL']}")

    # Generic CI
    if os.environ.get("CI"):
        parts.append("ci:true")

    # If no CI identifiers found, fall back to basic fingerprint
    if not parts:
        return get_machine_fingerprint("basic")

    fingerprint_string = "|".join(parts)
    return hashlib.sha256(fingerprint_string.encode()).hexdigest()[:32]


def is_ci_environment() -> bool:
    """
    Detect if running in a CI/CD environment.

    Returns:
        True if running in CI
    """
    ci_indicators = [
        "CI",
        "CONTINUOUS_INTEGRATION",
        "GITHUB_ACTIONS",
        "GITLAB_CI",
        "CIRCLECI",
        "JENKINS_URL",
        "TRAVIS",
        "BUILDKITE",
        "AZURE_HTTP_USER_AGENT",
        "TEAMCITY_VERSION",
        "BITBUCKET_COMMIT",
        "CODEBUILD_BUILD_ID",
    ]
    return any(os.environ.get(var) for var in ci_indicators)


def _collect_components() -> FingerprintComponents:
    """Collect all fingerprint components."""
    return FingerprintComponents(
        hostname=platform.node(),
        machine=platform.machine(),
        system=platform.system(),
        mac_address=_get_mac_address(),
        cpu_info=_get_cpu_info(),
        disk_serial=_get_disk_serial(),
        username=_get_username(),
    )


def _get_mac_address() -> str | None:
    """Get the primary MAC address."""
    try:
        mac = uuid.getnode()
        # Check if MAC is stable (not random)
        if mac == uuid.getnode():
            return str(mac)
    except OSError:
        pass
    return None


def _get_cpu_info() -> str | None:
    """Get CPU information."""
    try:
        if platform.system() == "Linux":
            with open("/proc/cpuinfo") as f:
                for line in f:
                    if line.startswith("model name"):
                        return line.split(":")[1].strip()
        elif platform.system() == "Darwin":  # macOS
            result = subprocess.run(
                ["sysctl", "-n", "machdep.cpu.brand_string"],
                capture_output=True,
                text=True,
                timeout=5,
            )
            if result.returncode == 0:
                return result.stdout.strip()
        elif platform.system() == "Windows":
            import winreg

            key = winreg.OpenKey(
                winreg.HKEY_LOCAL_MACHINE,
                r"HARDWARE\DESCRIPTION\System\CentralProcessor\0",
            )
            return winreg.QueryValueEx(key, "ProcessorNameString")[0]
    except Exception as e:
        logger.debug(f"Failed to get CPU info: {e}")
    return None


def _get_disk_serial() -> str | None:
    """Get the primary disk serial number."""
    try:
        if platform.system() == "Linux":
            result = subprocess.run(
                ["lsblk", "-o", "SERIAL", "-n", "-d"],
                capture_output=True,
                text=True,
                timeout=5,
            )
            if result.returncode == 0:
                serials = result.stdout.strip().split("\n")
                if serials and serials[0]:
                    return serials[0].strip()
        elif platform.system() == "Darwin":  # macOS
            result = subprocess.run(
                ["ioreg", "-l"],
                capture_output=True,
                text=True,
                timeout=5,
            )
            if result.returncode == 0:
                for line in result.stdout.split("\n"):
                    if "IOPlatformSerialNumber" in line:
                        parts = line.split("=")
                        if len(parts) > 1:
                            return parts[1].strip().strip('"')
        elif platform.system() == "Windows":
            result = subprocess.run(
                ["wmic", "diskdrive", "get", "serialnumber"],
                capture_output=True,
                text=True,
                timeout=5,
            )
            if result.returncode == 0:
                lines = result.stdout.strip().split("\n")
                if len(lines) > 1:
                    return lines[1].strip()
    except Exception as e:
        logger.debug(f"Failed to get disk serial: {e}")
    return None


def _get_username() -> str | None:
    """Get the current username."""
    try:
        return os.getlogin()
    except OSError:
        try:
            import pwd

            return pwd.getpwuid(os.getuid()).pw_name
        except (ImportError, KeyError):
            pass
    return os.environ.get("USER") or os.environ.get("USERNAME")


def validate_fingerprint(
    stored_fingerprint: str,
    level: str = "basic",
) -> tuple[bool, str]:
    """
    Validate the current machine against a stored fingerprint.

    Environment-aware validation:
    - Container environments: Compare container fingerprints
    - CI environments: Compare repo-based fingerprints
    - Normal machines: Compare hardware fingerprints

    Args:
        stored_fingerprint: The fingerprint to validate against
        level: Validation level

    Returns:
        Tuple of (is_valid, message)
    """
    if level == "none":
        return True, "Fingerprint validation disabled"

    # Container environment has highest priority
    if is_container_environment():
        current = get_container_fingerprint()
        env_type = "container"
    # CI environment
    elif is_ci_environment():
        current = get_ci_fingerprint()
        env_type = "CI"
    else:
        current = get_machine_fingerprint(level)
        env_type = "machine"

    if current == stored_fingerprint:
        return True, f"{env_type.title()} fingerprint matches"

    return (
        False,
        f"{env_type.title()} fingerprint mismatch - license may be bound to another {env_type}",
    )


def get_fingerprint_debug_info() -> dict[str, Any]:
    """
    Get debug information about fingerprint components.

    Useful for troubleshooting fingerprint mismatches.
    """
    components = _collect_components()
    env_info = get_fingerprint_environment()

    result = {
        "components": components.to_dict(),
        "environment": env_info,
        "current_fingerprint": get_machine_fingerprint("basic"),
        "basic_fingerprint": get_machine_fingerprint("basic"),
        "strict_fingerprint": get_machine_fingerprint("strict"),
        "is_ci": is_ci_environment(),
        "is_container": is_container_environment(),
    }

    if is_ci_environment():
        result["ci_fingerprint"] = get_ci_fingerprint()

    if is_container_environment():
        result["container_type"] = get_container_type()
        result["container_fingerprint"] = get_container_fingerprint()

    return result
