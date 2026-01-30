"""
RepliMap Codify v4.1.1 - Brownfield Infrastructure Adoption.

Transform ClickOps AWS infrastructure into production-ready, safe,
maintainable Terraform code with zero risk of data loss.

Architecture:
    Stage 0 - Schema Mapping (MUST BE FIRST):
        SchemaMapperTransformer - 12-step AWS→Terraform schema mapping
        (GlobalFilter, WhitelistOverride, ResourceFilter, StructureFlattener,
         FieldRenamer, TransformApplier, TypeCaster, BlockMarker, DefaultPruner,
         EmptyPruner, TagNormalizer, SetSorter)

    Phase 1 - Filtering (Stages 1-4):
        1. DefaultResourceFilter - Skip default VPC/SG/RTB
        2. GlobalResourceFilter - Region-aware IAM/Route53
        3. DataSourceFilter - AMI → data source (conservative)
        4. ManagedResourceFilter - Skip TF-managed resources

    Phase 2 - Structural (Stages 5-6):
        5. SecurityGroupSplitter - Prevent cyclic dependencies
        6. IamAttachmentNormalizer - Non-destructive IAM

    Phase 3 - Transformation (Stages 7-9):
        7. SecretsToVariableTransformer - Bidirectional binding
        8. MinimalNamingTransformer - HCL-safe names
        9. HardcodedIdToRefTransformer - Context-aware replacement

    Phase 4 - Safety & Generation (Stages 10-12):
        10. LifecycleProtector - prevent_destroy for critical resources
        11. ImportIDResolver - Complex ID handling
        12. FinalCleanupTransformer - MUST BE LAST (v3.7+)
            Removes dirty fields, fixes matcher blocks, SQS conflicts

Usage:
    from replimap.codify import CodifyPipeline, get_codify_pipeline

    pipeline = get_codify_pipeline(region="us-east-1")
    graph = pipeline.execute(graph)

    from replimap.codify.generators import CodifyOutputGenerator
    generator = CodifyOutputGenerator(region="us-east-1")
    generator.generate(graph, output_dir)
"""

from __future__ import annotations

from .empty_pruner import EmptyPruner

# Output Generators
from .generators import CodifyOutputGenerator

# HCL Type Markers
from .hcl_types import HCLBlock, HCLJsonEncode, HCLMap, HCLSet

# Pipeline
from .pipeline import CodifyPipeline, get_codify_pipeline

# Stage 0 - Schema Mapping
from .schema_mapper import SchemaMapperTransformer
from .schema_rules import ResourceRules, SchemaRuleLoader
from .set_sorter import SetSorter

# Phase 4 - Cleanup (MUST BE LAST)
from .transformers.cleanup_transformer import FinalCleanupTransformer
from .transformers.data_source_filter import DataSourceFilter

# Phase 1 - Filtering
from .transformers.default_filter import DefaultResourceFilter
from .transformers.global_filter import GlobalResourceFilter
from .transformers.iam_normalizer import IamAttachmentNormalizer
from .transformers.import_resolver import ImportIDResolver

# Phase 4 - Safety
from .transformers.lifecycle_protector import LifecycleProtector
from .transformers.managed_filter import ManagedResourceFilter
from .transformers.naming_transformer import MinimalNamingTransformer
from .transformers.ref_transformer import HardcodedIdToRefTransformer

# Phase 3 - Transformation
from .transformers.secrets_transformer import SecretsToVariableTransformer

# Phase 2 - Structural
from .transformers.sg_splitter import SecurityGroupSplitter
from .transforms import (
    TransformConfig,
    TransformHandler,
    apply_transforms,
    transform_field,
)

# Utility classes
from .type_caster import TypeCaster

__all__ = [
    # Pipeline
    "CodifyPipeline",
    "get_codify_pipeline",
    # Stage 0 - Schema Mapping
    "SchemaMapperTransformer",
    "SchemaRuleLoader",
    "ResourceRules",
    # HCL Type Markers
    "HCLBlock",
    "HCLMap",
    "HCLJsonEncode",
    "HCLSet",
    # Utility Classes
    "TypeCaster",
    "EmptyPruner",
    "SetSorter",
    # Transforms (v3.1)
    "TransformConfig",
    "TransformHandler",
    "apply_transforms",
    "transform_field",
    # Phase 1 - Filtering
    "DefaultResourceFilter",
    "GlobalResourceFilter",
    "DataSourceFilter",
    "ManagedResourceFilter",
    # Phase 2 - Structural
    "SecurityGroupSplitter",
    "IamAttachmentNormalizer",
    # Phase 3 - Transformation
    "SecretsToVariableTransformer",
    "MinimalNamingTransformer",
    "HardcodedIdToRefTransformer",
    # Phase 4 - Safety
    "LifecycleProtector",
    "ImportIDResolver",
    # Phase 4 - Cleanup (MUST BE LAST in pipeline)
    "FinalCleanupTransformer",
    # Generators
    "CodifyOutputGenerator",
]
