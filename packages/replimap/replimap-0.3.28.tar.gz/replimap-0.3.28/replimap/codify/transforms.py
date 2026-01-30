"""
replimap/codify/transforms.py

Transform handlers for schema mapping.

VERSION: 3.7.10 SQS Conflicts & Read-Only Fix
STATUS: Production Ready

Type-safe transformations for AWS API -> Terraform conversions.

Supported transforms (v3.7.10):
- unwrap_list: Extract first element from single-item list
- list_to_map: Convert [{key, value}] list to {key: value} map
- boolean_from_string: Convert "true"/"false" to boolean
- flatten_single_key: Extract value from single-key dict
- rename_keys: Rename keys inside nested dict (v3.5)
- extract_ids: Extract ID field from object list (v3.5)
- flatten_to_string: Extract single field from nested dict (v3.5, FIXED v3.7)
- sort_list: Sort list deterministically (v3.5)
- clean_list_items: Rename & strip keys in list of dicts (v3.7.3)
- rename_value: Rename specific string values (v3.7.6)
- to_int: Convert string to integer (v3.7.7 NEW)
- to_bool: Convert string to boolean (v3.7.7 NEW)

v3.7.7 Critical Fixes:
- NEW: to_int transform for SQS numeric fields (fixes 184 errors)
  AWS API returns strings like "30" but Terraform expects integers
- NEW: to_bool transform for boolean fields returned as strings

v3.7.6 Critical Fixes:
- NEW: rename_value transform for handling reserved names
  e.g., "default" -> "default-imported" for aws_db_subnet_group

v3.7.3 Critical Fixes:
- NEW: clean_list_items transform for RDS parameter groups
  AWS API returns read-only fields (apply_type, is_modifiable) that Terraform rejects

v3.7 Critical Fixes:
- flatten_to_string: Now handles list-wrapped dicts [{"HttpCode": "200"}]
  AWS API sometimes returns blocks as lists instead of dicts

v3.5 transforms fix critical terraform plan errors:
- rename_keys: health_check { IntervalSeconds → interval }
- extract_ids: Subnets [{SubnetIdentifier: "subnet-1"}] → subnet_ids = ["subnet-1"]
- flatten_to_string: Matcher { HttpCode: "200" } → matcher = "200"

Usage:
    from replimap.codify.transforms import TransformHandler, transform_field, apply_transforms

    # Direct usage
    value = TransformHandler.apply(["my-role"], "unwrap_list")
    # Result: "my-role"

    # With config
    dims = [{"Name": "InstanceId", "Value": "i-123"}]
    result = TransformHandler.apply(dims, TransformConfig(
        type="list_to_map",
        key_field="Name",
        value_field="Value"
    ))
    # Result: {"InstanceId": "i-123"}

    # Full config transformation
    result = apply_transforms(config, transforms_dict)
"""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass
from typing import Any

logger = logging.getLogger(__name__)


# ===============================================================================
# CONFIGURATION
# ===============================================================================


@dataclass
class TransformConfig:
    """
    Configuration for a transform operation.

    Attributes:
        type: Transform type (unwrap_list, list_to_map, boolean_from_string, etc.)
        key_field: For list_to_map - field name containing the key (default: "Name")
        value_field: For list_to_map - field name containing the value (default: "Value")
        target: Target field name after transformation (optional rename)
        default: Default value if transformation results in None/empty
        mapping: For rename_keys - dict mapping source keys to target keys (v3.5)
        id_field: For extract_ids - field containing ID value (v3.5)
        extract_field: For flatten_to_string - field to extract (v3.5)
    """

    type: str
    key_field: str | None = None
    value_field: str | None = None
    target: str | None = None
    default: Any = None
    # v3.5 new fields
    mapping: dict | None = None
    id_field: str | None = None
    extract_field: str | None = None

    @classmethod
    def from_dict(cls, data: dict | str) -> TransformConfig:
        """Create TransformConfig from dict or string."""
        if isinstance(data, str):
            return cls(type=data)
        if isinstance(data, dict):
            return cls(
                **{k: v for k, v in data.items() if k in cls.__dataclass_fields__}
            )
        raise ValueError(f"Invalid transform config: {data}")


