"""
Codify Transformers - Multi-stage pipeline for brownfield adoption.

Each transformer processes the graph in sequence, preparing resources
for safe Terraform import and code generation.

v3.7: Added FinalCleanupTransformer as the last stage to remove dirty fields.
"""

from __future__ import annotations

from .cleanup_transformer import FinalCleanupTransformer
from .data_source_filter import DataSourceFilter
from .default_filter import DefaultResourceFilter
from .global_filter import GlobalResourceFilter
from .iam_normalizer import IamAttachmentNormalizer
from .import_resolver import ImportIDResolver
from .lifecycle_protector import LifecycleProtector
from .managed_filter import ManagedResourceFilter
from .naming_transformer import MinimalNamingTransformer
from .ref_transformer import HardcodedIdToRefTransformer
from .secrets_transformer import SecretsToVariableTransformer
from .sg_splitter import SecurityGroupSplitter

__all__ = [
    "DefaultResourceFilter",
    "GlobalResourceFilter",
    "DataSourceFilter",
    "ManagedResourceFilter",
    "SecurityGroupSplitter",
    "IamAttachmentNormalizer",
    "SecretsToVariableTransformer",
    "MinimalNamingTransformer",
    "HardcodedIdToRefTransformer",
    "LifecycleProtector",
    "ImportIDResolver",
    "FinalCleanupTransformer",
]
