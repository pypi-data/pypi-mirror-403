"""
Schema Mapper Transformer v3.4 - Production Final.

Processing Pipeline (12 Steps):
1.  GlobalFilter        Remove global readonly patterns
2.  WhitelistOverride   Keep fields in 'keep' list
3.  ResourceFilter      Remove resource-specific ignores
4.  StructureFlattener  Flatten nested structures
5.  FieldRenamer        Apply renames mapping (O(1) normalized lookup)
6.  TransformApplier    Apply type transforms (O(1) normalized lookup)
7.  TypeCaster          Cast types (json, bool, int, set)
8.  BlockMarker         Mark HCL blocks vs maps
9.  DefaultPruner       Remove default values
10. EmptyPruner         Remove empty [], {}, null
11. TagNormalizer       Convert tag formats
12. SetSorter           Deterministic sorting for sets

CRITICAL v3.4 NOTES:
- Uses normalize() for O(1) dict/set lookups (removes underscores)
- Uses to_snake_case() for global regex matching (preserves underscores)
- Pre-compiled lookup tables for renames, ignores, transforms, keep
- LRU cache for string operations (>99% hit rate on typical workloads)
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from replimap.codify.empty_pruner import EmptyPruner
from replimap.codify.hcl_types import HCLBlock, HCLJsonEncode, HCLSet
from replimap.codify.schema_rules import (
    ResourceRules,
    SchemaRuleLoader,
    normalize,
    to_snake_case,
)
from replimap.codify.set_sorter import SetSorter
from replimap.codify.transformers.base import BaseCodifyTransformer
from replimap.codify.transforms import TransformConfig, TransformHandler
from replimap.codify.type_caster import TypeCaster

if TYPE_CHECKING:
    from replimap.core.unified_storage import GraphEngineAdapter

logger = logging.getLogger(__name__)


class SchemaMapperTransformer(BaseCodifyTransformer):
    """
    Transform AWS API responses to valid Terraform configurations.

    v3.4 Production Final:
    - O(1) pre-compiled lookup tables
    - Dual conversion strategy (normalize vs to_snake_case)
    - LRU caching for string operations
    """

    name = "SchemaMapperTransformer"

    def __init__(self) -> None:
        self.loader = SchemaRuleLoader()
        self.type_caster = TypeCaster()
        self.empty_pruner = EmptyPruner(
            prune_values=self.loader.get_global_rules().prune_values
        )
        self.set_sorter = SetSorter()

    def transform(self, graph: GraphEngineAdapter) -> GraphEngineAdapter:
        """Apply schema mapping to all resources."""
        for resource in graph.iter_resources():
            if resource.config:
                tf_type = str(resource.resource_type)
                resource.config = self._map_config(
                    tf_type,
                    resource.config,
                )
        return graph

    def _map_config(self, tf_type: str, config: dict) -> dict:
        """
        Apply all mapping rules to a configuration.

        v3.4: Uses O(1) normalized lookups for renames/transforms.
        """
        rules = self.loader.get_rules(tf_type)
        global_rules = self.loader.get_global_rules()

        # Step 1-3: Filter fields (global + whitelist + resource-specific)
        config = self._filter_fields(config, rules)

        # Step 4: Flatten nested structures
        config = self._apply_flatten(config, rules.flatten)

        # Step 5: Rename fields (O(1) normalized lookup)
        config = self._apply_renames(config, rules)

        # Step 6: Apply transforms (O(1) normalized lookup)
        config = self._apply_transforms(config, rules)

        # Step 7: Cast types
        config = self._apply_types(config, rules)

        # Step 8: Mark blocks
        config = self._apply_block_markers(config, rules)

        # Step 9: Prune defaults
        config = self._apply_default_pruning(config, rules.defaults)

        # Step 10: Prune empty values
        if global_rules.prune_empty:
            keep_empty = {name for name, cfg in rules.blocks.items() if cfg.keep_empty}
            config = self.empty_pruner.prune(config, keep_empty)

        # Step 11: Normalize tags
        config = self._normalize_tags(config)

        # Step 12: Sort sets
        config = self.set_sorter.sort_sets(config)

        return config

    def _filter_fields(self, config: dict, rules: ResourceRules) -> dict:
        """Steps 1-3: Filter out readonly and ignored fields, respecting whitelist."""
        result = {}

        for key, value in config.items():
            if self.loader.should_remove_field(key, rules):
                logger.debug(f"Filtered: {key}")
                continue

            if isinstance(value, dict):
                result[key] = self._filter_fields(value, rules)
            elif isinstance(value, list):
                result[key] = [
                    self._filter_fields(item, rules) if isinstance(item, dict) else item
                    for item in value
                ]
            else:
                result[key] = value

        return result

    def _apply_flatten(self, config: dict, flatten_configs: list) -> dict:
        """Step 4: Flatten nested structures according to rules."""
        if not flatten_configs:
            return config

        result = dict(config)

        for flatten_config in flatten_configs:
            source_field = flatten_config.source

            # Find source value using normalized lookup
            source_value = None
            norm_source = normalize(source_field)
            for key in list(result.keys()):
                if normalize(key) == norm_source:
                    source_value = result.pop(key)
                    break

            if source_value is None or not isinstance(source_value, dict):
                continue

            target = flatten_config.target
            mapping = flatten_config.mapping

            if target == "__root__":
                # Flatten to root level
                for src_key, dest_key in mapping.items():
                    if src_key in source_value:
                        result[dest_key] = source_value[src_key]
                # Copy unmapped fields to root
                for key, value in source_value.items():
                    if key not in mapping:
                        snake_key = to_snake_case(key)
                        if snake_key not in result:
                            result[snake_key] = value
            else:
                # Flatten to nested target
                nested = {}
                for src_key, dest_key in mapping.items():
                    if src_key in source_value:
                        nested[dest_key] = source_value[src_key]
                if nested:
                    result[target] = nested

        return result

    def _apply_renames(self, config: dict, rules: ResourceRules) -> dict:
        """
        Step 5: Apply field name mappings.

        v3.4: Uses O(1) normalized lookup via loader.get_rename().
        """
        result = {}

        for key, value in config.items():
            # O(1) lookup for rename
            new_key = self.loader.get_rename(key, rules)
            if not new_key:
                # No rename found, convert to snake_case
                new_key = to_snake_case(key)

            # Recurse into nested structures
            if isinstance(value, dict):
                result[new_key] = self._apply_renames(value, rules)
            elif isinstance(value, list):
                result[new_key] = [
                    self._apply_renames(item, rules) if isinstance(item, dict) else item
                    for item in value
                ]
            else:
                result[new_key] = value

        return result

    def _apply_transforms(self, config: dict, rules: ResourceRules) -> dict:
        """
        Step 6: Apply transforms with target support.

        v3.4: Uses O(1) normalized lookup via loader.get_transform().
        Transform targets can rename fields without needing explicit renames.
        """
        result = {}
        processed_keys = set()

        for key, value in config.items():
            # O(1) lookup for transform
            transform_config = self.loader.get_transform(key, rules)

            if transform_config:
                tc = TransformConfig.from_dict(transform_config)
                transformed_value = TransformHandler.apply(value, tc)

                # Use transform target as new field name if specified
                final_key = tc.target if tc.target else key

                if transformed_value is not None:
                    result[final_key] = transformed_value
                    processed_keys.add(key)
                    logger.debug(f"Transform: {key} -> {final_key}")
            else:
                result[key] = value

        return result

    def _apply_types(self, config: dict, rules: ResourceRules) -> dict:
        """Step 7: Apply type casting based on rules."""
        result = {}

        for key, value in config.items():
            # Check for explicit type rule
            rule_type = rules.types.get(key)

            # Check for block config
            block_config = rules.blocks.get(key)

            # Check global JSON patterns
            if not rule_type and self.loader.is_json_field(key, rules):
                rule_type = "json"

            # Apply type casting
            if rule_type or block_config:
                result[key] = self.type_caster.cast(key, value, rule_type, block_config)
            elif isinstance(value, dict):
                result[key] = self._apply_types(value, rules)
            elif isinstance(value, list):
                result[key] = [
                    self._apply_types(item, rules) if isinstance(item, dict) else item
                    for item in value
                ]
            else:
                result[key] = value

        return result

    def _apply_block_markers(self, config: dict, rules: ResourceRules) -> dict:
        """Step 8: Mark fields that should be rendered as HCL blocks."""
        result = {}

        for key, value in config.items():
            block_config = rules.blocks.get(key)

            # Skip if already marked as HCLSet by TypeCaster
            if isinstance(value, HCLSet):
                result[key] = value
            elif isinstance(value, HCLJsonEncode):
                result[key] = value
            elif block_config and isinstance(value, dict):
                result[key] = HCLBlock(value)
            elif block_config and isinstance(value, list):
                result[key] = [
                    HCLBlock(item) if isinstance(item, dict) else item for item in value
                ]
            else:
                result[key] = value

        return result

    def _apply_default_pruning(self, config: dict, defaults: dict) -> dict:
        """Step 9: Remove fields that match Terraform defaults."""
        if not defaults:
            return config

        result = {}
        for key, value in config.items():
            if key in defaults and value == defaults[key]:
                logger.debug(f"Pruned default: {key}={value}")
                continue
            result[key] = value

        return result

    def _normalize_tags(self, config: dict) -> dict:
        """Step 11: Convert AWS tag format to Terraform tag format."""
        result = dict(config)

        tag_fields = [
            "Tags",
            "tags",
            "TagSet",
            "tag_set",
            "TagList",
            "TagSpecifications",
        ]

        for tag_field in tag_fields:
            if tag_field in result:
                tags = result.pop(tag_field)

                if isinstance(tags, list):
                    # Convert [{Key: k, Value: v}] to {k: v}
                    result["tags"] = {
                        tag.get("Key") or tag.get("key", ""): tag.get("Value")
                        or tag.get("value", "")
                        for tag in tags
                        if isinstance(tag, dict) and (tag.get("Key") or tag.get("key"))
                    }
                elif isinstance(tags, dict):
                    result["tags"] = tags

        return result
