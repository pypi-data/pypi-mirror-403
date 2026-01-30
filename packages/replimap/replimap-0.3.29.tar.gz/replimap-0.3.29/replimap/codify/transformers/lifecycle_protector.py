"""
Lifecycle Protector - The "Do No Harm" Rule.

CRITICAL: During infrastructure adoption, generated code may not be perfectly
accurate. If Terraform decides a resource must be REPLACED, this could cause:
  - Data loss (RDS, S3, DynamoDB)
  - Service outage (EC2, ELB)

SOLUTION: Add lifecycle { prevent_destroy = true } to all critical resources.

This creates a safety net: even if generated code has issues, Terraform will
refuse to destroy production resources.

Philosophy: Fail safe, not dangerous.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from .base import BaseCodifyTransformer

if TYPE_CHECKING:
    from replimap.core.unified_storage import GraphEngineAdapter

logger = logging.getLogger(__name__)


# Resource types that contain critical/stateful data
CRITICAL_RESOURCES = {
    # Databases
    "aws_db_instance",
    "aws_rds_cluster",
    "aws_rds_cluster_instance",
    "aws_elasticache_cluster",
    "aws_elasticache_replication_group",
    "aws_dynamodb_table",
    "aws_opensearch_domain",
    "aws_redshift_cluster",
    "aws_docdb_cluster",
    "aws_neptune_cluster",
    # Storage
    "aws_s3_bucket",
    "aws_efs_file_system",
    "aws_fsx_lustre_file_system",
    "aws_fsx_windows_file_system",
    "aws_ebs_volume",
    # Security
    "aws_kms_key",
    "aws_secretsmanager_secret",
    "aws_ssm_parameter",  # If sensitive
    # Certificates
    "aws_acm_certificate",
    # Other stateful
    "aws_kinesis_stream",
    "aws_kinesis_firehose_delivery_stream",
    "aws_sqs_queue",  # If FIFO with deduplication
}


class LifecycleProtector(BaseCodifyTransformer):
    """
    Add lifecycle protection to critical resources.

    Adds `lifecycle { prevent_destroy = true }` to resources that contain
    stateful data (databases, storage, etc.). This prevents accidental
    destruction during infrastructure adoption when the generated code
    may not perfectly match the actual configuration.
    """

    name = "LifecycleProtector"

    def __init__(
        self,
        protect_critical: bool = True,
        additional_protected: set[str] | None = None,
    ) -> None:
        """
        Initialize the protector.

        Args:
            protect_critical: Whether to add lifecycle protection
            additional_protected: Additional resource types to protect
        """
        self.protect_critical = protect_critical
        self.protected_types = CRITICAL_RESOURCES.copy()
        if additional_protected:
            self.protected_types.update(additional_protected)
        self._protected_count = 0

    def transform(self, graph: GraphEngineAdapter) -> GraphEngineAdapter:
        """
        Add lifecycle protection to critical resources.

        Args:
            graph: The graph to transform

        Returns:
            The transformed graph
        """
        if not self.protect_critical:
            logger.debug("LifecycleProtector: protection disabled")
            return graph

        self._protected_count = 0
        protected_resources: list[str] = []

        for resource in graph.iter_resources():
            resource_type = str(resource.resource_type)

            if resource_type in self.protected_types:
                # Add lifecycle flag to config
                resource.config["_lifecycle_prevent_destroy"] = True
                self._protected_count += 1
                protected_resources.append(f"{resource_type}.{resource.terraform_name}")

        # Store protected resources in metadata for reporting
        graph.set_metadata("codify_protected_resources", protected_resources)

        if self._protected_count > 0:
            logger.info(
                f"LifecycleProtector: protected {self._protected_count} critical resources"
            )

        return graph

    @property
    def protected_count(self) -> int:
        """Return the number of protected resources."""
        return self._protected_count
