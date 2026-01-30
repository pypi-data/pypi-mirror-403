"""
RepliMap Configuration Integrity Checker v3.6.

This module provides critical validation to prevent deployment errors.
It should be called at pipeline startup to catch configuration mistakes
before they cause terraform plan failures.

Based on Gemini's final audit recommendation.

Author: RepliMap Team
Version: 3.6
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from pathlib import Path

logger = logging.getLogger(__name__)


class ConfigIntegrityError(Exception):
    """Raised when critical configuration rules are violated."""


def normalize(name: str) -> str:
    """Normalize field name for comparison."""
    return name.lower().replace("_", "").replace("-", "")


def validate_critical_rules(rules: dict[str, Any]) -> list[str]:
    """
    Final defense: Ensure all critical fixes are applied.

    This function validates that:
    1. vpc_id is NOT ignored in aws_subnet (required field)
    2. targets IS ignored in aws_lb_target_group (parent-child boundary)
    3. matcher transform exists in aws_lb_target_group
    4. no_redact whitelist contains kms_key_id
    5. health_check threshold fields are in aws_lb_target_group.keep whitelist
       (to bypass global .*_count$ filter)

    Returns:
        List of warnings (non-critical issues)

    Raises:
        ConfigIntegrityError: If critical rules are violated
    """
    errors = []
    warnings = []

    resources = rules.get("resources", {})
    global_rules = rules.get("global", {})

    # ═══════════════════════════════════════════════════════════════════════════
    # Critical Check 1: aws_subnet.vpc_id must NOT be ignored
    # ═══════════════════════════════════════════════════════════════════════════
    subnet_config = resources.get("aws_subnet", {})
    subnet_ignores = {normalize(x) for x in subnet_config.get("ignores", [])}

    if "vpcid" in subnet_ignores:
        errors.append(
            "CRITICAL: 'vpc_id' is in aws_subnet.ignores!\n"
            "  This will cause: Error: The argument 'vpc_id' is required\n"
            "  Fix: Remove 'vpc_id' from aws_subnet.ignores in schema_rules.yaml"
        )

    # ═══════════════════════════════════════════════════════════════════════════
    # Critical Check 2: aws_lb_target_group.targets MUST be ignored
    # ═══════════════════════════════════════════════════════════════════════════
    tg_config = resources.get("aws_lb_target_group", {})
    tg_ignores = {normalize(x) for x in tg_config.get("ignores", [])}

    if "targets" not in tg_ignores:
        errors.append(
            "CRITICAL: 'targets' is NOT in aws_lb_target_group.ignores!\n"
            "  This will cause: Error: Blocks of type 'targets' are not expected here\n"
            "  Fix: Add 'targets' to aws_lb_target_group.ignores"
        )

    # ═══════════════════════════════════════════════════════════════════════════
    # Critical Check 3: aws_lb_target_group.matcher transform must exist
    # ═══════════════════════════════════════════════════════════════════════════
    tg_transforms = tg_config.get("transforms", {})
    matcher_transform = None

    for field, transform in tg_transforms.items():
        if normalize(field) == "matcher":
            matcher_transform = transform
            break

    if not matcher_transform:
        errors.append(
            "CRITICAL: 'matcher' transform is missing in aws_lb_target_group!\n"
            "  This will cause: Error: Blocks of type 'matcher' are not expected here\n"
            "  Fix: Add matcher transform with type: flatten_to_string"
        )
    elif isinstance(matcher_transform, dict):
        if matcher_transform.get("type") != "flatten_to_string":
            warnings.append(
                f"WARNING: matcher transform type is '{matcher_transform.get('type')}', "
                f"expected 'flatten_to_string'"
            )

    # ═══════════════════════════════════════════════════════════════════════════
    # Critical Check 4: kms_key_id must be in no_redact whitelist
    # ═══════════════════════════════════════════════════════════════════════════
    global_no_redact = {normalize(x) for x in global_rules.get("no_redact", [])}

    critical_no_redact = ["kmskeyid", "kmsmasterkeyid"]
    missing_no_redact = [x for x in critical_no_redact if x not in global_no_redact]

    if missing_no_redact:
        errors.append(
            f"CRITICAL: Missing fields in global.no_redact: {missing_no_redact}\n"
            "  This will cause: Error: 'kms_key_id' ([REDACTED]) is an invalid ARN\n"
            "  Fix: Add 'kms_key_id' and 'kms_master_key_id' to global.no_redact"
        )

    # ═══════════════════════════════════════════════════════════════════════════
    # Critical Check 5: health_check threshold fields must be in keep whitelist
    # ═══════════════════════════════════════════════════════════════════════════
    # The global .*_count$ pattern would filter out HealthyThresholdCount and
    # UnhealthyThresholdCount if they're not explicitly kept
    tg_keep = {normalize(x) for x in tg_config.get("keep", [])}

    required_keep_fields = ["healthythresholdcount", "unhealthythresholdcount"]
    missing_keep = [x for x in required_keep_fields if x not in tg_keep]

    if missing_keep:
        errors.append(
            f"CRITICAL: Missing fields in aws_lb_target_group.keep: {missing_keep}\n"
            "  Global pattern '.*_count$' filters these needed health_check fields\n"
            "  Fix: Add 'HealthyThresholdCount' and 'UnhealthyThresholdCount' to keep list"
        )

    # ═══════════════════════════════════════════════════════════════════════════
    # Warning Check: health_check transform should have rename_keys
    # ═══════════════════════════════════════════════════════════════════════════
    health_check_transform = None
    for field, transform in tg_transforms.items():
        if normalize(field) == "healthcheck":
            health_check_transform = transform
            break

    if not health_check_transform:
        warnings.append(
            "WARNING: 'health_check' transform missing in aws_lb_target_group.\n"
            "  This may cause: interval_seconds/timeout_seconds field name errors"
        )

    # ═══════════════════════════════════════════════════════════════════════════
    # Report Results
    # ═══════════════════════════════════════════════════════════════════════════
    if errors:
        raise ConfigIntegrityError(
            "\n"
            + "=" * 70
            + "\n"
            + "CONFIGURATION INTEGRITY CHECK FAILED\n"
            + "=" * 70
            + "\n\n"
            + "\n\n".join(errors)
            + "\n\n"
            + "=" * 70
            + "\n"
            + "Fix the above errors before running the pipeline.\n"
            + "=" * 70
        )

    return warnings


def check_config_file(yaml_path: str | Path) -> bool:
    """
    Load and validate a YAML config file.

    Args:
        yaml_path: Path to schema_rules.yaml

    Returns:
        True if validation passes

    Raises:
        ConfigIntegrityError: If critical rules are violated
    """
    import yaml

    logger.info(f"Checking configuration: {yaml_path}")

    with open(yaml_path) as f:
        rules = yaml.safe_load(f)

    warnings = validate_critical_rules(rules)

    if warnings:
        logger.warning("Non-critical warnings:")
        for w in warnings:
            logger.warning(f"  - {w}")

    logger.info("CONFIGURATION INTEGRITY VERIFIED")
    logger.info("  aws_subnet.vpc_id: NOT ignored (required)")
    logger.info("  aws_lb_target_group.targets: ignored (boundary)")
    logger.info("  aws_lb_target_group.matcher: flatten_to_string")
    logger.info("  aws_lb_target_group.keep: threshold fields protected")
    logger.info("  global.no_redact: kms_key_id protected")

    return True


def run_self_tests() -> bool:  # noqa: T201 - print is intentional for CLI output
    """Test the integrity checker itself."""
    print("=" * 70)  # noqa: T201
    print("Configuration Integrity Checker - Self Tests")  # noqa: T201
    print("=" * 70)  # noqa: T201

    all_passed = True

    # Test 1: Valid config should pass
    print("\n[Test 1] Valid configuration")  # noqa: T201
    valid_config = {
        "global": {
            "no_redact": ["kms_key_id", "kms_master_key_id"],
        },
        "resources": {
            "aws_subnet": {
                "ignores": ["subnet_id", "owner_id"],  # vpc_id NOT here
            },
            "aws_lb_target_group": {
                "ignores": ["targets", "load_balancer_arns"],
                "keep": [  # v3.6: Required to bypass global .*_count$ filter
                    "HealthyThresholdCount",
                    "UnhealthyThresholdCount",
                ],
                "transforms": {
                    "matcher": {
                        "type": "flatten_to_string",
                        "extract_field": "HttpCode",
                    },
                    "health_check": {"type": "rename_keys"},
                },
            },
        },
    }

    try:
        validate_critical_rules(valid_config)
        print("  Valid config passed: PASS")  # noqa: T201
    except ConfigIntegrityError as e:
        print(f"  Valid config failed unexpectedly: FAIL\n{e}")  # noqa: T201
        all_passed = False

    # Test 2: vpc_id in ignores should fail
    print("\n[Test 2] Invalid: vpc_id in aws_subnet.ignores")  # noqa: T201
    invalid_vpc_config = {
        "global": {"no_redact": ["kms_key_id", "kms_master_key_id"]},
        "resources": {
            "aws_subnet": {"ignores": ["vpc_id"]},  # WRONG!
            "aws_lb_target_group": {
                "ignores": ["targets"],
                "keep": ["HealthyThresholdCount", "UnhealthyThresholdCount"],
                "transforms": {"matcher": {"type": "flatten_to_string"}},
            },
        },
    }

    try:
        validate_critical_rules(invalid_vpc_config)
        print("  Should have failed but passed: FAIL")  # noqa: T201
        all_passed = False
    except ConfigIntegrityError:
        print("  Correctly detected vpc_id error: PASS")  # noqa: T201

    # Test 3: Missing targets ignore should fail
    print("\n[Test 3] Invalid: targets NOT in aws_lb_target_group.ignores")  # noqa: T201
    invalid_targets_config = {
        "global": {"no_redact": ["kms_key_id", "kms_master_key_id"]},
        "resources": {
            "aws_subnet": {"ignores": ["subnet_id"]},
            "aws_lb_target_group": {
                "ignores": [],  # targets NOT here - WRONG!
                "keep": ["HealthyThresholdCount", "UnhealthyThresholdCount"],
                "transforms": {"matcher": {"type": "flatten_to_string"}},
            },
        },
    }

    try:
        validate_critical_rules(invalid_targets_config)
        print("  Should have failed but passed: FAIL")  # noqa: T201
        all_passed = False
    except ConfigIntegrityError:
        print("  Correctly detected missing targets: PASS")  # noqa: T201

    # Test 4: Missing kms_key_id in no_redact should fail
    print("\n[Test 4] Invalid: kms_key_id NOT in global.no_redact")  # noqa: T201
    invalid_kms_config = {
        "global": {"no_redact": []},  # kms_key_id NOT here - WRONG!
        "resources": {
            "aws_subnet": {"ignores": ["subnet_id"]},
            "aws_lb_target_group": {
                "ignores": ["targets"],
                "keep": ["HealthyThresholdCount", "UnhealthyThresholdCount"],
                "transforms": {"matcher": {"type": "flatten_to_string"}},
            },
        },
    }

    try:
        validate_critical_rules(invalid_kms_config)
        print("  Should have failed but passed: FAIL")  # noqa: T201
        all_passed = False
    except ConfigIntegrityError:
        print("  Correctly detected missing kms_key_id: PASS")  # noqa: T201

    # Test 5: Missing threshold keep fields should fail
    print("\n[Test 5] Invalid: threshold fields NOT in aws_lb_target_group.keep")  # noqa: T201
    invalid_keep_config = {
        "global": {"no_redact": ["kms_key_id", "kms_master_key_id"]},
        "resources": {
            "aws_subnet": {"ignores": ["subnet_id"]},
            "aws_lb_target_group": {
                "ignores": ["targets"],
                "keep": [],  # threshold fields NOT here - WRONG!
                "transforms": {"matcher": {"type": "flatten_to_string"}},
            },
        },
    }

    try:
        validate_critical_rules(invalid_keep_config)
        print("  Should have failed but passed: FAIL")  # noqa: T201
        all_passed = False
    except ConfigIntegrityError:
        print("  Correctly detected missing threshold keep: PASS")  # noqa: T201

    # Summary
    print("\n" + "=" * 70)  # noqa: T201
    if all_passed:
        print("ALL TESTS PASSED")  # noqa: T201
    else:
        print("SOME TESTS FAILED")  # noqa: T201
    print("=" * 70)  # noqa: T201

    return all_passed


if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1:
        # Check a specific YAML file
        yaml_path = sys.argv[1]
        try:
            check_config_file(yaml_path)
            sys.exit(0)
        except ConfigIntegrityError as e:
            print(e)  # noqa: T201
            sys.exit(1)
        except Exception as e:
            print(f"Error: {e}")  # noqa: T201
            sys.exit(1)
    else:
        # Run self tests
        success = run_self_tests()
        sys.exit(0 if success else 1)