# ===============================================================================
# TRANSFORM HANDLER
# ===============================================================================


class TransformHandler:
    """
    Handle value transformations based on schema rules.

    This class provides static methods for common AWS API -> Terraform
    type conversions that cannot be handled by simple renaming.

    Design Principles:
    - Never raise exceptions - log warnings and return original value on failure
    - Support multiple naming conventions (PascalCase, snake_case, lowercase)
    - Handle None and empty values gracefully
    """

    # Common key field name variants in AWS APIs
    KEY_FIELD_VARIANTS = ["Name", "name", "Key", "key"]
    VALUE_FIELD_VARIANTS = ["Value", "value"]

    @classmethod
    def apply(cls, value: Any, config: TransformConfig | str | dict) -> Any:
        """
        Apply transformation based on config type.

        Args:
            value: The value to transform
            config: Transform configuration (type string, dict, or TransformConfig)

        Returns:
            Transformed value, or original value if transformation fails
        """
        # Normalize config
        if isinstance(config, str):
            config = TransformConfig(type=config)
        elif isinstance(config, dict):
            config = TransformConfig.from_dict(config)

        handlers = {
            "unwrap_list": cls._unwrap_list,
            "list_to_map": cls._list_to_map,
            "boolean_from_string": cls._boolean_from_string,
            "flatten_single_key": cls._flatten_single_key,
            # v3.5 new transforms
            "rename_keys": cls._rename_keys,
            "extract_ids": cls._extract_ids,
            "flatten_to_string": cls._flatten_to_string,
            "sort_list": cls._sort_list,
            # v3.7.3 new transforms
            "clean_list_items": cls._clean_list_items,
            # v3.7.6 new transforms
            "rename_value": cls._rename_value,
            # v3.7.7 new transforms
            "to_int": cls._to_int,
            "to_bool": cls._to_bool,
        }

        handler = handlers.get(config.type)
        if not handler:
            logger.warning(f"Unknown transform type: {config.type}")
            return value

        try:
            result = handler(value, config)
            return result if result is not None else config.default
        except Exception as e:
            logger.warning(
                f"Transform {config.type} failed for value {type(value)}: {e}"
            )
            return value

    @staticmethod
    def _unwrap_list(value: Any, config: TransformConfig) -> Any:
        """
        Extract first element from a list.

        Use cases:
        - aws_iam_instance_profile: Roles: ["role-name"] -> role: "role-name"

        Examples:
            ["my-role"] -> "my-role"
            [] -> None (or config.default)
            "already-string" -> "already-string" (passthrough)
            [{"complex": "obj"}] -> {"complex": "obj"}
            None -> None
        """
        if value is None:
            return config.default

        if not isinstance(value, list):
            return value  # Passthrough non-list values

        if not value:
            return config.default

        return value[0]

    @classmethod
    def _list_to_map(cls, value: Any, config: TransformConfig) -> dict | None:
        """
        Convert list of dicts to a map.

        Use cases:
        - aws_cloudwatch_metric_alarm: Dimensions
        - aws_appautoscaling_target: Dimensions
        - AWS Tags: [{Key: k, Value: v}] -> {k: v}

        Features:
        - Supports multiple key field variants (Name, name, Key, key)
        - Supports multiple value field variants (Value, value)
        - Allows missing value field (defaults to None)
        - Skips invalid items without failing

        Examples:
            [{Name: "k1", Value: "v1"}] -> {"k1": "v1"}
            [{Key: "k1", Value: "v1"}] -> {"k1": "v1"}
            [{name: "k1", value: "v1"}] -> {"k1": "v1"}
            [{Name: "k1"}] -> {"k1": None}  # Missing value
            [] -> None
        """
        if value is None:
            return config.default

        if not isinstance(value, list):
            return value  # Passthrough non-list values

        if not value:
            return config.default

        # Determine key/value field names
        key_fields = [config.key_field] if config.key_field else cls.KEY_FIELD_VARIANTS
        value_fields = (
            [config.value_field] if config.value_field else cls.VALUE_FIELD_VARIANTS
        )

        result = {}
        for item in value:
            if not isinstance(item, dict):
                continue

            # Find key field
            k = None
            for kf in key_fields:
                if kf in item:
                    k = item[kf]
                    break

            if k is None:
                continue  # Skip items without a valid key

            # Find value field (allow missing - default to None)
            v = None
            for vf in value_fields:
                if vf in item:
                    v = item[vf]
                    break

            result[k] = v

        return result if result else config.default

    @staticmethod
    def _boolean_from_string(value: Any, config: TransformConfig) -> bool | None:
        """
        Convert string to boolean (case-insensitive).

        Examples:
            "true" -> True
            "false" -> False
            "True" -> True
            "FALSE" -> False
            "yes" -> True
            "no" -> False
            True -> True (passthrough)
            "" -> None
            None -> None
        """
        if value is None:
            return config.default

        if isinstance(value, bool):
            return value

        if isinstance(value, str):
            lower = value.lower().strip()
            if lower in ("true", "yes", "1", "enabled", "on"):
                return True
            elif lower in ("false", "no", "0", "disabled", "off"):
                return False
            elif lower == "":
                return config.default

        # For other types, use Python's truthiness
        return bool(value)

    @staticmethod
    def _flatten_single_key(value: Any, config: TransformConfig) -> Any:
        """
        Extract value from a single-key dict.

        Use cases:
        - DynamoDB attribute values: {"S": "string-value"} -> "string-value"

        Examples:
            {"S": "string-value"} -> "string-value"
            {"N": "123"} -> "123"
            {"key1": "v1", "key2": "v2"} -> unchanged (multiple keys)
            "already-string" -> "already-string" (passthrough)
        """
        if value is None:
            return config.default

        if not isinstance(value, dict):
            return value

        if len(value) == 1:
            return list(value.values())[0]

        return value

    # ═══════════════════════════════════════════════════════════════════════════
    # v3.5 NEW TRANSFORMS
    # ═══════════════════════════════════════════════════════════════════════════

    @classmethod
    def _rename_keys(cls, value: Any, config: TransformConfig) -> Any:
        """
        Rename keys inside a nested dict/block.

        Use cases:
        - aws_lb_target_group: health_check block field renaming
          IntervalSeconds -> interval, TimeoutSeconds -> timeout

        Examples:
            Input: {"IntervalSeconds": 30, "TimeoutSeconds": 5}
            Mapping: {"IntervalSeconds": "interval", "TimeoutSeconds": "timeout"}
            Output: {"interval": 30, "timeout": 5}

        Features:
        - Case-insensitive matching with normalization
        - Unmapped keys pass through unchanged
        """
        if value is None:
            return config.default

        if not isinstance(value, dict):
            return value

        mapping = config.mapping
        if not mapping:
            return value

        # Build normalized mapping for O(1) lookup
        norm_mapping: dict[str, str] = {}
        for src, dst in mapping.items():
            norm_key = src.lower().replace("_", "").replace("-", "")
            norm_mapping[norm_key] = dst

        new_dict = {}
        for k, v in value.items():
            norm_k = k.lower().replace("_", "").replace("-", "")
            target_key = norm_mapping.get(norm_k, k)
            new_dict[target_key] = v

        return new_dict

    @classmethod
    def _extract_ids(cls, value: Any, config: TransformConfig) -> list | Any:
        """
        Extract ID field from list of objects.

        Use cases:
        - aws_db_subnet_group: Subnets object list -> subnet_ids string list
        - aws_elasticache_subnet_group: Same pattern

        Examples:
            Input: [{"SubnetIdentifier": "subnet-1"}, {"SubnetIdentifier": "subnet-2"}]
            id_field: "SubnetIdentifier"
            Output: ["subnet-1", "subnet-2"]

        Features:
        - Case-insensitive field lookup
        - Sorted output for deterministic results
        """
        if value is None:
            return config.default

        if not isinstance(value, list):
            return value

        id_field = config.id_field or "Id"
        ids = []

        for item in value:
            if isinstance(item, dict):
                # Case-insensitive lookup
                id_val = cls._get_dict_value_ci(item, id_field)
                if id_val is not None:
                    ids.append(id_val)

        # Sort for deterministic output
        try:
            return sorted(ids)
        except TypeError:
            return sorted(ids, key=str)

    @classmethod
    def _flatten_to_string(cls, value: Any, config: TransformConfig) -> Any:
        """
        Extract a single field from nested dict and return as scalar.

        Use cases:
        - aws_lb_target_group: Matcher block -> matcher string
          {"HttpCode": "200"} -> "200"

        Examples:
            Input: {"HttpCode": "200"}
            extract_field: "HttpCode"
            Output: "200"

            Input: [{"HttpCode": "200"}]  # v3.7: List-wrapped dict
            Output: "200"

        Features:
        - v3.7 FIX: Unwraps list-of-dicts before processing
        - Explicit extract_field takes priority
        - Auto-detects common fields if not specified
        - Returns first value as fallback
        """
        if value is None:
            return config.default

        # v3.7 CRITICAL FIX: AWS API sometimes returns blocks as lists
        # e.g., Matcher: [{"HttpCode": "200"}] instead of {"HttpCode": "200"}
        # TODO: Handle multi-value lists like [{"HttpCode": "200"}, {"HttpCode": "301"}]
        #       if AWS API ever returns them. Currently takes first element only.
        if isinstance(value, list):
            if not value:
                return config.default or ""
            # Unwrap first element (AWS typically returns single-item lists for matcher)
            value = value[0]

        if not isinstance(value, dict):
            # Return string representation for scalar values
            return str(value) if value is not None else config.default

        extract_field = config.extract_field
        if extract_field:
            result = cls._get_dict_value_ci(value, extract_field)
            return str(result) if result is not None else config.default

        # Auto-detect common fields
        common_fields = [
            "HttpCode",
            "http_code",
            "Value",
            "value",
            "GrpcCode",
            "grpc_code",
        ]
        for field in common_fields:
            if field in value:
                return str(value[field])

        # Fallback: return first value if single-key dict
        if len(value) == 1:
            first_val = next(iter(value.values()))
            return str(first_val) if first_val is not None else config.default

        return value

    @staticmethod
    def _sort_list(value: Any, config: TransformConfig) -> Any:
        """
        Sort list deterministically to prevent terraform plan drift.

        Use cases:
        - security_group_ids, subnet_ids, etc.
        - Any list that should have consistent ordering

        Examples:
            ["c", "a", "b"] -> ["a", "b", "c"]
            [{"name": "b"}, {"name": "a"}] -> sorted by json serialization
        """
        if value is None:
            return config.default

        if not isinstance(value, list):
            return value

        if len(value) == 0:
            return value

        try:
            return sorted(value)
        except TypeError:
            # Complex types - sort by JSON serialization
            import json

            try:
                return sorted(value, key=lambda x: json.dumps(x, sort_keys=True))
            except (TypeError, ValueError):
                return sorted(value, key=str)

    # ═══════════════════════════════════════════════════════════════════════════
    # v3.7.3 NEW TRANSFORMS
    # ═══════════════════════════════════════════════════════════════════════════

    @classmethod
    def _clean_list_items(cls, value: Any, config: TransformConfig) -> list | Any:
        """
        Clean list of dicts by renaming and stripping keys.

        Use cases:
        - aws_db_parameter_group.parameter: AWS API returns read-only fields
          that Terraform doesn't accept (apply_type, is_modifiable, etc.)

        Examples:
            Input: [
                {"ParameterName": "foo", "ParameterValue": "bar", "ApplyType": "dynamic"},
                {"ParameterName": "baz", "ParameterValue": "qux", "IsModifiable": true}
            ]
            Mapping: {"ParameterName": "name", "ParameterValue": "value", "ApplyMethod": "apply_method"}
            Output: [
                {"name": "foo", "value": "bar"},
                {"name": "baz", "value": "qux"}
            ]

        Features:
        - Case-insensitive key matching with normalization
        - Only keys in mapping are kept; all others are stripped
        - Filters out items with no valid values after cleaning
        """
        if value is None:
            return config.default

        if not isinstance(value, list):
            return value

        mapping = config.mapping
        if not mapping:
            return value

        # Build normalized mapping for O(1) lookup
        norm_mapping: dict[str, str] = {}
        for src, dst in mapping.items():
            norm_key = src.lower().replace("_", "").replace("-", "")
            norm_mapping[norm_key] = dst

        result = []
        for item in value:
            if not isinstance(item, dict):
                result.append(item)
                continue

            new_item: dict[str, Any] = {}
            for k, v in item.items():
                norm_k = k.lower().replace("_", "").replace("-", "")
                if norm_k in norm_mapping:
                    target_key = norm_mapping[norm_k]
                    if v is not None:  # Skip None values
                        new_item[target_key] = v

            # Only include items that have at least one valid field
            if new_item:
                result.append(new_item)

        return result

    # ═══════════════════════════════════════════════════════════════════════════
    # v3.7.6 NEW TRANSFORMS
    # ═══════════════════════════════════════════════════════════════════════════

    @staticmethod
    def _rename_value(value: Any, config: TransformConfig) -> Any:
        """
        Rename specific string values using a mapping.

        Use cases:
        - aws_db_subnet_group: "default" -> "default-imported"
          Terraform rejects "default" as a reserved name

        Examples:
            Input: "default"
            Mapping: {"default": "default-imported"}
            Output: "default-imported"

            Input: "my-custom-name"
            Mapping: {"default": "default-imported"}
            Output: "my-custom-name"  (unchanged, not in mapping)

        Features:
        - Case-insensitive matching with original case preserved for unmapped values
        - Only string values are transformed
        """
        if value is None:
            return config.default

        if not isinstance(value, str):
            return value

        mapping = config.mapping
        if not mapping:
            return value

        # Case-insensitive lookup
        value_lower = value.lower()
        for src, dst in mapping.items():
            if src.lower() == value_lower:
                logger.debug(f"rename_value: '{value}' -> '{dst}'")
                return dst

        return value

    @staticmethod
    def _to_int(value: Any, config: TransformConfig) -> int | None:
        """
        Convert value to integer.

        Use cases:
        - aws_sqs_queue: delay_seconds, max_message_size, etc.
          AWS API returns "30" but Terraform expects 30

        Examples:
            "30" -> 30
            30 -> 30
            "30.5" -> 30 (truncated)
            "" -> None
            None -> None

        Features:
        - Handles string, int, and float input
        - Returns None for empty or invalid values
        """
        if value is None:
            return config.default

        if isinstance(value, int):
            return value

        if isinstance(value, float):
            return int(value)

        if isinstance(value, str):
            value = value.strip()
            if not value:
                return config.default
            try:
                # Handle decimal strings like "30.0"
                return int(float(value))
            except (ValueError, TypeError):
                # 🚨 v3.7.18 FIX: Don't warn for [REDACTED] values - this is expected
                # SecretsToVariableTransformer replaces sensitive values with [REDACTED]
                # and the to_int transform runs on all fields including redacted ones
                if value != "[REDACTED]":
                    logger.warning(f"to_int: Cannot convert '{value}' to int")
                return config.default

        return config.default

    @staticmethod
    def _to_bool(value: Any, config: TransformConfig) -> bool | None:
        """
        Convert value to boolean.

        Use cases:
        - Various AWS fields that return "true"/"false" strings
          but Terraform expects boolean true/false

        Examples:
            "true" -> True
            "false" -> False
            "True" -> True
            "1" -> True
            "0" -> False
            True -> True
            None -> None

        Features:
        - Case-insensitive string matching
        - Handles various truthy/falsy representations
        """
        if value is None:
            return config.default

        if isinstance(value, bool):
            return value

        if isinstance(value, int):
            return value != 0

        if isinstance(value, str):
            value_lower = value.lower().strip()
            if value_lower in ("true", "yes", "1", "enabled", "on"):
                return True
            elif value_lower in ("false", "no", "0", "disabled", "off", ""):
                return False

        return config.default

    @staticmethod
    def _get_dict_value_ci(d: dict, key: str) -> Any:
        """Get value from dict with case-insensitive key lookup."""
        if key in d:
            return d[key]
        key_lower = key.lower()
        for k, v in d.items():
            if k.lower() == key_lower:
                return v
        # Also try normalized (remove underscores)
        key_norm = key.lower().replace("_", "").replace("-", "")
        for k, v in d.items():
            if k.lower().replace("_", "").replace("-", "") == key_norm:
                return v
        return None


