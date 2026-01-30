"""
Codify Pipeline - Orchestrates the 13-stage transformation pipeline.

Pipeline Architecture (v3.7):

    Stage 0 - Schema Mapping (MUST BE FIRST):
        SchemaMapperTransformer - 11-step AWS→Terraform schema mapping
        (GlobalFilter, WhitelistOverride, ResourceFilter, StructureFlattener,
         FieldRenamer, TypeCaster, BlockMarker, DefaultPruner, EmptyPruner,
         TagNormalizer, SetSorter)

    Phase 1 - Filtering (Stages 1-4):
        1. DefaultResourceFilter
        2. GlobalResourceFilter
        3. DataSourceFilter
        4. ManagedResourceFilter

    Phase 2 - Structural (Stages 5-6):
        5. SecurityGroupSplitter
        6. IamAttachmentNormalizer

    Phase 3 - Transformation (Stages 7-9):
        7. SecretsToVariableTransformer
        8. MinimalNamingTransformer
        9. HardcodedIdToRefTransformer

    Phase 4 - Safety & Generation (Stages 10-12):
        10. LifecycleProtector
        11. ImportIDResolver
        12. FinalCleanupTransformer (MUST BE LAST - v3.7)
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from .schema_mapper import SchemaMapperTransformer
from .transformers import (
    DataSourceFilter,
    DefaultResourceFilter,
    FinalCleanupTransformer,
    GlobalResourceFilter,
    HardcodedIdToRefTransformer,
    IamAttachmentNormalizer,
    ImportIDResolver,
    LifecycleProtector,
    ManagedResourceFilter,
    MinimalNamingTransformer,
    SecretsToVariableTransformer,
    SecurityGroupSplitter,
)
from .transformers.base import BaseCodifyTransformer

if TYPE_CHECKING:
    from replimap.core.unified_storage import GraphEngineAdapter

logger = logging.getLogger(__name__)


class CodifyPipeline:
    """
    Manages execution of codify transformers in sequence.

    The pipeline executes all 13 transformers in the correct order,
    preparing the graph for safe Terraform code generation and import.

    CRITICAL:
    - SchemaMapperTransformer MUST be Stage 0 to transform AWS API responses
    - FinalCleanupTransformer MUST be Stage 12 (LAST) to remove dirty fields
    """

    def __init__(
        self,
        transformers: list[BaseCodifyTransformer] | None = None,
    ) -> None:
        """
        Initialize the pipeline.

        Args:
            transformers: List of transformers to execute
        """
        self._transformers = transformers or []

    def add(self, transformer: BaseCodifyTransformer) -> CodifyPipeline:
        """
        Add a transformer to the pipeline.

        Args:
            transformer: The transformer to add

        Returns:
            Self for method chaining
        """
        self._transformers.append(transformer)
        logger.debug(f"Added transformer: {transformer.name}")
        return self

    def execute(self, graph: GraphEngineAdapter) -> GraphEngineAdapter:
        """
        Execute all transformers in sequence.

        Args:
            graph: The input graph

        Returns:
            The transformed graph
        """
        logger.info(
            f"Executing codify pipeline ({len(self._transformers)} transformers)"
        )

        current = graph
        for transformer in self._transformers:
            logger.info(f"Running transformer: {transformer.name}")
            current = transformer.transform(current)

        logger.info("Codify pipeline complete")
        return current

    def __len__(self) -> int:
        return len(self._transformers)

    def __repr__(self) -> str:
        names = [t.name for t in self._transformers]
        return f"CodifyPipeline({names})"


def get_codify_pipeline(
    region: str,
    primary_region: str = "us-east-1",
    include_global: bool = False,
    protect_resources: bool = True,
    convert_amis: bool = True,
    extract_secrets: bool = True,
    split_sg_rules: bool = True,
    normalize_iam: bool = True,
    skip_defaults: bool = True,
    managed_ids: set[str] | None = None,
) -> CodifyPipeline:
    """
    Build the complete codify pipeline for production use (v3.7).

    CRITICAL:
    - SchemaMapperTransformer MUST be Stage 0 (transforms AWS API responses)
    - FinalCleanupTransformer MUST be Stage 12 (removes dirty fields)

    Args:
        region: Current region being processed
        primary_region: Region where global resources should be defined
        include_global: Force include global resources regardless of region
        protect_resources: Add lifecycle protection to critical resources
        convert_amis: Convert known AMIs to data sources
        extract_secrets: Extract sensitive values to variables
        split_sg_rules: Split inline SG rules to separate resources
        normalize_iam: Normalize IAM to standalone attachments
        skip_defaults: Skip default VPC/SG/etc
        managed_ids: Set of already-managed resource IDs to skip

    Returns:
        Configured CodifyPipeline
    """
    transformers: list[BaseCodifyTransformer] = [
        # ═══════════════════════════════════════════════════════════════════
        # STAGE 0: Schema Mapping (MUST BE FIRST)
        # ═══════════════════════════════════════════════════════════════════
        SchemaMapperTransformer(),
        # ═══════════════════════════════════════════════════════════════════
        # PHASE 1: Filtering (Stages 1-4)
        # ═══════════════════════════════════════════════════════════════════
        DefaultResourceFilter(skip_defaults=skip_defaults),
        GlobalResourceFilter(
            current_region=region,
            primary_region=primary_region,
            force_include_global=include_global,
        ),
        DataSourceFilter(convert_amis=convert_amis),
        ManagedResourceFilter(managed_ids=managed_ids),
        # ═══════════════════════════════════════════════════════════════════
        # PHASE 2: Structural (Stages 5-6)
        # ═══════════════════════════════════════════════════════════════════
        SecurityGroupSplitter(split_rules=split_sg_rules),
        IamAttachmentNormalizer(normalize_attachments=normalize_iam),
        # ═══════════════════════════════════════════════════════════════════
        # PHASE 3: Transformation (Stages 7-9)
        # ═══════════════════════════════════════════════════════════════════
        SecretsToVariableTransformer(extract_secrets=extract_secrets),
        MinimalNamingTransformer(),
        HardcodedIdToRefTransformer(),
        # ═══════════════════════════════════════════════════════════════════
        # PHASE 4: Safety & Generation (Stages 10-12)
        # ═══════════════════════════════════════════════════════════════════
        LifecycleProtector(protect_critical=protect_resources),
        ImportIDResolver(),
        # ═══════════════════════════════════════════════════════════════════
        # STAGE 12: Final Cleanup (MUST BE LAST - v3.7)
        # Removes dirty fields that leaked from earlier stages
        # ═══════════════════════════════════════════════════════════════════
        FinalCleanupTransformer(),
    ]

    return CodifyPipeline(transformers)
