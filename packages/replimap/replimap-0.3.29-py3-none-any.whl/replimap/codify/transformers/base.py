"""
Base class for Codify transformers.

Codify transformers operate on GraphEngineAdapter and prepare resources
for Terraform code generation and import.
"""

from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from replimap.core.unified_storage import GraphEngineAdapter

logger = logging.getLogger(__name__)


class BaseCodifyTransformer(ABC):
    """
    Abstract base class for Codify transformers.

    Each transformer modifies the graph in-place, preparing resources
    for safe Terraform import and code generation.

    Subclasses must implement:
    - name: Human-readable name for logging
    - transform(): The transformation logic
    """

    name: str = "BaseCodifyTransformer"

    @abstractmethod
    def transform(self, graph: GraphEngineAdapter) -> GraphEngineAdapter:
        """
        Transform the resource graph.

        Args:
            graph: The GraphEngineAdapter to transform

        Returns:
            The transformed GraphEngineAdapter (same instance, modified in place)
        """
        pass

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}()"
