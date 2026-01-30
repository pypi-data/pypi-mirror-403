"""Unused resources detection command for RepliMap CLI.

V3 Architecture:
- Uses @enhanced_cli_error_handler for structured error handling
- Uses ctx.obj.output for stdout hygiene (stderr for progress, stdout for results)
- JSON mode available via global --format flag
"""

from __future__ import annotations

import csv
import json as json_module
from pathlib import Path
from typing import TYPE_CHECKING

import typer
from rich.table import Table

from replimap.cli.errors import enhanced_cli_error_handler
from replimap.cli.utils import get_aws_session, resolve_effective_region
from replimap.core import GraphEngine
from replimap.scanners.base import run_all_scanners

if TYPE_CHECKING:
    from replimap.cli.context import GlobalContext


def unused_command(
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
        help="AWS region to scan",
    ),
    # === Selection Options ===
    confidence: str = typer.Option(
        "all",
        "--confidence",
        "-c",
        help="Filter by confidence: high, medium, low, all",
        rich_help_panel="Selection",
    ),
    resource_types: str | None = typer.Option(
        None,
        "--types",
        "-t",
        help="Resource types to check: ec2,ebs,rds,nat,elb (comma-separated)",
        rich_help_panel="Selection",
    ),
    # === Output Options ===
    output_file: Path | None = typer.Option(
        None,
        "--output",
        "-o",
        help="Output file path (JSON, CSV, or Markdown)",
        rich_help_panel="Output",
    ),
    report_format: str = typer.Option(
        "console",
        "--format",
        "-f",
        help="Output format: console, json, csv, markdown",
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
) -> None:
    """Detect unused and underutilized AWS resources.

    \b

    Identifies resources that may be candidates for termination
    or optimization to reduce costs.

    \b

    Examples:

        replimap unused -r us-east-1

        replimap unused -r us-east-1 --confidence high

        replimap unused -r us-east-1 --types ec2,ebs

        replimap unused -r us-east-1 -f json -o unused.json
    """
    from replimap.cost.unused_detector import (
        ConfidenceLevel,
        UnusedResourceDetector,
    )
    from replimap.licensing import check_cost_allowed

    # Get V3 context
    gctx: GlobalContext = ctx.obj
    output = gctx.output
    stderr_console = output._stderr_console

    # Check feature access
    cost_gate = check_cost_allowed()
    if not cost_gate.allowed:
        output.log(cost_gate.prompt)
        raise typer.Exit(1)

    # Use context defaults
    effective_profile = profile or gctx.profile or "default"

    # Determine region using consolidated resolution
    effective_region, region_source = resolve_effective_region(
        region, effective_profile, default=gctx.region or "us-east-1"
    )
    if region_source == "default" and gctx.region:
        region_source = "context"

    output.panel(
        f"[bold cyan]Unused Resource Detector[/bold cyan]\n\n"
        f"Region: [cyan]{effective_region}[/] [dim](from {region_source})[/]\n"
        f"Profile: [cyan]{effective_profile}[/]",
        border_style="cyan",
    )

    session = get_aws_session(
        effective_profile, effective_region, use_cache=not no_cache
    )

    types_filter = None
    if resource_types:
        types_filter = [t.strip().lower() for t in resource_types.split(",")]

    # Try to load from cache first (global signal handler handles Ctrl-C)
    from replimap.core.cache_manager import get_or_load_graph, save_graph_to_cache

    output.log("")
    cached_graph, cache_meta = get_or_load_graph(
        profile=effective_profile,
        region=effective_region,
        console=stderr_console,
        refresh=refresh,
    )

    if cached_graph is not None:
        graph = cached_graph
    else:
        with output.spinner("Scanning for unused resources..."):
            graph = GraphEngine()
            run_all_scanners(session, effective_region, graph)

        # Save to cache
        save_graph_to_cache(
            graph=graph,
            profile=effective_profile,
            region=effective_region,
            console=stderr_console,
        )

    # Analyze resource utilization (global signal handler handles Ctrl-C)
    import asyncio

    account_id = session.client("sts").get_caller_identity().get("Account", "")

    with output.spinner("Analyzing resource utilization..."):
        detector = UnusedResourceDetector(
            region=effective_region,
            account_id=account_id,
        )

        async def run_detection():
            try:
                return await detector.scan(graph, check_metrics=True)
            finally:
                await detector.close()

        report = asyncio.run(run_detection())
        unused_resources = report.unused_resources

    # Filter by confidence
    if confidence != "all":
        confidence_map = {
            "high": ConfidenceLevel.HIGH,
            "medium": ConfidenceLevel.MEDIUM,
            "low": ConfidenceLevel.LOW,
        }
        filter_confidence = confidence_map.get(confidence.lower())
        if filter_confidence:
            unused_resources = [
                r for r in unused_resources if r.confidence == filter_confidence
            ]

    # Filter by resource type
    if types_filter:
        unused_resources = [
            r
            for r in unused_resources
            if any(t in r.resource_type.lower() for t in types_filter)
        ]

    output.log("")
    if not unused_resources:
        output.success("No unused resources detected!")
        output.log("")
        return

    output.warn(f"Found {len(unused_resources)} unused/underutilized resources")
    output.log("")

    if report_format == "console":
        # Group by resource type
        by_type: dict[str, list] = {}
        for r in unused_resources:
            if r.resource_type not in by_type:
                by_type[r.resource_type] = []
            by_type[r.resource_type].append(r)

        for rtype, resources in sorted(by_type.items()):
            output.log(f"[bold]{rtype}[/bold] ({len(resources)})")
            table = Table(show_header=True)
            table.add_column("Resource ID", style="cyan")
            table.add_column("Name")
            table.add_column("Reason")
            table.add_column("Confidence")
            table.add_column("Monthly Savings", justify="right")

            for r in resources[:10]:
                conf_style = {"high": "green", "medium": "yellow", "low": "dim"}.get(
                    r.confidence.value, "dim"
                )
                table.add_row(
                    r.resource_id,
                    r.resource_name[:30] if r.resource_name else "-",
                    r.reason.description[:40],
                    f"[{conf_style}]{r.confidence.value}[/]",
                    f"${r.potential_savings:.2f}" if r.potential_savings else "-",
                )

            stderr_console.print(table)
            if len(resources) > 10:
                output.log(f"  ... and {len(resources) - 10} more")
            output.log("")

        total_savings = sum(r.potential_savings or 0 for r in unused_resources)
        if total_savings > 0:
            output.success(f"Potential monthly savings: ${total_savings:.2f}")

    elif report_format == "json":
        output_path = output_file or Path("unused_resources.json")
        data = {
            "region": effective_region,
            "total_unused": len(unused_resources),
            "resources": [
                {
                    "resource_id": r.resource_id,
                    "resource_type": r.resource_type,
                    "resource_name": r.resource_name,
                    "reason": r.reason.value,
                    "confidence": r.confidence.value,
                    "details": r.details,
                    "potential_savings": float(r.potential_savings or 0),
                }
                for r in unused_resources
            ],
        }
        with open(output_path, "w") as f:
            json_module.dump(data, f, indent=2)
        output.success(f"Saved to {output_path}")

    elif report_format == "csv":
        output_path = output_file or Path("unused_resources.csv")
        with open(output_path, "w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(
                [
                    "Resource ID",
                    "Type",
                    "Name",
                    "Reason",
                    "Confidence",
                    "Details",
                    "Monthly Savings",
                ]
            )
            for r in unused_resources:
                writer.writerow(
                    [
                        r.resource_id,
                        r.resource_type,
                        r.resource_name,
                        r.reason.value,
                        r.confidence.value,
                        r.details,
                        r.potential_savings or 0,
                    ]
                )
        output.success(f"Saved to {output_path}")

    elif report_format in ("md", "markdown"):
        output_path = output_file or Path("unused_resources.md")
        with open(output_path, "w") as f:
            f.write("# Unused Resources Report\n\n")
            f.write(f"- Region: {effective_region}\n")
            f.write(f"- Total: {len(unused_resources)}\n\n")
            f.write("| Resource ID | Type | Reason | Confidence | Savings |\n")
            f.write("|-------------|------|--------|------------|--------|\n")
            for r in unused_resources:
                f.write(
                    f"| {r.resource_id} | {r.resource_type} | {r.reason.value} | "
                    f"{r.confidence.value} | ${r.potential_savings or 0:.2f} |\n"
                )
        output.success(f"Saved to {output_path}")

    output.log("")


def register(app: typer.Typer, panel: str | None = None) -> None:
    """Register the unused command with the Typer app."""
    app.command(name="unused", rich_help_panel=panel)(
        enhanced_cli_error_handler(unused_command)
    )
