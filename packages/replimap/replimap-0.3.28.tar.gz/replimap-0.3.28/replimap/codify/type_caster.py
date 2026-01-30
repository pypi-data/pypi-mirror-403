"""
Type Caster - Force type casting based on YAML rules.

CRITICAL: Includes null safety as per Architect's Pre-Flight Patch.
Values that are None pass through to be handled by EmptyPruner later.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any

from replimap.codify.hcl_types import HCLJsonEncode, HCLSet

if TYPE_CHECKING:
    from replimap.codify.schema_rules import BlockConfig

logger = logging.getLogger(__name__)


class TypeCaster:
    """Cast field values to correct types based on rules."""

    # Boolean string mappings
    BOOL_TRUE = {"true", "True", "TRUE", "yes", "Yes", "YES", "1"}
    BOOL_FALSE = {"false", "False", "FALSE", "no", "No", "NO", "0"}

    def cast(
        self,
        key: str,
        value: Any,
        rule_type: str | None,
        block_config: BlockConfig | None = None,
    ) -> Any:
        """
        Cast a value to the specified type.

        CRITICAL: Null Safety - if value is None, return None immediately.
        Let EmptyPruner (Step 9) handle it later.
        """
        # NULL SAFETY: Check for None FIRST
        if value is None:
            return None  # Let EmptyPruner handle it

        # Handle explicit type rules
        if rule_type == "json":
            if isinstance(value, (dict, list)):
                return HCLJsonEncode(value)
            return value

        if rule_type == "bool":
            return self._cast_bool(value)

        if rule_type == "int":
            return self._cast_int(value)

        # Handle block configurations
        if block_config:
            if block_config.block_type == "set" and isinstance(value, list):
                return HCLSet(
                    items=[item for item in value if isinstance(item, dict)],
                    sort_keys=block_config.sort_keys,
                )

        return value

    def _cast_bool(self, value: Any) -> bool | None:
        """
        Cast value to boolean.

        Handles:
        - Actual bool: pass through
        - String: "true"/"false" variations
        - Int: 0/1
        - None: return None (null safety)
        """
        if value is None:
            return None

        if isinstance(value, bool):
            return value

        if isinstance(value, str):
            if value in self.BOOL_TRUE:
                return True
            if value in self.BOOL_FALSE:
                return False
            logger.warning(f"Unexpected boolean string: {value}, defaulting to False")
            return False

        if isinstance(value, int):
            return value != 0

        return bool(value)

    def _cast_int(self, value: Any) -> int | None:
        """Cast value to integer with null safety."""
        if value is None:
            return None

        if isinstance(value, int):
            return value

        if isinstance(value, str):
            try:
                # Handle empty string
                if not value.strip():
                    return None
                return int(value)
            except ValueError:
                logger.warning(f"Cannot cast to int: {value}, returning None")
                return None

        if isinstance(value, float):
            return int(value)

        try:
            return int(value)
        except (ValueError, TypeError):
            return None
