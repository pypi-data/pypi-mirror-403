"""
Clone command - Generate Infrastructure-as-Code from AWS resources.

V3 Architecture:
- Uses @enhanced_cli_error_handler for structured error handling
- Uses ctx.obj.output for stdout hygiene (NEVER use console.print directly)
- JSON mode available via global --format flag
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import TYPE_CHECKING

import typer
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.table import Table

from replimap import __version__
from replimap.cli.errors import enhanced_cli_error_handler
from replimap.cli.utils import (
    get_available_profiles,
    get_aws_session,
    resolve_effective_region,
)
from replimap.core import GraphEngine
from replimap.licensing.manager import get_license_manager
from replimap.renderers import TerraformRenderer
from replimap.scanners.base import run_all_scanners
from replimap.transformers import create_default_pipeline

if TYPE_CHECKING:
    from replimap.cli.context import GlobalContext


def register(app: typer.Typer, panel: str | None = None) -> None:
    """Register the clone command with the app."""

    @app.command(rich_help_panel=panel)
    @enhanced_cli_error_handler
    def clone(
        ctx: typer.Context,
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
        clone_format: str = typer.Option(
            "terraform",
            "--format",
            "-f",
            help="Output format: 'terraform' (Community+), 'cloudformation' (Pro+), "
            "'pulumi' (Team+)",
        ),
        mode: str = typer.Option(
            "dry-run",
            "--mode",
            "-m",
            help="Mode: 'dry-run' (preview) or 'generate' (create files)",
        ),
        downsize: bool = typer.Option(
            True,
            "--downsize/--no-downsize",
            help="Enable instance downsizing for cost savings",
        ),
        rename_pattern: str | None = typer.Option(
            None,
            "--rename-pattern",
            help="Renaming pattern, e.g., 'prod:stage'",
        ),
        interactive: bool = typer.Option(
            False,
            "--interactive",
            "-i",
            help="Interactive mode - prompt for missing options",
        ),
        no_cache: bool = typer.Option(
            False,
            "--no-cache",
            help="Don't use cached credentials (re-authenticate)",
        ),
        refresh: bool = typer.Option(
            False,
            "--refresh",
            "-R",
            help="Force fresh AWS scan (ignore cached graph)",
        ),
        dev_mode: bool = typer.Option(
            False,
            "--dev-mode",
            "--dev",
            help="[PRO+] Optimize resources for dev/staging "
            "(generates right-sizer.auto.tfvars)",
        ),
        dev_strategy: str = typer.Option(
            "conservative",
            "--dev-strategy",
            help="Right-Sizer strategy: 'conservative' (default) or 'aggressive'",
        ),
        # Backend options
        backend: str = typer.Option(
            "local",
            "--backend",
            "-b",
            help="Terraform backend type: 'local' (default) or 's3'",
        ),
        backend_bucket: str | None = typer.Option(
            None,
            "--backend-bucket",
            help="S3 bucket for state (required if --backend=s3)",
        ),
        backend_key: str = typer.Option(
            "replimap/terraform.tfstate",
            "--backend-key",
            help="S3 key for state file",
        ),
        backend_region: str | None = typer.Option(
            None,
            "--backend-region",
            help="S3 bucket region (defaults to scan region)",
        ),
        backend_dynamodb: str | None = typer.Option(
            None,
            "--backend-dynamodb",
            help="DynamoDB table for state locking",
        ),
        backend_bootstrap: bool = typer.Option(
            False,
            "--backend-bootstrap",
            help="Generate bootstrap Terraform to create S3 backend infrastructure",
        ),
    ) -> None:
        """Clone AWS environment to Infrastructure-as-Code.

        \b

        The region is determined in this order:

        1. --region flag (if provided)

        2. Profile's configured region (from ~/.aws/config)

        3. AWS_DEFAULT_REGION environment variable

        4. us-east-1 (fallback)

        \b

        Output formats:

        - terraform: Terraform HCL (Community tier and above)

        - cloudformation: AWS CloudFormation YAML (Pro plan and above)

        - pulumi: Pulumi Python (Team plan and above)

        \b

        Backend types (Terraform only):

        - local: State stored locally (default)

        - s3: State stored in S3 for team collaboration

        \b

        Examples:

            replimap clone --profile prod --mode dry-run

            replimap clone --profile prod --format terraform --mode generate

            replimap clone -i  # Interactive mode

            replimap clone --profile prod --format cloudformation -o ./cfn

        \b

        S3 Backend Examples:

            replimap clone -p prod -o ./tf --backend s3 --backend-bucket my-state

            replimap clone -p prod -o ./tf --backend s3 --backend-bucket my-state --backend-dynamodb locks

            replimap clone -p prod -o ./tf --backend s3 --backend-bucket my-state --backend-bootstrap
        """
        from replimap.licensing.gates import FeatureNotAvailableError
        from replimap.renderers import CloudFormationRenderer, PulumiRenderer

        # Get V3 context
        gctx: GlobalContext = ctx.obj
        output = gctx.output

        # Interactive mode - prompt for missing options
        if interactive:
            if not profile:
                available = get_available_profiles()
                output.log("\n[bold]Available AWS Profiles:[/]")
                for i, p in enumerate(available, 1):
                    output.log(f"  {i}. {p}")
                output.log("")
                profile = output.select(
                    "Select profile",
                    choices=available,
                    default="default",
                )

        # Determine region: flag > profile config > env var > default
        effective_region, region_source = resolve_effective_region(region, profile)

        if interactive and not region:
            output.progress(
                f"Detected region: {effective_region} (from {region_source})"
            )
            if not output.confirm("Use this region?", default=True):
                effective_region = output.prompt(
                    "Enter region", default=effective_region
                )

        # Validate output format
        valid_formats = ("terraform", "cloudformation", "pulumi")
        if clone_format not in valid_formats:
            output.error(
                f"Invalid format '{clone_format}'. "
                f"Use one of: {', '.join(valid_formats)}"
            )
            raise typer.Exit(1)

        # Validate backend options
        valid_backends = ("local", "s3")
        if backend not in valid_backends:
            output.error(
                f"Invalid backend '{backend}'. Use one of: {', '.join(valid_backends)}"
            )
            raise typer.Exit(1)

        if backend == "s3" and not backend_bucket:
            output.error("--backend-bucket is required when using S3 backend")
            raise typer.Exit(1)

        # Backend is only applicable for Terraform format
        if backend == "s3" and clone_format != "terraform":
            output.warn(
                f"Backend options only apply to Terraform format. "
                f"Ignoring --backend for {clone_format}."
            )
            backend = "local"

        if interactive:
            output.progress(f"Current format: {clone_format}")
            if not output.confirm("Use this format?", default=True):
                clone_format = output.select(
                    "Select format",
                    choices=list(valid_formats),
                    default="terraform",
                )

        # Get the appropriate renderer
        format_info = {
            "terraform": ("Terraform HCL", "Community+"),
            "cloudformation": ("CloudFormation YAML", "Pro+"),
            "pulumi": ("Pulumi Python", "Team+"),
        }
        format_name, plan_required = format_info[clone_format]

        manager = get_license_manager()
        plan_badge = f"[dim]({manager.current_plan.value})[/]"

        output.panel(
            f"[bold]RepliMap Clone[/] v{__version__} {plan_badge}\n"
            f"Region: [cyan]{effective_region}[/] [dim](from {region_source})[/]\n"
            f"Profile: [cyan]{profile or 'default'}[/]\n"
            f"Format: [cyan]{format_name}[/] ({plan_required})\n"
            f"Mode: [cyan]{mode}[/]\n"
            f"Output: [cyan]{output_dir}[/]\n"
            f"Downsize: [cyan]{downsize}[/]"
            + (f"\nRename: [cyan]{rename_pattern}[/]" if rename_pattern else ""),
            title="Configuration",
            border_style="cyan",
        )

        if mode not in ("dry-run", "generate"):
            output.error(f"Invalid mode '{mode}'. Use 'dry-run' or 'generate'.")
            raise typer.Exit(1)

        # Get AWS session
        session = get_aws_session(profile, effective_region, use_cache=not no_cache)

        # Try to load from cache first (global signal handler handles Ctrl-C)
        from replimap.core.cache_manager import get_or_load_graph, save_graph_to_cache

        output.log("")
        cached_graph, cache_meta = get_or_load_graph(
            profile=profile or "default",
            region=effective_region,
            console=output._stderr_console,
            refresh=refresh,
        )

        # Use cached graph or scan
        if cached_graph is not None:
            graph = cached_graph
        else:
            # Initialize graph
            graph = GraphEngine()

            # Run all scanners with progress
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                console=output._stderr_console,
            ) as progress:
                task = progress.add_task("Scanning AWS resources...", total=None)
                run_all_scanners(session, effective_region, graph)
                progress.update(task, completed=True)

            # Save to cache
            save_graph_to_cache(
                graph=graph,
                profile=profile or "default",
                region=effective_region,
                console=output._stderr_console,
            )

        stats = graph.statistics()
        output.success(
            f"Found {stats['total_resources']} resources "
            f"with {stats['total_dependencies']} dependencies"
        )

        # Apply transformations
        output.log("")

        # Determine if Right-Sizer will handle optimization
        effective_downsize = downsize
        if dev_mode and clone_format == "terraform":
            from replimap.licensing.gates import check_right_sizer_allowed

            rightsizer_result = check_right_sizer_allowed()
            if rightsizer_result.allowed:
                # Right-Sizer will handle optimization - skip DownsizeTransformer
                effective_downsize = False
                output.progress(
                    "DownsizeTransformer skipped (Right-Sizer will handle optimization)"
                )

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=output._stderr_console,
        ) as progress:
            task = progress.add_task("Applying transformations...", total=None)
            pipeline = create_default_pipeline(
                downsize=effective_downsize,
                rename_pattern=rename_pattern,
                sanitize=True,
            )
            graph = pipeline.execute(graph)
            progress.update(task, completed=True)

        output.success(f"Applied {len(pipeline)} transformers")

        # Select renderer based on format
        if clone_format == "terraform":
            renderer = TerraformRenderer()
        elif clone_format == "cloudformation":
            renderer = CloudFormationRenderer()
        else:  # pulumi
            renderer = PulumiRenderer()

        # Preview
        preview = renderer.preview(graph)

        # Show output files table
        output.log("")
        table = Table(title="Output Files", show_header=True, header_style="bold cyan")
        table.add_column("File", style="dim")
        table.add_column("Resources", justify="right")

        for filename, resources in sorted(preview.items()):
            table.add_row(filename, str(len(resources)))

        output._stderr_console.print(table)

        if mode == "dry-run":
            output.log("")
            output.panel(
                "[yellow]This is a dry-run.[/]\n"
                "Use [bold]--mode generate[/] to create files.",
                border_style="yellow",
            )
        else:
            output.log("")
            try:
                with Progress(
                    SpinnerColumn(),
                    TextColumn("[progress.description]{task.description}"),
                    console=output._stderr_console,
                ) as progress:
                    task = progress.add_task(
                        f"Generating {format_name} files...", total=None
                    )
                    written = renderer.render(graph, output_dir)
                    progress.update(task, completed=True)

                # Print summary of skipped resource types (if any)
                if hasattr(renderer, "print_summary"):
                    renderer.print_summary(output._stderr_console)

                # Print warning about redacted secrets (if any)
                if hasattr(renderer, "scrubber") and renderer.scrubber.has_findings():
                    renderer.scrubber.print_warnings(output._stderr_console)

                output.panel(
                    f"[green]Generated {len(written)} files[/] "
                    f"in [bold]{output_dir}[/]",
                    border_style="green",
                )

                # BACKEND GENERATION (After Terraform files, before Right-Sizer)
                if clone_format == "terraform":
                    from replimap.renderers.backend import (
                        BackendGenerator,
                        LocalBackendConfig,
                        S3BackendConfig,
                    )

                    backend_generator = BackendGenerator()

                    if backend == "s3":
                        s3_config = S3BackendConfig(
                            bucket=backend_bucket,  # type: ignore[arg-type]
                            key=backend_key,
                            region=backend_region or effective_region,
                            encrypt=True,
                            dynamodb_table=backend_dynamodb,
                        )

                        # Generate backend.tf
                        backend_file = backend_generator.generate_s3_backend(
                            s3_config, output_dir
                        )
                        output.success(f"Generated S3 backend: {backend_file}")

                        # Generate bootstrap if requested
                        if backend_bootstrap:
                            bootstrap_file = (
                                backend_generator.generate_backend_bootstrap(
                                    s3_config, output_dir
                                )
                            )
                            output.success(
                                f"Generated backend bootstrap: {bootstrap_file}"
                            )
                            output.log("")
                            output.log(
                                "[yellow]To create the backend infrastructure:[/]"
                            )
                            output.log(f"  cd {output_dir}/bootstrap")
                            output.log("  terraform init")
                            output.log("  terraform apply")
                            output.log("")

                    else:
                        # Local backend (explicit generation is optional)
                        local_config = LocalBackendConfig()
                        backend_file = backend_generator.generate_local_backend(
                            local_config, output_dir
                        )
                        output.progress(f"Using local backend: {backend_file}")

                # RIGHT-SIZER INTEGRATION (After Terraform generation)
                if dev_mode and clone_format == "terraform":
                    from replimap.cost.rightsizer import (
                        DowngradeStrategy,
                        RightSizerClient,
                        check_and_prompt_upgrade,
                        right_sizer_success_panel,
                    )

                    # Check license first
                    if not check_and_prompt_upgrade():
                        output.warn(
                            "Right-Sizer skipped. Continuing with production defaults."
                        )
                    else:
                        output.log(
                            "\n[cyan]Analyzing resources for "
                            "Right-Sizer optimization...[/cyan]\n"
                        )

                        try:
                            # Initialize client
                            rightsizer = RightSizerClient()

                            # Extract resource metadata from graph
                            all_resources = graph.get_all_resources()
                            summaries = rightsizer.extract_resources(
                                all_resources, effective_region
                            )

                            if not summaries:
                                output.warn(
                                    "No rightsizable resources found "
                                    "(EC2, RDS, ElastiCache)."
                                )
                            else:
                                output.progress(
                                    f"Analyzing {len(summaries)} resources..."
                                )

                                # Get suggestions from API
                                strategy = DowngradeStrategy(dev_strategy.lower())
                                result = rightsizer.get_suggestions(summaries, strategy)

                                if result.success and result.suggestions:
                                    # 1. Display recommendations table
                                    rightsizer.display_suggestions_table(
                                        result, console=output._stderr_console
                                    )

                                    # 2. Generate and write tfvars file
                                    tfvars_content = rightsizer.generate_tfvars_content(
                                        result.suggestions
                                    )
                                    tfvars_path = rightsizer.write_tfvars_file(
                                        str(output_dir), tfvars_content
                                    )

                                    # 3. Display success panel
                                    output._stderr_console.print(
                                        right_sizer_success_panel(
                                            original_monthly=(
                                                result.total_current_monthly
                                            ),
                                            recommended_monthly=(
                                                result.total_recommended_monthly
                                            ),
                                            suggestions_count=(
                                                result.resources_with_suggestions
                                            ),
                                            skipped_count=result.resources_skipped,
                                            tfvars_filename=os.path.basename(
                                                tfvars_path
                                            ),
                                        )
                                    )

                                elif result.error_message:
                                    output.error(
                                        f"Right-Sizer error: {result.error_message}"
                                    )
                                    output.warn("Continuing with production defaults.")

                                else:
                                    output.success(
                                        "All resources are already optimally sized!"
                                    )

                        except Exception as e:
                            # Graceful degradation - don't crash the whole clone
                            output.error(f"Right-Sizer error: {e}")
                            output.warn("Continuing with production defaults.")

            except FeatureNotAvailableError as e:
                output.log("")
                output.panel(
                    f"[red]Feature not available:[/] {e}\n\n"
                    f"Upgrade your plan to use {format_name} output:\n"
                    f"[bold]https://replimap.com/pricing[/]",
                    title="Upgrade Required",
                    border_style="red",
                )
                raise typer.Exit(1)

        output.log("")
