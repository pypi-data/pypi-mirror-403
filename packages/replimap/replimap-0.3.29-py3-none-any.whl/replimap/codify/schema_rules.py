"""
Schema Rule Loader - Load and cache mapping rules from YAML.

Single Source of Truth for all AWS → Terraform mappings.
This module loads rules from schema_rules.yaml and provides
methods to query them for field filtering, renaming, typing, and transforms.

VERSION: 3.5 - Ultimate Fix
- O(1) pre-compiled lookup tables with normalize()
- LRU cache for string operations
- Dual conversion: normalize() for lookups, to_snake_case() for regex
- NEW: no_redact whitelist for fields like kms_key_id that should not be redacted
"""

from __future__ import annotations

import functools
import logging
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml

logger = logging.getLogger(__name__)


# ═══════════════════════════════════════════════════════════════════════════════
# String Conversion Functions (with LRU Cache)
# ═══════════════════════════════════════════════════════════════════════════════


@functools.lru_cache(maxsize=2048)
def normalize(name: str) -> str:
    """
    Normalize field name for O(1) dict/set lookup.

    Removes underscores, hyphens and converts to lowercase.
    Cached for performance (field names repeat across resources).

    Examples:
        VpcId → vpcid
        vpc_id → vpcid
        SecurityGroups → securitygroups
        security_groups → securitygroups
    """
    return name.lower().replace("_", "").replace("-", "")


@functools.lru_cache(maxsize=2048)
def to_snake_case(name: str) -> str:
    """
    Convert PascalCase/camelCase to snake_case.

    Used ONLY for global readonly pattern matching where
    patterns like ".*_count$" expect snake_case input.
    Cached for performance.

    Examples:
        RequestCount → request_count
        VpcId → vpc_id
        DNSName → dns_name
        IPv6CidrBlock → ipv6_cidr_block
    """
    # Step 1: Handle acronyms (2+ uppercase) followed by word start
    s1 = re.sub(r"([A-Z]{2,})([A-Z][a-z])", r"\1_\2", name)
    # Step 2: Handle camelCase - insert _ between lower/digit and upper
    s2 = re.sub(r"([a-z0-9])([A-Z])", r"\1_\2", s1)
    return s2.lower()


def clear_cache() -> None:
    """Clear LRU caches (useful for testing)."""
    normalize.cache_clear()
    to_snake_case.cache_clear()


# ═══════════════════════════════════════════════════════════════════════════════
# Data Classes
# ═══════════════════════════════════════════════════════════════════════════════


@dataclass
class BlockConfig:
    """Configuration for a block field."""

    name: str
    block_type: str = "block"  # block, set, list
    sort_keys: list[str] | None = None
    keep_empty: bool = False


@dataclass
class FlattenConfig:
    """Configuration for structure flattening."""

    source: str
    target: str  # "__root__" for root level
    mapping: dict[str, str] = field(default_factory=dict)


@dataclass
class ResourceRules:
    """Rules for a specific Terraform resource type."""

    # Original rules (as loaded from YAML)
    renames: dict[str, str] = field(default_factory=dict)
    ignores: set[str] = field(default_factory=set)
    keep: set[str] = field(default_factory=set)
    types: dict[str, str] = field(default_factory=dict)
    blocks: dict[str, BlockConfig] = field(default_factory=dict)
    defaults: dict[str, Any] = field(default_factory=dict)
    secrets: set[str] = field(default_factory=set)
    flatten: list[FlattenConfig] = field(default_factory=list)
    transforms: dict[str, dict] = field(default_factory=dict)
    # v3.5: Fields that should NOT be redacted (preserve original value)
    no_redact: set[str] = field(default_factory=set)

    # Pre-compiled normalized lookups (for O(1) access)
    _norm_renames: dict[str, str] = field(default_factory=dict)
    _norm_ignores: set[str] = field(default_factory=set)
    _norm_keep: set[str] = field(default_factory=set)
    _norm_transforms: dict[str, dict] = field(default_factory=dict)
    _norm_no_redact: set[str] = field(default_factory=set)


@dataclass
class GlobalRules:
    """Global rules applied to all resources."""

    readonly_patterns: list[re.Pattern] = field(default_factory=list)
    json_patterns: list[re.Pattern] = field(default_factory=list)
    prune_empty: bool = True
    prune_values: list[Any] = field(default_factory=lambda: ["", [], {}, None])
    # v3.5: Fields that should NOT be redacted globally (preserve original value)
    no_redact: set[str] = field(default_factory=set)
    _norm_no_redact: set[str] = field(default_factory=set)


# ═══════════════════════════════════════════════════════════════════════════════
# Schema Rule Loader
# ═══════════════════════════════════════════════════════════════════════════════


