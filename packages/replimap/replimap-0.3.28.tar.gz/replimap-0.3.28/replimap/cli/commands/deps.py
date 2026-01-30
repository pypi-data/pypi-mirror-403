"""Dependency exploration command for RepliMap CLI.

V3 Architecture:
- Uses @enhanced_cli_error_handler for structured error handling
- Uses ctx.obj.output for stdout hygiene (NEVER use console.print directly)
- JSON mode available via global --format flag
"""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING, Any

import typer
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.status import Status

from replimap.cli.errors import enhanced_cli_error_handler
from replimap.cli.utils import get_aws_session, logger, resolve_effective_region
from replimap.core import GraphEngine
from replimap.core.browser import open_in_browser
from replimap.scanners.base import run_all_scanners

if TYPE_CHECKING:
    from replimap.cli.context import GlobalContext
    from replimap.cli.output import OutputManager


def _run_analyzer_mode(
    resource_id: str,
    session: Any,
    region: str,
    report_format: str,
    output_file: Path | None,
    output: OutputManager,
) -> None:
    """Run deep analyzer mode for deps command."""
    from replimap.deps import get_analyzer
    from replimap.deps.reporter import DependencyAnalysisReporter

    output.log("")

    # Create AWS clients
    with Status("[bold blue]Creating AWS clients...", console=output._stderr_console):
        ec2_client = session.client("ec2", region_name=region)
        rds_client = session.client("rds", region_name=region)
        iam_client = session.client("iam")  # IAM is global
        lambda_client = session.client("lambda", region_name=region)
        elbv2_client = session.client("elbv2", region_name=region)
        autoscaling_client = session.client("autoscaling", region_name=region)
        elasticache_client = session.client("elasticache", region_name=region)
        s3_client = session.client("s3", region_name=region)
        sts_client = session.client("sts")

    # Get the appropriate analyzer
    try:
        analyzer = get_analyzer(
            resource_id,
            ec2_client=ec2_client,
            rds_client=rds_client,
            iam_client=iam_client,
            lambda_client=lambda_client,
            elbv2_client=elbv2_client,
            autoscaling_client=autoscaling_client,
            elasticache_client=elasticache_client,
            s3_client=s3_client,
            sts_client=sts_client,
        )
    except ValueError:
        output.panel(
            f"[red]Unsupported resource type:[/] {resource_id}\n\n"
            f"Analyzer mode currently supports:\n"
            f"  • EC2 instances (i-xxx)\n"
            f"  • Security Groups (sg-xxx)\n"
            f"  • IAM Roles\n"
            f"  • RDS Instances\n"
            f"  • Auto Scaling Groups\n"
            f"  • S3 Buckets\n"
            f"  • Lambda Functions\n"
            f"  • Load Balancers (ALB/NLB)\n"
            f"  • ElastiCache Clusters\n\n"
            f"Use without --analyze flag for graph-based analysis.",
            title="Error",
            border_style="red",
        )
        raise typer.Exit(1)

    # Run analysis with progress feedback
    with Status(
        f"[bold blue]Analyzing {analyzer.resource_type}...",
        console=output._stderr_console,
    ) as status:
        try:
            status.update(f"[bold blue]Analyzing {resource_id}...")
            analysis = analyzer.analyze(resource_id, region)

            # Update status for large queries
            from replimap.deps.models import RelationType

            consumers = analysis.dependencies.get(RelationType.CONSUMER, [])
            if len(consumers) > 10:
                status.update(
                    f"[bold blue]Found {len(consumers)} consumers, calculating blast radius..."
                )

        except ValueError:
            output.panel(
                f"[red]Resource not found:[/] {resource_id}\n\n"
                f"Make sure the resource ID is correct and exists in region {region}.",
                title="Error",
                border_style="red",
            )
            raise typer.Exit(1)
        except Exception as e:
            output.panel(
                f"[red]Analysis failed:[/]\n{e}",
                title="Error",
                border_style="red",
            )
            logger.exception("Analyzer mode failed")
            raise typer.Exit(1)

    # Report results
    reporter = DependencyAnalysisReporter(console=output._stderr_console)
    output.log("")

    if report_format == "tree":
        reporter.to_tree(analysis)
    elif report_format == "table":
        reporter.to_table(analysis)
    elif report_format == "json":
        out_path = output_file or Path("./deps.json")
        reporter.to_json(analysis, out_path)
    else:
        # Default: console output
        reporter.to_console(analysis)

    output.log("")


