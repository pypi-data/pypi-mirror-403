"""
Secrets to Variable Transformer - Extract secrets with BIDIRECTIONAL binding.

VERSION: 3.7.8 - Enhanced SAFE_SUFFIXES with numeric field suffixes

v3.7.8 FIX: Added _seconds, _timeout, _period, _size, _count, _limit, _port,
            _interval, _threshold, _version to SAFE_SUFFIXES to prevent
            over-redaction of numeric fields that need type conversion.
v3.7.1 FIX: Enhanced SAFE_FIELDS whitelist with suffix checks

CRITICAL: This transformer must do TWO things:
1. Create Variable definitions in variables.tf
2. UPDATE the resource attribute to reference the variable

WRONG (one-way):
  variables.tf:  variable "db_password" { ... }
  rds.tf:        password = "actual-password"  # NOT UPDATED!

RIGHT (bidirectional):
  variables.tf:  variable "db_password" { ... }
  rds.tf:        password = var.db_password    # CORRECTLY REFERENCED

v3.5 FIX: Added SAFE_FIELDS whitelist to prevent over-redaction of fields
like kms_key_id, certificate_arn, role_arn which must contain valid ARNs.

v3.7.1 FIX: Added suffix-based checks (_id, _arn, _name) as defense-in-depth
for fields not explicitly listed in SAFE_FIELDS whitelist.
"""

from __future__ import annotations

import logging
import re
from typing import TYPE_CHECKING, Any

from .base import BaseCodifyTransformer

if TYPE_CHECKING:
    from replimap.core.unified_storage import GraphEngineAdapter

logger = logging.getLogger(__name__)


# Patterns for identifying sensitive field names
SENSITIVE_PATTERNS = [
    r"password",
    r"secret",
    r"api[_-]?key",
    r"auth[_-]?token",
    r"access[_-]?key",
    r"private[_-]?key",
    r"credential",
    r"master_password",
    r"admin_password",
    r"db_password",
    r"connection[_-]?string",
    r"secret[_-]?key",
]

# Compiled patterns for efficiency
SENSITIVE_REGEX = [re.compile(p, re.IGNORECASE) for p in SENSITIVE_PATTERNS]


