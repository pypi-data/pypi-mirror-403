"""
Codify command - Transform ClickOps AWS infrastructure into Terraform code.

V4.1 Brownfield Infrastructure Adoption:
- 11-stage transformation pipeline
- Production-ready, safe, maintainable Terraform code
- Zero risk of data loss with lifecycle protection

V3 Architecture:
- Uses @enhanced_cli_error_handler for structured error handling
- Uses ctx.obj.output for stdout hygiene (stderr for progress, stdout for results)
- JSON mode available via global --format flag
"""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

import typer

from replimap import __version__
from replimap.cli.errors import enhanced_cli_error_handler
from replimap.cli.utils import (
    get_aws_session,
    resolve_effective_region,
)

if TYPE_CHECKING:
    from replimap.cli.context import GlobalContext


def register(app: typer.Typer, panel: str | None = None) -> None:
    """Register the codify command with the app."""

    @app.command(rich_help_panel=panel)
    @enhanced_cli_error_handler
    def codify(
        ctx: typer.Context,
        # === Common Options ===
        profile: str | None = typer.Option(
            None,
            "--profile",
            "-p",
            help="AWS source profile name",
        ),
        region: str | None = typer.Option(
            None,
            "--region",
            "-r",
            help="AWS region to scan (uses profile's region or us-east-1)",
        ),
        output_dir: Path = typer.Option(
            Path("./terraform"),
            "--output-dir",
            "-o",
            help="Output directory for generated files",
        ),
        output_format: str | None = typer.Option(
            None,
            "--format",
            "-f",
            help="Output format: text, json, table, quiet (overrides global)",
        ),
        # === Terraform Generation Options ===
        primary_region: str | None = typer.Option(
            None,
            "--primary-region",
            help="Region where global resources (IAM, Route53) should be defined",
            rich_help_panel="Terraform Generation",
        ),
        include_global: bool = typer.Option(
            False,
            "--include-global",
            help="Force include global resources regardless of region",
            rich_help_panel="Terraform Generation",
        ),
        no_lifecycle_protection: bool = typer.Option(
            False,
            "--no-lifecycle-protection",
            help="Disable lifecycle { prevent_destroy = true } on critical resources",
            rich_help_panel="Terraform Generation",
        ),
        use_import_script: bool = typer.Option(
            False,
            "--use-import-script",
            help="Generate imports.sh instead of imports.tf (for Terraform < 1.5)",
            rich_help_panel="Terraform Generation",
        ),
        skip_defaults: bool = typer.Option(
            True,
            "--skip-defaults/--no-skip-defaults",
            help="Skip default VPC, security groups, etc.",
            rich_help_panel="Terraform Generation",
        ),
        state_file: str | None = typer.Option(
            None,
            "--state-file",
            help="Path to existing terraform.tfstate to skip already-managed resources",
            rich_help_panel="Terraform Generation",
        ),
        # === Cache & Performance ===
        dry_run: bool = typer.Option(
            False,
            "--dry-run",
            help="Show what would be generated without writing files",
            rich_help_panel="Cache & Performance",
        ),
        no_cache: bool = typer.Option(
            False,
            "--no-cache",
            help="Don't use cached credentials (re-authenticate)",
            rich_help_panel="Cache & Performance",
        ),
        refresh: bool = typer.Option(
            False,
            "--refresh",
            "-R",
            help="Force fresh AWS scan (ignore cached graph)",
            rich_help_panel="Cache & Performance",
        ),
    ) -> None:
        """Transform ClickOps AWS infrastructure into production-ready Terraform code.

        \b
        RepliMap Codify generates safe, maintainable Terraform code from your
        existing AWS infrastructure. It includes lifecycle protection for critical
        resources and handles complex import scenarios automatically.

        \b
        Features:
        - 11-stage transformation pipeline
        - Lifecycle protection for databases, storage, etc.
        - Security group rule splitting (prevents cyclic deps)
        - Non-destructive IAM (standalone attachments)
        - Context-aware reference replacement
        - Terraform 1.5+ import block generation

        \b
        Examples:
            # Basic usage
            replimap codify -p prod -r us-east-1 -o ./terraform
        \b
            # Skip lifecycle protection (for dev environments)
            replimap codify -p prod -r us-east-1 --no-lifecycle-protection
        \b
            # Skip already-managed resources
            replimap codify -p prod -r us-east-1 --state-file ./terraform.tfstate
        \b
            # Force include global resources (IAM, Route53) in non-primary region
            replimap codify -p prod -r eu-west-1 --include-global
        \b
            # Dry run to preview what would be generated
            replimap codify -p prod -r us-east-1 --dry-run
        """
        from replimap.cli.context import GlobalContext
        from replimap.cli.output import OutputFormat, create_output_manager
        from replimap.codify import CodifyOutputGenerator, get_codify_pipeline
        from replimap.codify.transformers.managed_filter import ManagedResourceFilter
        from replimap.core import GraphEngine
        from replimap.core.cache_manager import get_or_load_graph, save_graph_to_cache
        from replimap.core.unified_storage import GraphEngineAdapter
        from replimap.scanners.base import run_all_scanners

        # Get V3 context - handle both GlobalContext and legacy dict patterns
        gctx: GlobalContext | None = None
        if isinstance(ctx.obj, GlobalContext):
            gctx = ctx.obj
        elif isinstance(ctx.obj, dict) and "_parent_context" in ctx.obj:
            # Legacy pattern from sub-command groups
            parent = ctx.obj.get("_parent_context")
            if isinstance(parent, GlobalContext):
                gctx = parent

        # If local --format specified, create new output manager with that format
        if output_format:
            try:
                OutputFormat(output_format)  # Validate
                verbose = gctx.output.verbose if gctx else 0
                output = create_output_manager(format=output_format, verbose=verbose)
            except ValueError:
                raise typer.BadParameter(
                    f"Invalid format '{output_format}'. "
                    f"Choose from: text, json, table, quiet"
                ) from None
        elif gctx:
            output = gctx.output
        else:
            # Fallback: create default output manager
            output = create_output_manager(format="text", verbose=0)

        # Use profile/region from context if not provided via flags
        ctx_profile = gctx.profile if gctx else None
        ctx_region = gctx.region if gctx else None
        # Also check legacy dict pattern
        if ctx_profile is None and isinstance(ctx.obj, dict):
            ctx_profile = ctx.obj.get("profile")
        if ctx_region is None and isinstance(ctx.obj, dict):
            ctx_region = ctx.obj.get("region")

        effective_profile = profile or ctx_profile

        # Use consolidated region resolution, with context region as fallback default
        effective_region, region_source = resolve_effective_region(
            region, effective_profile, default=ctx_region or "us-east-1"
        )
        # Adjust source if it came from context
        if region_source == "default" and ctx_region:
            region_source = "context"

        # Use effective_region as primary_region default if not specified
        effective_primary_region = primary_region or effective_region

        # Display configuration (to stderr via panel)
        config_content = (
            f"[bold]RepliMap Codify[/] v{__version__}\n"
            f"Region: [cyan]{effective_region}[/] [dim](from {region_source})[/]\n"
            f"Profile: [cyan]{effective_profile}[/]\n"
            f"Output: [cyan]{output_dir}[/]\n"
            f"Primary Region: [cyan]{effective_primary_region}[/]\n"
            f"Lifecycle Protection: [cyan]{not no_lifecycle_protection}[/]\n"
            f"Import Method: [cyan]{'imports.sh' if use_import_script else 'imports.tf'}[/]"
        )
        output.panel(config_content, title="Configuration", border_style="cyan")

        # Get AWS session
        session = get_aws_session(
            effective_profile, effective_region, use_cache=not no_cache
        )

        # Load from cache or scan - use stderr console for cache manager
        stderr_console = output._stderr_console
        cached_graph, cache_meta = get_or_load_graph(
            profile=effective_profile,
            region=effective_region,
            console=stderr_console,
            refresh=refresh,
        )

        if cached_graph is not None:
            # Convert to GraphEngineAdapter if needed
            if isinstance(cached_graph, GraphEngine):
                graph = GraphEngineAdapter()
                for resource in cached_graph.iter_resources():
                    graph.add_resource(resource)
            else:
                graph = cached_graph
        else:
            # Initialize graph and scan
            legacy_graph = GraphEngine()

            with output.spinner("Scanning AWS resources..."):
                run_all_scanners(session, effective_region, legacy_graph)

            # Save to cache
            save_graph_to_cache(
                graph=legacy_graph,
                profile=effective_profile,
                region=effective_region,
                console=stderr_console,
            )

            # Convert to GraphEngineAdapter
            graph = GraphEngineAdapter()
            for resource in legacy_graph.iter_resources():
                graph.add_resource(resource)

        # Get resource count
        resource_count = len(list(graph.iter_resources()))
        output.success(f"Found {resource_count} resources")

        if resource_count == 0:
            output.panel(
                "[yellow]No resources found to codify.[/]\n"
                "Check your AWS profile and region settings.",
                border_style="yellow",
            )
            raise typer.Exit(0)

        # Load managed IDs from state file if provided
        managed_ids: set[str] | None = None
        if state_file:
            with output.spinner("Loading existing Terraform state..."):
                managed_filter = ManagedResourceFilter.from_terraform_state(state_file)
                managed_ids = managed_filter.managed_ids

            if managed_ids:
                output.log(f"Found {len(managed_ids)} already-managed resources")

        # Build and execute pipeline
        with output.spinner("Running codify pipeline..."):
            pipeline = get_codify_pipeline(
                region=effective_region,
                primary_region=effective_primary_region,
                include_global=include_global,
                protect_resources=not no_lifecycle_protection,
                skip_defaults=skip_defaults,
                managed_ids=managed_ids,
            )

            graph = pipeline.execute(graph)

        output.success(f"Applied {len(pipeline)} transformers")

        # Get statistics
        final_count = len(list(graph.iter_resources()))
        protected = graph.get_metadata("codify_protected_resources") or []
        variables = graph.get_metadata("codify_variables") or []

        # Prepare result data for JSON output
        result_data = {
            "resources": final_count,
            "protected": len(protected),
            "secrets_extracted": len(variables),
            "output_dir": str(output_dir),
            "dry_run": dry_run,
            "files": {},
        }

        if dry_run:
            # Show preview
            preview_data = [
                {"Metric": "Resources to generate", "Value": str(final_count)},
                {"Metric": "Protected resources", "Value": str(len(protected))},
                {"Metric": "Extracted secrets", "Value": str(len(variables))},
                {"Metric": "Output directory", "Value": str(output_dir)},
            ]
            output.table(preview_data, title="Dry Run Preview")

            output.panel(
                "[yellow]Dry run mode - no files written.[/]\n"
                "Remove [bold]--dry-run[/] to generate files.",
                border_style="yellow",
            )

            # In JSON mode, present the result data
            if output.is_json:
                output.present(result_data)
        else:
            # Generate output
            with output.spinner("Generating Terraform files..."):
                generator = CodifyOutputGenerator(
                    region=effective_region,
                    use_import_blocks=not use_import_script,
                )
                written_files = generator.generate(graph, output_dir)

            # Update result data with files
            result_data["files"] = {k: str(v) for k, v in written_files.items()}

            # Show results table (to stderr)
            file_data = [
                {"File": filename, "Path": str(filepath)}
                for filename, filepath in sorted(written_files.items())
            ]
            output.table(file_data, title="Generated Files")

            # Show completion panel (to stderr)
            completion_content = (
                f"[green]Generated {len(written_files)} files[/] in [bold]{output_dir}[/]\n\n"
                f"Resources: [cyan]{final_count}[/]\n"
                f"Protected: [cyan]{len(protected)}[/] (lifecycle {{ prevent_destroy = true }})\n"
                f"Secrets: [cyan]{len(variables)}[/] (extracted to variables)\n\n"
                "[bold]Next steps:[/]\n"
                f"  1. cd {output_dir}\n"
                "  2. terraform init\n"
                "  3. terraform plan  # Should show: X to import, 0 to add\n"
                "  4. terraform apply\n\n"
                "[dim]See README.md for detailed instructions.[/]"
            )
            output.panel(
                completion_content, title="Codify Complete", border_style="green"
            )

            # In JSON mode, present the final result
            if output.is_json:
                output.present(result_data)