def deps_command(
    ctx: typer.Context,
    resource_id: str = typer.Argument(
        ...,
        help="Resource ID to analyze (e.g., vpc-12345, sg-abc123)",
    ),
    # === Common Options ===
    profile: str | None = typer.Option(
        None,
        "--profile",
        "-p",
        help="AWS profile name",
    ),
    region: str | None = typer.Option(
        None,
        "--region",
        "-r",
        help="AWS region to scan",
    ),
    vpc: str | None = typer.Option(
        None,
        "--vpc",
        "-v",
        help="VPC ID to scope the scan (optional)",
    ),
    max_depth: int = typer.Option(
        10,
        "--depth",
        "-d",
        help="Maximum depth to traverse",
    ),
    output_file: Path | None = typer.Option(
        None,
        "--output",
        "-o",
        help="Output file path (HTML or JSON)",
    ),
    report_format: str = typer.Option(
        "console",
        "--format",
        "-f",
        help="Output format: console, tree, table, html, or json",
    ),
    # === Output Options ===
    open_report: bool = typer.Option(
        True,
        "--open/--no-open",
        help="Open HTML report in browser after generation",
        rich_help_panel="Output",
    ),
    show_disclaimer: bool = typer.Option(
        True,
        "--disclaimer/--no-disclaimer",
        help="Show disclaimer about limitations",
        rich_help_panel="Output",
    ),
    verbose: bool = typer.Option(
        False,
        "--verbose",
        "-V",
        help="Show all resources (not summarized by type)",
        rich_help_panel="Output",
    ),
    # === Cache & Performance ===
    no_cache: bool = typer.Option(
        False,
        "--no-cache",
        help="Don't use cached credentials",
        rich_help_panel="Cache & Performance",
    ),
    refresh: bool = typer.Option(
        False,
        "--refresh",
        "-R",
        help="Force fresh AWS scan (ignore cached graph)",
        rich_help_panel="Cache & Performance",
    ),
    # === Analysis Mode ===
    analyze: bool = typer.Option(
        False,
        "--analyze",
        "-a",
        help="Use deep analyzer mode with categorized output (EC2, SG, IAM Role)",
        rich_help_panel="Analysis",
    ),
) -> None:
    """Explore dependencies for a resource.

    \b

    Shows what resources MAY be affected if you modify or delete a resource.
    This analysis is based on AWS API metadata only.

    \b

    IMPORTANT: Application-level dependencies (hardcoded IPs, DNS, config files)
    are NOT detected. Always validate all dependencies before making
    infrastructure changes.

    \b

    This is a Pro+ feature.

    \b

    Output formats:

    - console: Rich terminal output with summary (default)

    - tree: Tree view of dependencies

    - table: Table of affected resources

    - html: Interactive HTML report with D3.js visualization

    - json: Machine-readable JSON

    \b

    Examples:

        replimap deps sg-12345 -r us-east-1              # Security group deps

        replimap deps vpc-abc123 -r us-east-1 -f tree    # Tree view

        replimap deps i-xyz789 -r us-east-1 -f html -o deps.html

        replimap deps vpc-12345 -r us-east-1 --depth 3   # Limit depth
    """
    from replimap.dependencies import (
        DISCLAIMER_SHORT,
        DependencyExplorerReporter,
        DependencyGraphBuilder,
        ImpactCalculator,
    )
    from replimap.licensing import check_deps_allowed

    # Get V3 context
    gctx: GlobalContext = ctx.obj
    output = gctx.output

    # Check deps feature access (Pro+ feature)
    deps_gate = check_deps_allowed()
    if not deps_gate.allowed:
        output.error(deps_gate.prompt)
        raise typer.Exit(1)

    # Determine region: flag > profile config > default
    effective_region, region_source = resolve_effective_region(region, profile)

    output.log("")
    output.panel(
        f"[bold blue]Dependency Explorer[/bold blue]\n\n"
        f"Resource: [cyan]{resource_id}[/]\n"
        f"Region: [cyan]{effective_region}[/] [dim](from {region_source})[/]\n"
        f"Profile: [cyan]{profile or 'default'}[/]\n"
        + (f"VPC: [cyan]{vpc}[/]\n" if vpc else "")
        + f"Max Depth: [cyan]{max_depth}[/]\n\n"
        f"[dim]{DISCLAIMER_SHORT}[/dim]",
        border_style="blue",
    )

    # Get AWS session
    session = get_aws_session(profile, effective_region, use_cache=not no_cache)

    # Use analyzer mode if requested (deep analysis with categorized output)
    if analyze:
        _run_analyzer_mode(
            resource_id=resource_id,
            session=session,
            region=effective_region,
            report_format=report_format,
            output_file=output_file,
            output=output,
        )
        return

    # Graph-based mode (default)
    # Try to load from cache first
    from replimap.core.cache_manager import get_or_load_graph, save_graph_to_cache

    # Try to load from cache first (global signal handler handles Ctrl-C)
    try:
        output.log("")
        cached_graph, cache_meta = get_or_load_graph(
            profile=profile or "default",
            region=effective_region,
            console=output._stderr_console,
            refresh=refresh,
            vpc=vpc,
        )

        if cached_graph is not None:
            graph = cached_graph
        else:
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                console=output._stderr_console,
            ) as progress:
                task = progress.add_task("Scanning AWS resources...", total=None)

                # Create graph and run scanners
                graph = GraphEngine()
                run_all_scanners(
                    session=session,
                    region=effective_region,
                    graph=graph,
                )
                progress.update(task, completed=True)

            # Save to cache
            save_graph_to_cache(
                graph=graph,
                profile=profile or "default",
                region=effective_region,
                console=output._stderr_console,
                vpc=vpc,
            )
    except Exception as e:
        output.log("")
        output.panel(
            f"[red]Dependency exploration failed:[/]\n{e}",
            title="Error",
            border_style="red",
        )
        logger.exception("Dependency exploration failed")
        raise typer.Exit(1)

    # Apply VPC filter if specified
    if vpc:
        from replimap.core import ScanFilter, apply_filter_to_graph

        filter_config = ScanFilter(
            vpc_ids=[vpc],
            include_vpc_resources=True,
        )
        graph = apply_filter_to_graph(graph, filter_config)

    # Build dependency graph and explore dependencies
    try:
        builder = DependencyGraphBuilder()
        dep_graph = builder.build_from_graph_engine(graph, effective_region)

        # Build resource configs map for ASG detection
        resource_configs = {res.id: res.config for res in graph.get_all_resources()}

        # Explore dependencies
        calculator = ImpactCalculator(
            dep_graph,
            builder.get_nodes(),
            builder.get_edges(),
            resource_configs=resource_configs,
        )

        try:
            result = calculator.calculate_blast_radius(resource_id, max_depth)
        except ValueError:
            output.log("")
            output.panel(
                f"[red]Resource not found:[/] {resource_id}\n\n"
                f"Make sure the resource ID is correct and exists in region {effective_region}.\n\n"
                f"[dim]Available resources: {len(builder.get_nodes())}[/]",
                title="Error",
                border_style="red",
            )
            raise typer.Exit(1)

    except Exception as e:
        output.log("")
        output.panel(
            f"[red]Dependency exploration failed:[/]\n{e}",
            title="Error",
            border_style="red",
        )
        logger.exception("Dependency exploration failed")
        raise typer.Exit(1)

    # Report results
    reporter = DependencyExplorerReporter(console=output._stderr_console)
    output.log("")

    if report_format == "tree":
        reporter.to_tree(result)
    elif report_format == "table":
        reporter.to_table(result)
    elif report_format == "json":
        out_path = output_file or Path("./deps.json")
        reporter.to_json(result, out_path)
    elif report_format == "html":
        out_path = output_file or Path("./deps.html")
        reporter.to_html(result, out_path)
        if open_report:
            output.log("")
            open_in_browser(out_path, console=output._stderr_console)
    else:
        # Default: console output (compact by default, verbose shows all)
        reporter.to_console(result, verbose=verbose)

    # Also export if output path specified but format is console
    if output_file and report_format == "console":
        if output_file.suffix == ".html":
            reporter.to_html(result, output_file)
            if open_report:
                output.log("")
                open_in_browser(output_file, console=output._stderr_console)
        elif output_file.suffix == ".json":
            reporter.to_json(result, output_file)

    output.log("")