class SecretsToVariableTransformer(BaseCodifyTransformer):
    """
    Extract sensitive values to Terraform variables.

    Scans resource configurations for fields that look like secrets
    (passwords, API keys, tokens, etc.) and:
    1. Creates variable definitions for each secret
    2. Replaces the actual value with a variable reference

    This ensures secrets are never hardcoded in generated Terraform code.

    v3.5 FIX: Added SAFE_FIELDS whitelist to prevent over-redaction of
    fields like kms_key_id that must contain valid ARNs.
    """

    name = "SecretsToVariableTransformer"

    # ═══════════════════════════════════════════════════════════════════════════
    # v3.5 CRITICAL: Fields that should NEVER be redacted
    # These contain ARNs or IDs that must be valid for terraform plan to succeed
    # ═══════════════════════════════════════════════════════════════════════════
    SAFE_FIELDS: set[str] = {
        # KMS Keys (must be valid ARNs)
        "kms_key_id",
        "kms_master_key_id",
        "kms_key_arn",
        "key_arn",
        "key_id",
        # Certificates
        "certificate_arn",
        "acm_certificate_arn",
        "ssl_certificate_id",
        # IAM
        "iam_role_arn",
        "role_arn",
        "execution_role_arn",
        "task_role_arn",
        "instance_profile_arn",
        # Other ARN fields that are NOT secrets
        "source_arn",
        "destination_arn",
        "target_arn",
        "topic_arn",
        "queue_arn",
        "function_arn",
        "bucket_arn",
        "stream_arn",
        "table_arn",
        "cluster_arn",
        "service_arn",
        "load_balancer_arn",
        "target_group_arn",
        "listener_arn",
        "log_group_arn",
        "sns_topic_arn",
        "sqs_queue_arn",
    }

    # Pre-compiled normalized safe fields for O(1) lookup
    _NORM_SAFE_FIELDS: set[str] = {f.lower().replace("_", "") for f in SAFE_FIELDS}

    # v3.7.1: Safe suffixes - fields ending with these are NEVER redacted
    # Using original key with underscore to avoid false positives (e.g., "fluid")
    # v3.7.8: Added _seconds, _timeout, _period to prevent numeric field redaction
    SAFE_SUFFIXES: tuple[str, ...] = (
        "_id",
        "_arn",
        "_ids",
        "_arns",
        "_name",
        "_type",
        "_seconds",
        "_timeout",
        "_period",
        "_size",
        "_count",
        "_limit",
        "_port",
        "_interval",
        "_threshold",
        "_version",
    )

    def __init__(self, extract_secrets: bool = True) -> None:
        """
        Initialize the transformer.

        Args:
            extract_secrets: Whether to extract secrets to variables
        """
        self.extract_secrets = extract_secrets
        self.extracted_variables: list[dict[str, Any]] = []
        self._secrets_extracted = 0

    def transform(self, graph: GraphEngineAdapter) -> GraphEngineAdapter:
        """
        Extract secrets to variables and update references.

        Args:
            graph: The graph to transform

        Returns:
            The transformed graph
        """
        if not self.extract_secrets:
            logger.debug("SecretsToVariableTransformer: extraction disabled")
            return graph

        self.extracted_variables = []
        self._secrets_extracted = 0

        for resource in graph.iter_resources():
            self._scan_config(resource.config, resource)

        # Store extracted variables in graph metadata
        graph.set_metadata("codify_variables", self.extracted_variables)

        if self._secrets_extracted > 0:
            logger.info(
                f"SecretsToVariableTransformer: extracted {self._secrets_extracted} secrets"
            )

        return graph

    def _scan_config(
        self,
        config: dict[str, Any],
        resource: Any,
        path: str = "",
    ) -> None:
        """
        Recursively scan config for sensitive values.

        Args:
            config: Configuration dictionary to scan
            resource: Parent resource for naming
            path: Current path in config for nested fields
        """
        if not isinstance(config, dict):
            return

        for key, value in list(config.items()):
            current_path = f"{path}.{key}" if path else key

            if isinstance(value, str) and self._is_sensitive_key(key):
                # Skip if value is already a variable reference
                if value.startswith("${var.") or value.startswith("var."):
                    continue

                # Skip empty values
                if not value.strip():
                    continue

                # Generate variable name
                var_name = self._generate_variable_name(resource, key)

                # Create variable definition
                self.extracted_variables.append(
                    {
                        "name": var_name,
                        "sensitive": True,
                        "type": "string",
                        "description": (
                            f"Sensitive value for "
                            f"{resource.resource_type}.{resource.terraform_name}.{key}"
                        ),
                        "original_path": current_path,
                        "resource_id": resource.id,
                    }
                )

                # CRITICAL: Update the actual value to reference the variable
                config[key] = f"${{var.{var_name}}}"
                self._secrets_extracted += 1
                logger.debug(f"Extracted secret: {current_path} -> var.{var_name}")

            elif isinstance(value, dict):
                self._scan_config(value, resource, current_path)

            elif isinstance(value, list):
                for i, item in enumerate(value):
                    if isinstance(item, dict):
                        self._scan_config(item, resource, f"{current_path}[{i}]")

    def _is_safe_field(self, key: str) -> bool:
        """
        Check if a field is in the SAFE_FIELDS whitelist.

        v3.5: These fields should NEVER be redacted, even if they
        look like they might contain sensitive data.

        v3.7.1: Also checks safe suffixes (_id, _arn, etc.) as defense-in-depth.
        """
        # 1. Check explicit whitelist (normalized for case/underscore insensitivity)
        normalized = key.lower().replace("_", "").replace("-", "")
        if normalized in self._NORM_SAFE_FIELDS:
            return True

        # 2. Check safe suffixes (with underscore to avoid false positives like "fluid")
        key_lower = key.lower()
        if key_lower.endswith(self.SAFE_SUFFIXES):
            return True

        return False

    def _is_sensitive_key(self, key: str) -> bool:
        """
        Check if a field name indicates sensitive data.

        v3.5: Safe fields are NEVER considered sensitive.
        """
        # SAFE FIELDS ARE NEVER REDACTED
        if self._is_safe_field(key):
            return False

        return any(pattern.search(key) for pattern in SENSITIVE_REGEX)

    def _generate_variable_name(self, resource: Any, field_name: str) -> str:
        """Generate a unique variable name for a secret."""
        # Sanitize resource name
        resource_name = self._sanitize_name(resource.terraform_name)
        field = self._sanitize_name(field_name)

        return f"{resource_name}_{field}"

    def _sanitize_name(self, name: str) -> str:
        """Sanitize a name for use as a Terraform variable name."""
        result = ""
        for char in name:
            if char.isalnum() or char == "_":
                result += char
            else:
                result += "_"
        # Remove consecutive underscores
        while "__" in result:
            result = result.replace("__", "_")
        return result.strip("_").lower()

    @property
    def secrets_extracted(self) -> int:
        """Return the number of secrets extracted."""
        return self._secrets_extracted
