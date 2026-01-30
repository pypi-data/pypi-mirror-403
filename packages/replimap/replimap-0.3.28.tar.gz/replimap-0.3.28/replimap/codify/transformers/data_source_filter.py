"""
Data Source Filter - CONSERVATIVE AMI STRATEGY.

RULE: Only convert AMIs to data sources if we are CONFIDENT about the source.

Known Safe Owners:
- 137112412989: Amazon
- 099720109477: Canonical (Ubuntu)
- 136693071363: Debian
- 309956199498: Red Hat
- 801119661308: Amazon (Windows)

Unknown owners: Keep hardcoded + add TODO comment.

Philosophy: Working code with TODOs > broken data sources.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any

from .base import BaseCodifyTransformer

if TYPE_CHECKING:
    from replimap.core.unified_storage import GraphEngineAdapter

logger = logging.getLogger(__name__)


# Known safe AMI owners and their patterns
AMI_PATTERNS = [
    {
        "name": "amazon_linux_2023",
        "owner": "137112412989",
        "pattern": "al2023-ami-*-x86_64",
        "description": "Amazon Linux 2023",
    },
    {
        "name": "amazon_linux_2",
        "owner": "137112412989",
        "pattern": "amzn2-ami-hvm-*-x86_64-gp2",
        "description": "Amazon Linux 2",
    },
    {
        "name": "ubuntu_24_04",
        "owner": "099720109477",
        "pattern": "ubuntu/images/hvm-ssd-gp3/ubuntu-noble-24.04-amd64-server-*",
        "description": "Ubuntu 24.04 LTS",
    },
    {
        "name": "ubuntu_22_04",
        "owner": "099720109477",
        "pattern": "ubuntu/images/hvm-ssd/ubuntu-jammy-22.04-amd64-server-*",
        "description": "Ubuntu 22.04 LTS",
    },
    {
        "name": "ubuntu_20_04",
        "owner": "099720109477",
        "pattern": "ubuntu/images/hvm-ssd/ubuntu-focal-20.04-amd64-server-*",
        "description": "Ubuntu 20.04 LTS",
    },
    {
        "name": "debian_12",
        "owner": "136693071363",
        "pattern": "debian-12-amd64-*",
        "description": "Debian 12",
    },
    {
        "name": "rhel_9",
        "owner": "309956199498",
        "pattern": "RHEL-9*_HVM-*-x86_64-*",
        "description": "Red Hat Enterprise Linux 9",
    },
    {
        "name": "windows_2022",
        "owner": "801119661308",
        "pattern": "Windows_Server-2022-English-Full-Base-*",
        "description": "Windows Server 2022",
    },
]

KNOWN_SAFE_OWNERS = {
    "137112412989",  # Amazon
    "099720109477",  # Canonical
    "136693071363",  # Debian
    "309956199498",  # Red Hat
    "801119661308",  # Amazon (Windows)
    "amazon",  # Alias for Amazon
}


class DataSourceFilter(BaseCodifyTransformer):
    """
    Convert known-safe AMIs to data sources.

    For brownfield adoption, hardcoded AMI IDs are problematic:
    - They're region-specific
    - They may be deprecated or unavailable
    - They don't receive security updates

    This transformer converts KNOWN-SAFE AMIs to data sources that
    dynamically fetch the latest version. Unknown AMIs are kept
    hardcoded with TODO comments for safety.
    """

    name = "DataSourceFilter"

    def __init__(
        self,
        convert_amis: bool = True,
        ami_metadata: dict[str, dict[str, Any]] | None = None,
    ) -> None:
        """
        Initialize the filter.

        Args:
            convert_amis: Whether to convert AMIs to data sources
            ami_metadata: Optional metadata about AMIs (owner, name, etc.)
        """
        self.convert_amis = convert_amis
        self.ami_metadata = ami_metadata or {}
        self.generated_data_sources: list[dict[str, Any]] = []
        self._converted_count = 0
        self._skipped_count = 0

    def transform(self, graph: GraphEngineAdapter) -> GraphEngineAdapter:
        """
        Convert known-safe AMIs to data source references.

        Args:
            graph: The graph to transform

        Returns:
            The transformed graph
        """
        if not self.convert_amis:
            logger.debug("DataSourceFilter: AMI conversion disabled")
            return graph

        self.generated_data_sources = []
        self._converted_count = 0
        self._skipped_count = 0

        # Track which AMI data sources we've already created
        created_data_sources: set[str] = set()

        for resource in graph.iter_resources():
            resource_type = str(resource.resource_type)
            if resource_type not in ("aws_instance", "aws_launch_template"):
                continue

            # Get AMI ID from config (different key names)
            ami_id = (
                resource.config.get("ImageId")
                or resource.config.get("ami")
                or resource.config.get("image_id")
            )
            if not ami_id or not ami_id.startswith("ami-"):
                continue

            ami_meta = self.ami_metadata.get(ami_id, {})

            if self._should_convert_ami(ami_id, ami_meta):
                data_source = self._create_ami_data_source(ami_id, ami_meta)
                if data_source and data_source["name"] not in created_data_sources:
                    self.generated_data_sources.append(data_source)
                    created_data_sources.add(data_source["name"])

                    # Update resource to reference data source
                    ami_key = "ami" if "ami" in resource.config else "image_id"
                    resource.config[ami_key] = (
                        f"${{data.aws_ami.{data_source['name']}.id}}"
                    )
                    self._converted_count += 1
                    logger.debug(
                        f"Converted AMI {ami_id} to data source {data_source['name']}"
                    )
            else:
                # Keep hardcoded but add TODO comment for manual review
                resource.config["_ami_todo"] = (
                    f"# TODO: Verify AMI source (current: {ami_id})\n"
                    f"# Consider converting to data source if this is a standard OS image"
                )
                self._skipped_count += 1
                logger.debug(f"Kept hardcoded AMI {ami_id} (unknown source)")

        # Store generated data sources in graph metadata
        graph.set_metadata("codify_data_sources", self.generated_data_sources)

        if self._converted_count > 0 or self._skipped_count > 0:
            logger.info(
                f"DataSourceFilter: converted {self._converted_count} AMIs, "
                f"kept {self._skipped_count} hardcoded"
            )

        return graph

    def _should_convert_ami(self, ami_id: str, ami_meta: dict[str, Any]) -> bool:
        """
        Determine if an AMI should be converted to a data source.

        Only convert if we're confident about the source.
        """
        owner = ami_meta.get("OwnerId", "")
        return owner in KNOWN_SAFE_OWNERS

    def _create_ami_data_source(
        self, ami_id: str, ami_meta: dict[str, Any]
    ) -> dict[str, Any] | None:
        """
        Create a data source definition for an AMI.

        Returns None if we can't determine the appropriate pattern.
        """
        owner = ami_meta.get("OwnerId", "")

        for pattern in AMI_PATTERNS:
            if pattern["owner"] == owner:
                return {
                    "name": pattern["name"],
                    "owner": pattern["owner"],
                    "pattern": pattern["pattern"],
                    "description": pattern["description"],
                    "original_ami": ami_id,
                }

        return None

    @property
    def converted_count(self) -> int:
        """Return the number of AMIs converted to data sources."""
        return self._converted_count

    @property
    def skipped_count(self) -> int:
        """Return the number of AMIs kept hardcoded."""
        return self._skipped_count