# ===============================================================================
# CONVENIENCE FUNCTIONS
# ===============================================================================


def _to_snake_case(name: str) -> str:
    """Convert PascalCase/camelCase to snake_case."""
    s1 = re.sub("(.)([A-Z][a-z]+)", r"\1_\2", name)
    return re.sub("([a-z0-9])([A-Z])", r"\1_\2", s1).lower()


def transform_field(
    field_name: str,
    value: Any,
    transforms: dict,
) -> tuple[str, Any]:
    """
    Apply transform to a field if configured.

    This is a convenience function for use in the schema mapper.

    Args:
        field_name: The field name to check
        value: The field value
        transforms: Dict of field_name -> transform config

    Returns:
        Tuple of (target_field_name, transformed_value)

    Example:
        transforms = {
            "Roles": {"type": "unwrap_list", "target": "role"},
            "Dimensions": {"type": "list_to_map", "key_field": "Name", "value_field": "Value"}
        }

        name, val = transform_field("Roles", ["my-role"], transforms)
        # name = "role", val = "my-role"
    """
    if field_name not in transforms:
        return field_name, value

    transform_config = transforms[field_name]

    # Parse config
    if isinstance(transform_config, dict):
        config = TransformConfig.from_dict(transform_config)
    elif isinstance(transform_config, str):
        config = TransformConfig(type=transform_config)
    else:
        config = transform_config

    # Apply transformation
    transformed = TransformHandler.apply(value, config)

    # Determine target field name
    target_name = config.target or field_name

    return target_name, transformed