class SchemaRuleLoader:
    """
    Load and provide access to schema mapping rules.

    v3.5 Improvements:
    - Pre-compiled normalized lookup tables for O(1) access
    - Dual conversion: normalize() for dict lookups, to_snake_case() for regex
    - LRU caching for string operations
    - NEW: no_redact whitelist for preventing over-redaction of ARN fields
    """

    _instance: SchemaRuleLoader | None = None
    _rules_cache: dict[str, ResourceRules] = {}
    _global_rules: GlobalRules | None = None
    _loaded: bool = False

    def __new__(cls) -> SchemaRuleLoader:
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self) -> None:
        if not self._loaded:
            self._load_rules()
            SchemaRuleLoader._loaded = True

    def _load_rules(self) -> None:
        """Load rules from YAML file."""
        yaml_path = Path(__file__).parent.parent / "data" / "schema_rules.yaml"

        if not yaml_path.exists():
            logger.warning(f"Schema rules file not found: {yaml_path}")
            self._global_rules = GlobalRules()
            return

        with open(yaml_path) as f:
            data = yaml.safe_load(f)

        if not data:
            logger.warning("Schema rules file is empty")
            self._global_rules = GlobalRules()
            return

        # Load global rules
        global_data = data.get("global", {})
        prune_config = global_data.get("prune_empty", {})

        # v3.5: Parse global no_redact whitelist
        global_no_redact = set(global_data.get("no_redact", []))
        global_norm_no_redact = {normalize(item) for item in global_no_redact}

        self._global_rules = GlobalRules(
            readonly_patterns=[
                re.compile(p) for p in global_data.get("readonly_patterns", [])
            ],
            json_patterns=[re.compile(p) for p in global_data.get("json_patterns", [])],
            prune_empty=(
                prune_config.get("enabled", True)
                if isinstance(prune_config, dict)
                else True
            ),
            prune_values=(
                prune_config.get("values", ["", [], {}, None])
                if isinstance(prune_config, dict)
                else ["", [], {}, None]
            ),
            no_redact=global_no_redact,
            _norm_no_redact=global_norm_no_redact,
        )

        # Load resource-specific rules
        for resource_type, rules_data in data.get("resources", {}).items():
            if not rules_data:
                continue

            # Parse block configurations
            blocks = {}
            for block_item in rules_data.get("blocks", []):
                if isinstance(block_item, str):
                    blocks[block_item] = BlockConfig(name=block_item)
                elif isinstance(block_item, dict):
                    for name, config in block_item.items():
                        if config is None:
                            blocks[name] = BlockConfig(name=name)
                        else:
                            blocks[name] = BlockConfig(
                                name=name,
                                block_type=config.get("type", "block"),
                                sort_keys=config.get("sort_by"),
                                keep_empty=config.get("keep_empty", False),
                            )

            # Parse flatten configurations
            flatten_configs = []
            for source, config in rules_data.get("flatten", {}).items():
                if config and isinstance(config, dict):
                    flatten_configs.append(
                        FlattenConfig(
                            source=source,
                            target=config.get("target", "__root__"),
                            mapping=config.get("mapping", {}),
                        )
                    )
                elif config and isinstance(config, str):
                    flatten_configs.append(
                        FlattenConfig(
                            source=source,
                            target=config,
                            mapping={},
                        )
                    )

            # Parse transforms (v3.1)
            transforms = rules_data.get("transforms", {})

            # Get raw rules
            raw_renames = rules_data.get("renames", {})
            raw_ignores = set(rules_data.get("ignores", []))
            raw_keep = set(rules_data.get("keep", []))
            # v3.5: Parse resource-specific no_redact
            raw_no_redact = set(rules_data.get("no_redact", []))

            # Pre-compile normalized lookup tables
            norm_renames = {normalize(k): v for k, v in raw_renames.items()}
            norm_ignores = {normalize(item) for item in raw_ignores}
            norm_keep = {normalize(item) for item in raw_keep}
            norm_transforms = {normalize(k): v for k, v in transforms.items()}
            norm_no_redact = {normalize(item) for item in raw_no_redact}

            self._rules_cache[resource_type] = ResourceRules(
                renames=raw_renames,
                ignores=raw_ignores,
                keep=raw_keep,
                types=rules_data.get("types", {}),
                blocks=blocks,
                defaults=rules_data.get("defaults", {}),
                secrets=set(rules_data.get("secrets", [])),
                flatten=flatten_configs,
                transforms=transforms,
                no_redact=raw_no_redact,
                _norm_renames=norm_renames,
                _norm_ignores=norm_ignores,
                _norm_keep=norm_keep,
                _norm_transforms=norm_transforms,
                _norm_no_redact=norm_no_redact,
            )

        # Validate defaults match types
        self._validate_defaults()

        logger.info(f"Loaded schema rules for {len(self._rules_cache)} resources")

    def _validate_defaults(self) -> None:
        """Validate that default values match their declared types."""
        for resource_type, rules in self._rules_cache.items():
            for field_name, default_value in rules.defaults.items():
                declared_type = rules.types.get(field_name)
                if declared_type == "int" and not isinstance(default_value, int):
                    logger.warning(
                        f"[{resource_type}] Default for {field_name} should be int, "
                        f"got {type(default_value).__name__}"
                    )
                elif declared_type == "bool" and not isinstance(default_value, bool):
                    logger.warning(
                        f"[{resource_type}] Default for {field_name} should be bool, "
                        f"got {type(default_value).__name__}"
                    )

    def get_rules(self, resource_type: str) -> ResourceRules:
        """Get rules for a specific resource type."""
        return self._rules_cache.get(resource_type, ResourceRules())

    def get_global_rules(self) -> GlobalRules:
        """Get global rules."""
        return self._global_rules or GlobalRules()

    def should_remove_field(
        self,
        field_name: str,
        resource_rules: ResourceRules,
    ) -> bool:
        """
        Check if a field should be removed.

        v3.4: Uses dual conversion strategy:
        - normalize() for O(1) dict/set lookups (resource-specific rules)
        - to_snake_case() for global regex pattern matching

        Priority:
        1. Explicit keep (whitelist) → KEEP
        2. Explicit ignore → REMOVE
        3. Global pattern match → REMOVE
        4. Otherwise → KEEP
        """
        norm_name = normalize(field_name)

        # Priority 1: Whitelist override (O(1) lookup)
        if norm_name in resource_rules._norm_keep:
            return False

        # Priority 2: Explicit ignore (O(1) lookup)
        if norm_name in resource_rules._norm_ignores:
            return True

        # Priority 3: Global patterns (snake_case for regex)
        snake_name = to_snake_case(field_name)
        global_rules = self.get_global_rules()
        if any(p.search(snake_name) for p in global_rules.readonly_patterns):
            return True

        return False

    def get_rename(self, field_name: str, resource_rules: ResourceRules) -> str | None:
        """
        Get the renamed field name if a rename rule exists.

        v3.4: Uses normalize() for O(1) lookup.
        """
        norm_name = normalize(field_name)
        return resource_rules._norm_renames.get(norm_name)

    def get_transform(
        self, field_name: str, resource_rules: ResourceRules
    ) -> dict | None:
        """
        Get the transform config if a transform rule exists.

        v3.4: Uses normalize() for O(1) lookup.
        """
        norm_name = normalize(field_name)
        return resource_rules._norm_transforms.get(norm_name)

    def is_json_field(self, field_name: str, resource_rules: ResourceRules) -> bool:
        """Check if field should be JSON encoded."""
        # Check resource-specific types (exact match first)
        if resource_rules.types.get(field_name) == "json":
            return True

        # Check with normalized key
        norm_name = normalize(field_name)
        for type_field, type_val in resource_rules.types.items():
            if normalize(type_field) == norm_name and type_val == "json":
                return True

        # Check global patterns (snake_case for regex)
        snake_name = to_snake_case(field_name)
        return any(p.search(snake_name) for p in self.get_global_rules().json_patterns)

    def should_not_redact(
        self,
        field_name: str,
        resource_type: str | None = None,
    ) -> bool:
        """
        Check if a field should NOT be redacted (keep original value).

        v3.5: This prevents over-redaction of fields like kms_key_id that
        must contain valid ARNs for terraform plan to succeed.

        Priority:
        1. Resource-specific no_redact → DO NOT REDACT
        2. Global no_redact → DO NOT REDACT
        3. Otherwise → allow redaction

        Args:
            field_name: The field name to check
            resource_type: Optional resource type for resource-specific rules
        """
        norm_name = normalize(field_name)

        # Priority 1: Resource-specific no_redact (O(1) lookup)
        if resource_type:
            resource_rules = self.get_rules(resource_type)
            if norm_name in resource_rules._norm_no_redact:
                return True

        # Priority 2: Global no_redact (O(1) lookup)
        global_rules = self.get_global_rules()
        if norm_name in global_rules._norm_no_redact:
            return True

        return False

    def reload(self) -> None:
        """Reload rules from YAML (useful for testing)."""
        self._rules_cache.clear()
        SchemaRuleLoader._loaded = False
        clear_cache()  # Clear LRU caches
        self._load_rules()
        SchemaRuleLoader._loaded = True

    # Keep for backwards compatibility
    @staticmethod
    def _to_snake_case(name: str) -> str:
        """Convert CamelCase to snake_case. Use to_snake_case() instead."""
        return to_snake_case(name)
