"""Graph visualization command for RepliMap CLI.

V3 Architecture:
- Uses @enhanced_cli_error_handler for structured error handling
- Uses ctx.obj.output for stdout hygiene (NEVER use console.print directly)
- JSON mode available via global --format flag
"""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

import typer

from replimap.cli.errors import enhanced_cli_error_handler
from replimap.cli.utils import get_aws_session, resolve_effective_region
from replimap.core.browser import open_in_browser

if TYPE_CHECKING:
    from replimap.cli.context import GlobalContext


def graph_command(
    ctx: typer.Context,
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
        help="AWS region to visualize",
    ),
    vpc: str | None = typer.Option(
        None,
        "--vpc",
        "-v",
        help="VPC ID to scope the visualization (optional)",
    ),
    output_file: Path = typer.Option(
        Path("./infrastructure_graph.html"),
        "--output",
        "-o",
        help="Path for output file",
    ),
    graph_format: str = typer.Option(
        "html",
        "--format",
        "-f",
        help="Output format: html (interactive D3.js), mermaid, or json",
    ),
    # === Visualization Options ===
    open_graph: bool = typer.Option(
        True,
        "--open/--no-open",
        help="Open graph in browser after generation (HTML only)",
        rich_help_panel="Visualization",
    ),
    show_all: bool = typer.Option(
        False,
        "--all",
        "-a",
        help="Show all resources (disable filtering)",
        rich_help_panel="Visualization",
    ),
    show_sg_rules: bool = typer.Option(
        False,
        "--sg-rules",
        help="Show security group rules (hidden by default)",
        rich_help_panel="Visualization",
    ),
    show_routes: bool = typer.Option(
        False,
        "--routes",
        help="Show routes and route tables (hidden by default)",
        rich_help_panel="Visualization",
    ),
    no_collapse: bool = typer.Option(
        False,
        "--no-collapse",
        help="Disable resource grouping (show all individual resources)",
        rich_help_panel="Visualization",
    ),
    security_view: bool = typer.Option(
        False,
        "--security",
        help="Security-focused view (show SGs, IAM, KMS)",
        rich_help_panel="Visualization",
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
) -> None:
    """Generate visual dependency graph of AWS infrastructure.

    \b

    Scans your AWS environment and generates an interactive visualization
    showing resources and their dependencies.

    \b

    By default, the graph is simplified for readability:

    - Noisy resources (SG rules, routes) are hidden

    - Large groups of similar resources are collapsed

    \b

    Output formats:

    - html: Interactive D3.js force-directed graph (default)

    - mermaid: Mermaid diagram syntax for documentation

    - json: Raw JSON data for integration

    \b

    Examples:

        replimap graph --region us-east-1

        replimap graph -p prod -r us-west-2 -v vpc-abc123

        replimap graph -r us-east-1 --all           # Show everything

        replimap graph -r us-east-1 --sg-rules      # Include SG rules

        replimap graph -r us-east-1 --routes        # Include routes

        replimap graph -r us-east-1 --no-collapse   # No grouping

        replimap graph -r us-east-1 --security      # Security focus

        replimap graph -r us-east-1 --format mermaid -o docs/graph.md
    """
    from replimap.graph import GraphVisualizer
    from replimap.graph import OutputFormat as GraphOutputFormat

    # Get V3 context
    gctx: GlobalContext = ctx.obj
    output = gctx.output

    # Determine region: flag > profile config > default
    effective_region, region_source = resolve_effective_region(region, profile)

    # Parse output format
    try:
        fmt = GraphOutputFormat(graph_format.lower())
    except ValueError:
        output.error(
            f"Invalid format '{graph_format}'. Use one of: html, mermaid, json"
        )
        raise typer.Exit(1)

    # Build filter summary
    filter_parts = []
    if show_all:
        filter_parts.append("all resources")
    else:
        filter_parts.append("simplified")
        if show_sg_rules:
            filter_parts.append("+SG rules")
        if show_routes:
            filter_parts.append("+routes")
        if security_view:
            filter_parts.append("+security focus")
    if no_collapse:
        filter_parts.append("no grouping")

    filter_desc = ", ".join(filter_parts)

    output.log("")
    output.panel(
        f"[bold cyan]📊 RepliMap Graph Visualizer[/bold cyan]\n\n"
        f"Region: [cyan]{effective_region}[/] [dim](from {region_source})[/]\n"
        f"Profile: [cyan]{profile or 'default'}[/]\n"
        + (f"VPC: [cyan]{vpc}[/]\n" if vpc else "")
        + f"Format: [cyan]{fmt.value}[/]\n"
        f"Filter: [cyan]{filter_desc}[/]\n"
        f"Output: [cyan]{output_file}[/]",
        border_style="cyan",
    )

    # Get AWS session
    session = get_aws_session(profile, effective_region, use_cache=not no_cache)

    # Configure filter based on options
    effective_show_sg_rules = show_sg_rules or security_view
    effective_show_routes = show_routes

    # Try to load from cache first (global signal handler handles Ctrl-C)
    from replimap.core.cache_manager import get_or_load_graph, save_graph_to_cache

    try:
        output.log("")
        cached_graph, cache_meta = get_or_load_graph(
            profile=profile or "default",
            region=effective_region,
            console=output._stderr_console,
            refresh=refresh,
            vpc=vpc,
        )
        # Show message if we need to scan (no cache)
        if cached_graph is None:
            output.progress("Scanning AWS resources...")

        visualizer = GraphVisualizer(
            session=session,
            region=effective_region,
            profile=profile,
        )

        result = visualizer.generate(
            vpc_id=vpc,
            output_format=fmt,
            output_path=output_file,
            show_all=show_all,
            show_sg_rules=effective_show_sg_rules,
            show_routes=effective_show_routes,
            no_collapse=no_collapse,
            existing_graph=cached_graph,
        )

        # Save to cache if we did a fresh scan
        if cached_graph is None and visualizer._graph is not None:
            save_graph_to_cache(
                graph=visualizer._graph,
                profile=profile or "default",
                region=effective_region,
                console=output._stderr_console,
                vpc=vpc,
            )
    except Exception as e:
        output.log("")
        output.panel(
            f"[red]Graph generation failed:[/]\n{e}",
            title="Error",
            border_style="red",
        )
        raise typer.Exit(1)

    # Output result
    output.log("")
    if isinstance(result, Path):
        output.success(f"Graph generated: {result.absolute()}")

        # Open in browser for HTML
        if open_graph and fmt == GraphOutputFormat.HTML:
            output.log("")
            open_in_browser(result, console=output._stderr_console)
    else:
        # Content returned for stdout mode
        output.log(result)

    output.log("")


def register(app: typer.Typer, panel: str | None = None) -> None:
    """Register the graph command with the Typer app."""
    app.command(name="graph", rich_help_panel=panel)(
        enhanced_cli_error_handler(graph_command)
    )