def apply_transforms(config: dict, transforms: dict) -> dict:
    """
    Apply all transforms to a resource config.

    Args:
        config: Resource configuration dict
        transforms: Dict of field_name -> transform config

    Returns:
        New config dict with transforms applied

    Example:
        config = {
            "Roles": ["my-role"],
            "Dimensions": [{"Name": "InstanceId", "Value": "i-123"}]
        }
        transforms = {
            "Roles": {"type": "unwrap_list", "target": "role"},
            "Dimensions": {"type": "list_to_map"}
        }

        result = apply_transforms(config, transforms)
        # {
        #     "role": "my-role",
        #     "Dimensions": {"InstanceId": "i-123"}
        # }
    """
    if not config:
        return {}

    if not transforms:
        return config.copy()

    result = {}

    for field_name, value in config.items():
        target_name, transformed_value = transform_field(field_name, value, transforms)

        # Only include if transformed value is not None
        if transformed_value is not None:
            result[target_name] = transformed_value

    return result


# ===============================================================================
# INTEGRATION HELPER
# ===============================================================================


class SchemaTransformProcessor:
    """
    High-level processor for applying schema transforms to resources.

    Usage:
        processor = SchemaTransformProcessor(schema_rules)
        transformed = processor.process_resource("aws_iam_instance_profile", config)
    """

    def __init__(self, schema_rules: dict) -> None:
        """
        Initialize with schema rules dict.

        Args:
            schema_rules: Loaded schema_rules.yaml content
        """
        self.schema_rules = schema_rules
        self.resources = schema_rules.get("resources", {})

    def get_transforms(self, resource_type: str) -> dict:
        """Get transforms dict for a resource type."""
        resource_rules = self.resources.get(resource_type, {})
        return resource_rules.get("transforms", {})

    def process_resource(self, resource_type: str, config: dict) -> dict:
        """
        Apply all transforms for a resource type.

        Args:
            resource_type: Terraform resource type (e.g., "aws_iam_instance_profile")
            config: Resource configuration dict

        Returns:
            Transformed configuration dict
        """
        transforms = self.get_transforms(resource_type)
        if not transforms:
            return config

        return apply_transforms(config, transforms)
