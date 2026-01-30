"""
Security Group Splitter - Prevents cyclic dependency import failures.

CRITICAL: AWS Security Groups often have circular references.
If we generate inline ingress/egress blocks, Terraform will fail to import.

SOLUTION: Always generate aws_security_group_rule as SEPARATE resources.

Before:
  aws_security_group "web" {
    ingress { from_port = 22 ... }  # Inline
  }

After:
  aws_security_group "web" { }  # Empty

  aws_security_group_rule "web_ingress_ssh" {
    security_group_id = aws_security_group.web.id
    ...
  }
"""

from __future__ import annotations

import logging
import uuid
from typing import TYPE_CHECKING, Any

from replimap.core.models import ResourceNode, ResourceType

from .base import BaseCodifyTransformer

if TYPE_CHECKING:
    from replimap.core.unified_storage import GraphEngineAdapter

logger = logging.getLogger(__name__)


class SecurityGroupSplitter(BaseCodifyTransformer):
    """
    Split inline security group rules into standalone resources.

    This prevents cyclic dependency issues during import. When security
    groups reference each other (e.g., web SG allows traffic from app SG,
    and app SG allows traffic from web SG), inline rules cause circular
    dependencies that Terraform cannot import.

    By splitting rules into separate aws_security_group_rule resources,
    we break the cycle and enable successful import.
    """

    name = "SecurityGroupSplitter"

    def __init__(self, split_rules: bool = True) -> None:
        """
        Initialize the splitter.

        Args:
            split_rules: Whether to split inline rules into separate resources
        """
        self.split_rules = split_rules
        self._rules_created = 0

    def transform(self, graph: GraphEngineAdapter) -> GraphEngineAdapter:
        """
        Split inline SG rules into standalone rule resources.

        Args:
            graph: The graph to transform

        Returns:
            The transformed graph
        """
        if not self.split_rules:
            logger.debug("SecurityGroupSplitter: splitting disabled")
            return graph

        self._rules_created = 0
        new_resources: list[ResourceNode] = []

        for resource in graph.iter_resources():
            if str(resource.resource_type) != "aws_security_group":
                continue

            config = resource.config or {}

            # Extract ingress rules
            ingress_rules = config.pop("IpPermissions", [])
            for i, rule in enumerate(ingress_rules):
                rule_resources = self._create_rule_resources(
                    resource, rule, "ingress", i
                )
                new_resources.extend(rule_resources)

            # Extract egress rules
            egress_rules = config.pop("IpPermissionsEgress", [])
            for i, rule in enumerate(egress_rules):
                rule_resources = self._create_rule_resources(
                    resource, rule, "egress", i
                )
                new_resources.extend(rule_resources)

        # Add all new rule resources to graph
        for rule_resource in new_resources:
            graph.add_resource(rule_resource)
            self._rules_created += 1

        if self._rules_created > 0:
            logger.info(
                f"SecurityGroupSplitter: created {self._rules_created} "
                "standalone rule resources"
            )

        return graph

    def _create_rule_resources(
        self,
        sg: ResourceNode,
        rule: dict[str, Any],
        direction: str,
        index: int,
    ) -> list[ResourceNode]:
        """
        Create standalone security group rule resources.

        A single AWS rule may expand to multiple Terraform rules because:
        - AWS allows multiple CIDR blocks per rule
        - AWS allows multiple source SGs per rule
        - Terraform requires one rule per source
        """
        resources: list[ResourceNode] = []

        from_port = rule.get("FromPort", 0)
        to_port = rule.get("ToPort", 0)
        protocol = rule.get("IpProtocol", "-1")

        # Handle -1 protocol (all traffic)
        if protocol == "-1":
            from_port = 0
            to_port = 0

        # Generate base rule name
        port_desc = self._get_port_description(from_port, to_port, protocol)
        base_name = f"{sg.terraform_name}_{direction}_{port_desc}"

        # Create rules for IPv4 CIDR blocks
        ipv4_ranges = rule.get("IpRanges", [])
        for cidr_info in ipv4_ranges:
            cidr = cidr_info.get("CidrIp", "0.0.0.0/0")
            cidr_suffix = cidr.replace(".", "_").replace("/", "_")
            rule_name = f"{base_name}_cidr_{cidr_suffix}"

            rule_resource = self._create_rule_resource(
                sg=sg,
                direction=direction,
                protocol=protocol,
                from_port=from_port,
                to_port=to_port,
                cidr_ipv4=cidr,
                description=cidr_info.get("Description"),
                name=rule_name,
            )
            resources.append(rule_resource)

        # Create rules for IPv6 CIDR blocks
        ipv6_ranges = rule.get("Ipv6Ranges", [])
        for cidr_info in ipv6_ranges:
            cidr = cidr_info.get("CidrIpv6", "::/0")
            cidr_suffix = cidr.replace(":", "_").replace("/", "_")
            rule_name = f"{base_name}_cidr6_{cidr_suffix}"

            rule_resource = self._create_rule_resource(
                sg=sg,
                direction=direction,
                protocol=protocol,
                from_port=from_port,
                to_port=to_port,
                cidr_ipv6=cidr,
                description=cidr_info.get("Description"),
                name=rule_name,
            )
            resources.append(rule_resource)

        # Create rules for source security groups
        source_sgs = rule.get("UserIdGroupPairs", [])
        for sg_pair in source_sgs:
            source_sg_id = sg_pair.get("GroupId", "")
            if not source_sg_id:
                continue

            sg_suffix = source_sg_id.replace("sg-", "")
            rule_name = f"{base_name}_sg_{sg_suffix}"

            rule_resource = self._create_rule_resource(
                sg=sg,
                direction=direction,
                protocol=protocol,
                from_port=from_port,
                to_port=to_port,
                source_sg_id=source_sg_id,
                description=sg_pair.get("Description"),
                name=rule_name,
            )
            resources.append(rule_resource)

        # Create rules for prefix lists
        prefix_lists = rule.get("PrefixListIds", [])
        for pl_info in prefix_lists:
            pl_id = pl_info.get("PrefixListId", "")
            if not pl_id:
                continue

            pl_suffix = pl_id.replace("pl-", "")
            rule_name = f"{base_name}_pl_{pl_suffix}"

            rule_resource = self._create_rule_resource(
                sg=sg,
                direction=direction,
                protocol=protocol,
                from_port=from_port,
                to_port=to_port,
                prefix_list_id=pl_id,
                description=pl_info.get("Description"),
                name=rule_name,
            )
            resources.append(rule_resource)

        # If no specific sources, create a rule for 0.0.0.0/0
        if not resources and direction == "egress":
            rule_resource = self._create_rule_resource(
                sg=sg,
                direction=direction,
                protocol=protocol,
                from_port=from_port,
                to_port=to_port,
                cidr_ipv4="0.0.0.0/0",
                description=None,
                name=f"{base_name}_all",
            )
            resources.append(rule_resource)

        return resources

    def _create_rule_resource(
        self,
        sg: ResourceNode,
        direction: str,
        protocol: str,
        from_port: int,
        to_port: int,
        cidr_ipv4: str | None = None,
        cidr_ipv6: str | None = None,
        source_sg_id: str | None = None,
        prefix_list_id: str | None = None,
        description: str | None = None,
        name: str = "",
    ) -> ResourceNode:
        """Create a single security group rule resource."""
        # Generate unique ID
        rule_id = f"sgrule-{uuid.uuid4().hex[:12]}"

        config: dict[str, Any] = {
            "security_group_id": sg.id,
            "type": direction,
            "protocol": protocol,
            "from_port": from_port,
            "to_port": to_port,
            # Store parent SG reference for ref transformer
            "_parent_sg_id": sg.id,
            "_parent_sg_name": sg.terraform_name,
        }

        if cidr_ipv4:
            config["cidr_blocks"] = [cidr_ipv4]
        if cidr_ipv6:
            config["ipv6_cidr_blocks"] = [cidr_ipv6]
        if source_sg_id:
            config["source_security_group_id"] = source_sg_id
        if prefix_list_id:
            config["prefix_list_ids"] = [prefix_list_id]
        if description:
            config["description"] = description

        # Use UNKNOWN type for now - we'll add proper type support
        return ResourceNode(
            id=rule_id,
            resource_type=ResourceType.UNKNOWN,  # Will be rendered as aws_security_group_rule
            region=sg.region,
            config=config,
            tags=sg.tags.copy(),
            terraform_name=name,
            original_name=name,
        )

    def _get_port_description(self, from_port: int, to_port: int, protocol: str) -> str:
        """Generate a descriptive port string for naming."""
        if protocol == "-1":
            return "all"
        if from_port == to_port:
            if from_port == 22:
                return "ssh"
            if from_port == 80:
                return "http"
            if from_port == 443:
                return "https"
            if from_port == 3306:
                return "mysql"
            if from_port == 5432:
                return "postgres"
            if from_port == 6379:
                return "redis"
            return f"{protocol}_{from_port}"
        return f"{protocol}_{from_port}_{to_port}"

    @property
    def rules_created(self) -> int:
        """Return the number of rule resources created."""
        return self._rules_created