# Backward compatibility alias for blast command
def blast_command(
    ctx: typer.Context,
    resource_id: str = typer.Argument(...),
    profile: str | None = typer.Option(None, "--profile", "-p"),
    region: str | None = typer.Option(None, "--region", "-r"),
    vpc: str | None = typer.Option(None, "--vpc", "-v"),
    max_depth: int = typer.Option(10, "--depth", "-d"),
    output_file: Path | None = typer.Option(None, "--output", "-o"),
    report_format: str = typer.Option("console", "--format", "-f"),
    open_report: bool = typer.Option(True, "--open/--no-open"),
    no_cache: bool = typer.Option(False, "--no-cache"),
    refresh: bool = typer.Option(False, "--refresh", "-R"),
) -> None:
    """Deprecated: Use 'replimap deps' instead."""
    # Get V3 context
    gctx: GlobalContext = ctx.obj
    output = gctx.output
    output.warn("'replimap blast' is deprecated. Use 'replimap deps' instead.")

    deps_command(
        ctx=ctx,
        resource_id=resource_id,
        profile=profile,
        region=region,
        vpc=vpc,
        max_depth=max_depth,
        output_file=output_file,
        report_format=report_format,
        open_report=open_report,
        show_disclaimer=True,
        verbose=False,
        no_cache=no_cache,
        refresh=refresh,
        analyze=False,
    )


def register(app: typer.Typer, panel: str | None = None) -> None:
    """Register the deps and blast commands with the Typer app."""
    app.command(name="deps", rich_help_panel=panel)(
        enhanced_cli_error_handler(deps_command)
    )
    app.command(name="blast", hidden=True)(enhanced_cli_error_handler(blast_command))
