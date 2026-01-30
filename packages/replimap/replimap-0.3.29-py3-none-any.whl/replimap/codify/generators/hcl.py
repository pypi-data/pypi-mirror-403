"""
HCL Renderer - Generate Terraform HCL resource blocks.

Renders resources to HCL format, organized by resource type
into logical files (vpc.tf, ec2.tf, rds.tf, etc.).

Supports HCL type markers for proper formatting:
- HCLBlock: Block syntax without '=' (e.g., `vpc_config { ... }`)
- HCLMap: Map syntax with '=' (e.g., `tags = { ... }`)
- HCLJsonEncode: jsonencode() function call
- HCLSet: Set of blocks with deterministic sorting
"""

from __future__ import annotations

import json
import logging
import re
from pathlib import Path
from typing import TYPE_CHECKING, Any

from replimap.codify.hcl_types import HCLBlock, HCLJsonEncode, HCLMap, HCLSet

if TYPE_CHECKING:
    from replimap.core.models import ResourceNode
    from replimap.core.unified_storage import GraphEngineAdapter

logger = logging.getLogger(__name__)


# Mapping of resource types to output files
FILE_MAPPING = {
    # Networking
    "aws_vpc": "vpc.tf",
    "aws_subnet": "vpc.tf",
    "aws_route_table": "networking.tf",
    "aws_route": "networking.tf",
    "aws_internet_gateway": "networking.tf",
    "aws_nat_gateway": "networking.tf",
    "aws_vpc_endpoint": "networking.tf",
    "aws_network_acl": "networking.tf",
    "aws_eip": "networking.tf",
    # Security
    "aws_security_group": "security_groups.tf",
    "aws_security_group_rule": "security_group_rules.tf",
    # Compute
    "aws_instance": "ec2.tf",
    "aws_launch_template": "compute.tf",
    "aws_autoscaling_group": "compute.tf",
    # Load Balancing
    "aws_lb": "alb.tf",
    "aws_lb_listener": "alb.tf",
    "aws_lb_target_group": "alb.tf",
    # Database
    "aws_db_instance": "rds.tf",
    "aws_rds_cluster": "rds.tf",
    "aws_db_subnet_group": "rds.tf",
    "aws_db_parameter_group": "rds.tf",
    "aws_elasticache_cluster": "elasticache.tf",
    "aws_elasticache_subnet_group": "elasticache.tf",
    # Storage
    "aws_s3_bucket": "s3.tf",
    "aws_s3_bucket_policy": "s3.tf",
    "aws_ebs_volume": "storage.tf",
    # Messaging
    "aws_sqs_queue": "messaging.tf",
    "aws_sns_topic": "messaging.tf",
    # IAM
    "aws_iam_role": "iam_roles.tf",
    "aws_iam_policy": "iam_policies.tf",
    "aws_iam_instance_profile": "iam_roles.tf",
    "aws_iam_role_policy": "iam_policies.tf",
    "aws_iam_role_policy_attachment": "iam_attachments.tf",
    "aws_iam_user_policy_attachment": "iam_attachments.tf",
    "aws_iam_group_policy_attachment": "iam_attachments.tf",
    "aws_iam_user_policy": "iam_policies.tf",
    "aws_iam_group_policy": "iam_policies.tf",
    # Monitoring
    "aws_cloudwatch_log_group": "monitoring.tf",
    "aws_cloudwatch_metric_alarm": "monitoring.tf",
}


