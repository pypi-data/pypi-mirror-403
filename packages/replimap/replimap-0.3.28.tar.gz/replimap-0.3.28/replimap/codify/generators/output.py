"""
Codify Output Generator - Orchestrates all output generation.

Generates:
- *.tf files (production-ready HCL)
- imports.sh / imports.tf (plan-appropriate)
- README.md (dynamic operation guide)
- variables.tf (extracted variables)
- secrets.tfvars.example (template for secrets)
"""

from __future__ import annotations

import logging
import shutil
import subprocess
from pathlib import Path
from typing import TYPE_CHECKING, Any

from .backend import BackendGenerator
from .hcl import HclRenderer
from .imports import ImportGenerator
from .readme import ReadmeGenerator
from .variables import VariablesGenerator

if TYPE_CHECKING:
    from replimap.core.unified_storage import GraphEngineAdapter

logger = logging.getLogger(__name__)


class CodifyOutputGenerator:
    """
    Main output generator for codify command.

    Orchestrates all sub-generators to produce complete,
    production-ready Terraform code from the processed graph.
    """

    def __init__(
        self,
        region: str,
        use_import_blocks: bool = True,
        run_terraform_fmt: bool = True,
    ) -> None:
        """
        Initialize the generator.

        Args:
            region: AWS region for provider configuration
            use_import_blocks: Use TF 1.5+ import blocks (vs shell script)
            run_terraform_fmt: Run terraform fmt on generated files
        """
        self.region = region
        self.use_import_blocks = use_import_blocks
        self.run_terraform_fmt = run_terraform_fmt

        # Sub-generators
        self.hcl = HclRenderer()
        self.backend = BackendGenerator()
        self.imports = ImportGenerator()
        self.readme = ReadmeGenerator()
        self.variables = VariablesGenerator()

    def generate(
        self,
        graph: GraphEngineAdapter,
        output_dir: Path,
    ) -> dict[str, Path]:
        """
        Generate all output files.

        Args:
            graph: The processed graph
            output_dir: Directory to write files

        Returns:
            Dictionary mapping filenames to their paths
        """
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        written_files: dict[str, Path] = {}

        # Collect statistics for README
        stats: dict[str, Any] = {
            "total_resources": 0,
            "protected_resources": 0,
            "extracted_variables": 0,
            "region": self.region,
        }

        # 1. Generate HCL resource files
        logger.info("Generating HCL resource files...")
        hcl_files = self.hcl.render(graph, output_dir)
        written_files.update(hcl_files)
        stats["total_resources"] = sum(
            len(resources) for resources in self.hcl.file_contents.values()
        )

        # 2. Generate backend.tf
        logger.info("Generating backend.tf...")
        backend_file = self.backend.generate(output_dir, self.region)
        written_files["backend.tf"] = backend_file

        # 3. Generate data.tf (if we have data sources)
        data_sources = graph.get_metadata("codify_data_sources") or []
        if data_sources:
            logger.info("Generating data.tf...")
            data_file = self._generate_data_sources(data_sources, output_dir)
            written_files["data.tf"] = data_file

        # 4. Generate variables.tf
        logger.info("Generating variables.tf...")
        extracted_vars = graph.get_metadata("codify_variables") or []
        stats["extracted_variables"] = len(extracted_vars)
        variables_file = self.variables.generate(
            extracted_vars, output_dir, self.region
        )
        written_files["variables.tf"] = variables_file

        # 5. Generate secrets.tfvars.example
        if extracted_vars:
            logger.info("Generating secrets.tfvars.example...")
            secrets_file = self._generate_secrets_template(extracted_vars, output_dir)
            written_files["secrets.tfvars.example"] = secrets_file

        # 6. Generate imports (either imports.tf or imports.sh)
        logger.info("Generating import commands...")
        protected_resources = graph.get_metadata("codify_protected_resources") or []
        stats["protected_resources"] = len(protected_resources)

        if self.use_import_blocks:
            import_file = self.imports.generate_import_tf(graph, output_dir)
            written_files["imports.tf"] = import_file
        else:
            import_file = self.imports.generate_import_sh(graph, output_dir)
            written_files["imports.sh"] = import_file

        # 7. Generate README.md
        logger.info("Generating README.md...")
        readme_file = self.readme.generate(
            output_dir=output_dir,
            stats=stats,
            use_import_blocks=self.use_import_blocks,
        )
        written_files["README.md"] = readme_file

        # 8. Run terraform fmt
        if self.run_terraform_fmt:
            self._run_terraform_fmt(output_dir)

        logger.info(f"Generated {len(written_files)} files in {output_dir}")
        return written_files

    def _generate_data_sources(
        self,
        data_sources: list[dict[str, Any]],
        output_dir: Path,
    ) -> Path:
        """Generate data.tf with AMI data sources."""
        lines = [
            "# Generated by RepliMap Codify",
            "# Data sources for dynamic resource lookup",
            "",
        ]

        for ds in data_sources:
            lines.extend(
                [
                    f"# {ds.get('description', 'AMI data source')}",
                    f"# Original AMI: {ds.get('original_ami', 'unknown')}",
                    f'data "aws_ami" "{ds["name"]}" {{',
                    "  most_recent = true",
                    f'  owners      = ["{ds["owner"]}"]',
                    "",
                    "  filter {",
                    '    name   = "name"',
                    f'    values = ["{ds["pattern"]}"]',
                    "  }",
                    "",
                    "  filter {",
                    '    name   = "virtualization-type"',
                    '    values = ["hvm"]',
                    "  }",
                    "}",
                    "",
                ]
            )

        file_path = output_dir / "data.tf"
        file_path.write_text("\n".join(lines))
        return file_path

    def _generate_secrets_template(
        self,
        variables: list[dict[str, Any]],
        output_dir: Path,
    ) -> Path:
        """Generate secrets.tfvars.example template."""
        lines = [
            "# =============================================================================",
            "# Secrets Template - Generated by RepliMap Codify",
            "# =============================================================================",
            "#",
            "# Copy this file to secrets.tfvars and fill in the actual values.",
            "# Add secrets.tfvars to .gitignore!",
            "#",
            "# Usage:",
            "#   cp secrets.tfvars.example secrets.tfvars",
            "#   # Edit secrets.tfvars with actual values",
            "#   terraform plan -var-file=secrets.tfvars",
            "#",
            "# =============================================================================",
            "",
        ]

        for var in variables:
            if var.get("sensitive"):
                lines.append(f"# {var.get('description', '')}")
                lines.append(f'{var["name"]} = ""  # FILL IN')
                lines.append("")

        file_path = output_dir / "secrets.tfvars.example"
        file_path.write_text("\n".join(lines))
        return file_path

    def _run_terraform_fmt(self, output_dir: Path) -> bool:
        """Run terraform fmt on the output directory."""
        terraform_path = shutil.which("terraform")
        if not terraform_path:
            logger.warning("terraform not found in PATH - skipping format step")
            return True

        try:
            result = subprocess.run(
                ["terraform", "fmt", "-recursive"],
                cwd=output_dir,
                capture_output=True,
                text=True,
                timeout=30,
            )

            if result.returncode == 0:
                if result.stdout.strip():
                    formatted = result.stdout.strip().split("\n")
                    logger.info(f"terraform fmt: formatted {len(formatted)} file(s)")
                return True
            else:
                logger.warning(f"terraform fmt failed: {result.stderr.strip()}")
                return False

        except subprocess.TimeoutExpired:
            logger.warning("terraform fmt timed out")
            return False
        except Exception as e:
            logger.warning(f"terraform fmt error: {e}")
            return False
