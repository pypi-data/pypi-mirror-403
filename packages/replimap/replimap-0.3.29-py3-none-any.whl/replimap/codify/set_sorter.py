"""
Set Sorter - Deterministic sorting for HCL sets.

Prevents phantom drifts in terraform plan by ensuring
set items are always rendered in the same order.
"""

from __future__ import annotations

from replimap.codify.hcl_types import HCLBlock, HCLSet


class SetSorter:
    """Sort set items deterministically."""

    def sort_sets(self, config: dict) -> dict:
        """
        Find and sort all HCLSet instances in configuration.

        Returns config with HCLSet.items sorted and converted to HCLBlock list.
        """
        result = {}

        for key, value in config.items():
            if isinstance(value, HCLSet):
                # Sort and convert to list of HCLBlocks
                sorted_items = value.sorted_items()
                result[key] = [HCLBlock(item) for item in sorted_items]

            elif isinstance(value, dict):
                result[key] = self.sort_sets(value)

            elif isinstance(value, list):
                result[key] = [
                    self.sort_sets(item) if isinstance(item, dict) else item
                    for item in value
                ]
            else:
                result[key] = value

        return result