class HclRenderer:
    """
    Render resources to Terraform HCL format.

    Generates properly formatted HCL resource blocks with:
    - Lifecycle protection for critical resources
    - References to other resources
    - Proper quoting and escaping
    - Logical file organization
    - Support for HCL type markers (HCLBlock, HCLJsonEncode, etc.)
    """

    def __init__(self) -> None:
        """Initialize the renderer."""
        self.file_contents: dict[str, list[str]] = {}
        self._rendered_count = 0

    def render(
        self,
        graph: GraphEngineAdapter,
        output_dir: Path,
    ) -> dict[str, Path]:
        """
        Render all resources to HCL files.

        Resources are sorted by (resource_type, terraform_name, id) for
        deterministic output. This ensures identical output for identical
        infrastructure, avoiding Git diff noise.

        Args:
            graph: The graph containing resources
            output_dir: Directory to write files

        Returns:
            Dictionary mapping filenames to their paths
        """
        self.file_contents = {}
        self._rendered_count = 0

        # Collect all resources first, then sort for deterministic output
        resources_to_render: list[tuple[str, str, str, str, ResourceNode]] = []

        for resource in graph.iter_resources():
            # v3.7.19: Skip phantom nodes (placeholders for missing resources)
            # and have no real configuration to render
            if getattr(resource, "is_phantom", False):
                logger.debug(f"Skipping phantom resource: {resource.id}")
                continue

            resource_type = self._get_terraform_type(resource)
            tf_name = resource.terraform_name or ""
            output_file = FILE_MAPPING.get(resource_type, "other.tf")

            # Store sort key and resource
            resources_to_render.append(
                (output_file, resource_type, tf_name, resource.id, resource)
            )

        # Sort by (output_file, resource_type, terraform_name, id) for deterministic output
        resources_to_render.sort(key=lambda x: (x[0], x[1], x[2], x[3]))

        # Render sorted resources
        for output_file, _rt, _tn, _rid, resource in resources_to_render:
            hcl = self._render_resource(resource)
            if hcl:
                if output_file not in self.file_contents:
                    self.file_contents[output_file] = [
                        "# Generated by RepliMap Codify",
                        "",
                    ]

                self.file_contents[output_file].append(hcl)
                self._rendered_count += 1

        # Write files (sort filenames for deterministic output)
        written_files: dict[str, Path] = {}
        for filename in sorted(self.file_contents.keys()):
            contents = self.file_contents[filename]
            file_path = output_dir / filename
            file_path.write_text("\n".join(contents))
            written_files[filename] = file_path
            logger.debug(f"Wrote {filename}")

        logger.info(f"HclRenderer: rendered {self._rendered_count} resources")
        return written_files

    def _get_terraform_type(self, resource: ResourceNode) -> str:
        """Get the Terraform type for a resource."""
        # Check for custom terraform type
        if "_terraform_type" in resource.config:
            return resource.config["_terraform_type"]
        return str(resource.resource_type)

    def _render_resource(self, resource: ResourceNode) -> str | None:
        """Render a single resource to HCL."""
        tf_type = self._get_terraform_type(resource)
        tf_name = resource.terraform_name

        if not tf_name:
            return None

        lines = [f'resource "{tf_type}" "{tf_name}" {{']

        # Render config attributes
        config = resource.config or {}

        # 🚨 v3.7.20 FIX: Include resource.tags in config if not already present
        # Tags are stored separately on ResourceNode.tags, not in config
        # Without this, tags are never rendered, causing Terraform plan to show
        # tags going to null
        #
        # ASG uses different tag format: tag blocks instead of tags map
        if tf_type == "aws_autoscaling_group":
            # Convert any tags map to tag blocks for ASG
            tags_to_convert = config.get("tags") or resource.tags
            if tags_to_convert and "tag" not in config:
                # Create new config without tags, add tag blocks instead
                config = {k: v for k, v in config.items() if k != "tags"}
                config["tag"] = self._convert_tags_to_asg_format(tags_to_convert)
        elif resource.tags and "tags" not in config:
            config = {**config, "tags": resource.tags}

        rendered_attrs = self._render_config(config, indent=2)
        lines.extend(rendered_attrs)

        # Add lifecycle block if needed
        if config.get("_lifecycle_prevent_destroy"):
            lines.extend(
                [
                    "",
                    "  lifecycle {",
                    "    prevent_destroy = true",
                    "  }",
                ]
            )

        lines.append("}")
        lines.append("")

        return "\n".join(lines)

    def _render_config(
        self,
        config: dict[str, Any],
        indent: int = 0,
    ) -> list[str]:
        """Render configuration attributes to HCL.

        Keys are sorted alphabetically for deterministic output.
        """
        lines: list[str] = []
        prefix = " " * indent

        # Skip internal attributes
        skip_keys = {
            "_lifecycle_prevent_destroy",
            "_import_id",
            "_terraform_type",
            "_parent_sg_id",
            "_parent_sg_name",
            "_parent_role_name",
            "_parent_user_name",
            "_parent_group_name",
            "_ami_todo",
        }

        # Sort keys for deterministic output
        for key in sorted(config.keys()):
            value = config[key]
            if key in skip_keys:
                continue

            # Handle TODO comments
            if key == "_ami_todo":
                lines.append(f"{prefix}{value}")
                continue

            # Use key as-is (schema mapper already handled conversion)
            tf_key = key

            # Note: None values are rendered as 'null' by _render_attribute()
            # This allows explicit null values in Terraform configs

            # Render based on type (including HCL type markers)
            lines.extend(self._render_attribute(tf_key, value, indent))

        return lines

    def _render_attribute(
        self,
        key: str,
        value: Any,
        indent: int = 0,
    ) -> list[str]:
        """Render a single attribute to HCL lines."""
        lines: list[str] = []
        prefix = " " * indent

        # Handle None/null first (before any type checks)
        if value is None:
            lines.append(f"{prefix}{key} = null")
            return lines

        # Handle HCL type markers first
        if isinstance(value, HCLBlock):
            # Block syntax: key { ... } (NO '=')
            lines.append(f"{prefix}{key} {{")
            # Sort keys for deterministic output
            for k in sorted(value.content.keys()):
                lines.extend(self._render_attribute(k, value.content[k], indent + 2))
            lines.append(f"{prefix}}}")

        elif isinstance(value, HCLMap):
            # Map syntax: key = { ... }
            lines.append(f"{prefix}{key} = {{")
            # Sort keys for deterministic output
            for k in sorted(value.content.keys()):
                rendered = self._render_scalar(value.content[k])
                escaped_key = self._quote_key(k)
                lines.append(f"{prefix}  {escaped_key} = {rendered}")
            lines.append(f"{prefix}}}")

        elif isinstance(value, HCLJsonEncode):
            # jsonencode syntax
            json_str = json.dumps(value.content, indent=2, sort_keys=True)
            json_lines = json_str.split("\n")

            if len(json_lines) == 1:
                lines.append(f"{prefix}{key} = jsonencode({json_str})")
            else:
                lines.append(f"{prefix}{key} = jsonencode(")
                for json_line in json_lines:
                    lines.append(f"{prefix}  {json_line}")
                lines.append(f"{prefix})")

        elif isinstance(value, HCLSet):
            # Set: render as sorted list of blocks
            sorted_items = value.sorted_items()
            for item in sorted_items:
                lines.append(f"{prefix}{key} {{")
                # Sort keys within each block for deterministic output
                for k in sorted(item.keys()):
                    lines.extend(self._render_attribute(k, item[k], indent + 2))
                lines.append(f"{prefix}}}")

        elif isinstance(value, bool):
            lines.append(f"{prefix}{key} = {str(value).lower()}")

        elif isinstance(value, (int, float)):
            lines.append(f"{prefix}{key} = {value}")

        elif isinstance(value, str):
            # Check if it's a reference (starts with ${)
            if value.startswith("${") and value.endswith("}"):
                # Strip ${} wrapper for Terraform 0.12+ bare references
                bare_ref = value[2:-1]
                lines.append(f"{prefix}{key} = {bare_ref}")
            else:
                escaped = self._escape_string(value)
                lines.append(f'{prefix}{key} = "{escaped}"')

        elif isinstance(value, list):
            if not value:
                return lines

            # Check if list of HCLBlocks (from SetSorter)
            if value and isinstance(value[0], HCLBlock):
                for item in value:
                    lines.append(f"{prefix}{key} {{")
                    # Sort keys for deterministic output
                    for k in sorted(item.content.keys()):
                        lines.extend(
                            self._render_attribute(k, item.content[k], indent + 2)
                        )
                    lines.append(f"{prefix}}}")
            # Check if list of strings
            elif all(isinstance(item, str) for item in value):
                rendered_items = []
                for item in value:
                    if item.startswith("${") and item.endswith("}"):
                        # Strip ${} wrapper for Terraform 0.12+ bare references
                        bare_ref = item[2:-1]
                        rendered_items.append(bare_ref)
                    else:
                        rendered_items.append(f'"{self._escape_string(item)}"')
                lines.append(f"{prefix}{key} = [{', '.join(rendered_items)}]")
            # Check if list of numbers
            elif all(isinstance(item, (int, float)) for item in value):
                items_str = ", ".join(str(i) for i in value)
                lines.append(f"{prefix}{key} = [{items_str}]")
            # List of dicts - render as repeated blocks
            elif all(isinstance(item, dict) for item in value):
                for item in value:
                    lines.append(f"{prefix}{key} {{")
                    # Sort keys for deterministic output
                    for k in sorted(item.keys()):
                        lines.extend(self._render_attribute(k, item[k], indent + 2))
                    lines.append(f"{prefix}}}")

        elif isinstance(value, dict):
            # Handle tags specially
            if key == "tags":
                if value:
                    lines.append(f"{prefix}tags = {{")
                    # Sort tag keys for deterministic output
                    for tag_key in sorted(value.keys()):
                        escaped_key = self._quote_key(tag_key)
                        escaped_value = self._escape_string(str(value[tag_key]))
                        lines.append(f'{prefix}  {escaped_key} = "{escaped_value}"')
                    lines.append(f"{prefix}}}")
            else:
                # Nested block
                lines.append(f"{prefix}{key} {{")
                # Sort keys for deterministic output
                for k in sorted(value.keys()):
                    lines.extend(self._render_attribute(k, value[k], indent + 2))
                lines.append(f"{prefix}}}")

        return lines

    def _render_scalar(self, value: Any) -> str:
        """Render a scalar value to HCL format."""
        if value is None:
            return "null"

        if isinstance(value, bool):
            return "true" if value else "false"

        if isinstance(value, (int, float)):
            return str(value)

        if isinstance(value, str):
            # Handle multiline
            if "\n" in value:
                return f"<<-EOT\n{value}\nEOT"
            # Escape quotes
            escaped = self._escape_string(value)
            return f'"{escaped}"'

        if isinstance(value, list):
            if not value:
                return "[]"
            items = [self._render_scalar(v) for v in value]
            if len(items) <= 3 and all(len(str(i)) < 30 for i in items):
                return f"[{', '.join(items)}]"
            return "[\n    " + ",\n    ".join(items) + ",\n  ]"

        if isinstance(value, dict):
            if not value:
                return "{}"
            # Sort keys for deterministic output
            items = [
                f"{k} = {self._render_scalar(value[k])}" for k in sorted(value.keys())
            ]
            if len(items) <= 2:
                return "{ " + ", ".join(items) + " }"
            return "{\n    " + "\n    ".join(items) + "\n  }"

        return str(value)

    def _escape_string(self, value: str) -> str:
        """Escape a string for HCL.

        Handles:
        - Backslashes, quotes, newlines, tabs
        - Terraform interpolation sequences (${} and %{})
          These are escaped as $${ and %%{ to prevent Terraform
          from interpreting them as variable references or
          template directives.
        """
        escaped = (
            value.replace("\\", "\\\\")
            .replace('"', '\\"')
            .replace("\n", "\\n")
            .replace("\r", "\\r")
            .replace("\t", "\\t")
        )
        # Escape Terraform interpolation sequences
        # ${} is for variable interpolation, %{} is for template directives
        # Must be done after other escaping to avoid double-escaping
        escaped = escaped.replace("${", "$${").replace("%{", "%%{")
        return escaped

    def _quote_key(self, key: str) -> str:
        """Quote a key if needed for HCL."""
        # Check if key is a valid identifier
        if key and (key[0].isalpha() or key[0] == "_"):
            if all(c.isalnum() or c in "_-" for c in key):
                return key
        # Quote it
        return f'"{self._escape_string(key)}"'

    def _to_snake_case(self, name: str) -> str:
        """Convert CamelCase to snake_case."""
        # Insert underscore before uppercase letters
        s1 = re.sub("(.)([A-Z][a-z]+)", r"\1_\2", name)
        return re.sub("([a-z0-9])([A-Z])", r"\1_\2", s1).lower()

    def _convert_tags_to_asg_format(self, tags: dict[str, str]) -> list[dict[str, Any]]:
        """
        Convert tags dict to ASG tag block format.

        ASG requires tag blocks like:
            tag {
                key                 = "Name"
                value               = "my-asg"
                propagate_at_launch = true
            }

        Tags are sorted by key for deterministic output.
        """
        # Sort by tag key for deterministic output
        return [
            {
                "key": key,
                "value": tags[key],
                "propagate_at_launch": True,
            }
            for key in sorted(tags.keys())
        ]

    @property
    def rendered_count(self) -> int:
        """Return the number of resources rendered."""
        return self._rendered_count
