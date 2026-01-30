"""DR readiness command group for RepliMap CLI.

V3 Architecture:
- Uses @enhanced_cli_error_handler for structured error handling
- Uses ctx.obj.output for stdout hygiene (stderr for progress, stdout for results)
- JSON mode available via global --format flag
"""

from __future__ import annotations

import json as json_module
from pathlib import Path
from typing import TYPE_CHECKING

import typer

from replimap.cli.errors import enhanced_cli_error_handler
from replimap.cli.utils import get_aws_session, resolve_effective_region
from replimap.core import GraphEngine
from replimap.core.browser import open_in_browser
from replimap.scanners.base import run_all_scanners

if TYPE_CHECKING:
    from replimap.cli.output import OutputManager


def _get_output_manager(ctx: typer.Context) -> OutputManager:
    """Get the OutputManager from context, handling both V3 GlobalContext and dict patterns."""
    from replimap.cli.context import GlobalContext
    from replimap.cli.output import create_output_manager

    # Check for parent context reference
    parent_ctx = ctx.obj.get("_parent_context") if ctx.obj else None

    if isinstance(parent_ctx, GlobalContext):
        return parent_ctx.output

    # Fallback: create default output manager
    return create_output_manager(format="text", verbose=0)


def create_dr_app() -> typer.Typer:
    """Create and return the DR subcommand app."""
    dr_app = typer.Typer(
        help="Disaster Recovery readiness assessment",
        context_settings={"help_option_names": ["-h", "--help"]},
    )

    @dr_app.callback()
    def dr_callback(
        ctx: typer.Context,
        profile: str | None = typer.Option(
            None, "--profile", "-p", help="AWS profile name"
        ),
        region: str | None = typer.Option(
            None, "--region", "-r", help="Primary AWS region"
        ),
    ) -> None:
        """Disaster Recovery readiness assessment.

        \b

        Common options (--profile, --region) can be specified before the subcommand
        or at the global level (e.g., replimap -p prod dr assess).

        \b

        Examples:

            replimap -p prod dr assess

            replimap dr -p prod assess

            replimap dr -p prod scorecard
        """
        from replimap.cli.context import GlobalContext

        # Inherit GlobalContext from parent, or create empty dict fallback
        parent_obj = ctx.parent.obj if ctx.parent else None

        # Check if parent has GlobalContext (from main app callback)
        if isinstance(parent_obj, GlobalContext):
            global_profile = parent_obj.profile
            global_region = parent_obj.region
        elif parent_obj and hasattr(parent_obj, "get"):
            global_profile = parent_obj.get("profile")
            global_region = parent_obj.get("region")
        else:
            global_profile = None
            global_region = None

        # Create context dict for subcommands, merging local and global options
        ctx.ensure_object(dict)
        ctx.obj["profile"] = profile or global_profile
        ctx.obj["region"] = region or global_region
        # Store reference to parent GlobalContext for subcommands that need it
        ctx.obj["_parent_context"] = parent_obj

    @dr_app.command("assess")
    @enhanced_cli_error_handler
    def dr_assess(
        ctx: typer.Context,
        dr_region: str | None = typer.Option(
            None,
            "--dr-region",
            help="DR region to check for replicas",
            rich_help_panel="DR Configuration",
        ),
        target_tier: str = typer.Option(
            "tier_2",
            "--target-tier",
            "-t",
            help="Target DR tier",
            rich_help_panel="DR Configuration",
        ),
        # === Output Options ===
        output_file: Path | None = typer.Option(
            None,
            "--output",
            "-o",
            help="Output file path",
            rich_help_panel="Output",
        ),
        report_format: str = typer.Option(
            "console",
            "--format",
            "-f",
            help="Output format: console, json, markdown, html",
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
        """Assess disaster recovery readiness for your infrastructure."""
        from replimap.core.cache_manager import get_or_load_graph, save_graph_to_cache
        from replimap.dr.readiness import DRReadinessAssessor, DRTier

        # Get V3 output manager from parent context
        output = _get_output_manager(ctx)
        stderr_console = output._stderr_console

        # Get profile and region from context
        profile = ctx.obj.get("profile") if ctx.obj else None
        region = ctx.obj.get("region") if ctx.obj else None
        effective_profile = profile or "default"

        # Determine region using consolidated resolution
        effective_region, region_source = resolve_effective_region(
            region, effective_profile
        )

        tier_map = {
            "tier_0": DRTier.TIER_0,
            "tier_1": DRTier.TIER_1,
            "tier_2": DRTier.TIER_2,
            "tier_3": DRTier.TIER_3,
            "tier_4": DRTier.TIER_4,
        }
        target = tier_map.get(target_tier.lower(), DRTier.TIER_2)

        output.panel(
            f"[bold cyan]DR Readiness Assessment[/bold cyan]\n\n"
            f"Primary Region: [cyan]{effective_region}[/] [dim](from {region_source})[/]\n"
            f"DR Region: [cyan]{dr_region or 'Auto-detect'}[/]\n"
            f"Target Tier: [cyan]{target.display_name}[/]",
            border_style="cyan",
        )

        session = get_aws_session(
            effective_profile, effective_region, use_cache=not no_cache
        )

        # Try to load from cache first (global signal handler handles Ctrl-C)
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
            with output.spinner("Scanning primary region..."):
                graph = GraphEngine()
                run_all_scanners(session, effective_region, graph)

            # Save to cache
            save_graph_to_cache(
                graph=graph,
                profile=effective_profile,
                region=effective_region,
                console=stderr_console,
            )

        # Assess DR readiness
        with output.spinner("Assessing DR readiness..."):
            try:
                assessor = DRReadinessAssessor(
                    session,
                    primary_region=effective_region,
                    dr_region=dr_region,
                )
                result = assessor.assess(graph, target_tier=target)
            except Exception as e:
                output.error(f"Error: {e}")
                raise typer.Exit(1)

        output.log("")

        if report_format == "console":
            score_color = (
                "green"
                if result.score >= 80
                else "yellow"
                if result.score >= 60
                else "red"
            )
            output.log(
                f"[bold]DR Readiness Score: [{score_color}]{result.score}/100[/][/bold]"
            )
            output.log(f"Current Tier: [bold]{result.current_tier.display_name}[/bold]")
            output.log(f"Target Tier: {target.display_name}")
            output.log("")

            output.log("[bold]Recovery Objectives[/bold]")
            output.log(f"  Estimated RTO: {result.estimated_rto_minutes} minutes")
            output.log(f"  Estimated RPO: {result.estimated_rpo_minutes} minutes")
            output.log("")

            output.log("[bold]Coverage Analysis[/bold]")
            for category, coverage in result.coverage.items():
                pct = coverage.percentage
                bar = "█" * int(pct / 10) + "░" * (10 - int(pct / 10))
                color = "green" if pct >= 80 else "yellow" if pct >= 50 else "red"
                output.log(f"  {category}: [{color}]{bar}[/] {pct:.0f}%")
            output.log("")

            if result.gaps:
                output.log(
                    f"[bold yellow]Gaps Identified ({len(result.gaps)})[/bold yellow]"
                )
                for gap in result.gaps[:5]:
                    output.log(f"  ⚠ {gap.description}")
                    output.log(f"    [dim]Impact: {gap.impact}[/dim]")
                output.log("")

            if result.recommendations:
                output.log(
                    f"[bold green]Recommendations ({len(result.recommendations)})[/bold green]"
                )
                for rec in result.recommendations[:5]:
                    output.log(f"  ✓ {rec.description}")
                    if rec.estimated_cost:
                        output.log(
                            f"    [dim]Est. cost: ${rec.estimated_cost}/mo[/dim]"
                        )

        elif report_format == "json":
            output_path = output_file or Path("dr_assessment.json")
            with open(output_path, "w") as f:
                json_module.dump(result.to_dict(), f, indent=2)
            output.success(f"Saved to {output_path}")

        elif report_format in ("md", "markdown"):
            output_path = output_file or Path("dr_assessment.md")
            with open(output_path, "w") as f:
                f.write("# DR Readiness Assessment\n\n")
                f.write(f"- Score: {result.score}/100\n")
                f.write(f"- Current Tier: {result.current_tier.display_name}\n")
                f.write(f"- Estimated RTO: {result.estimated_rto_minutes} minutes\n")
                f.write(f"- Estimated RPO: {result.estimated_rpo_minutes} minutes\n")
            output.success(f"Saved to {output_path}")

        elif report_format == "html":
            output_path = output_file or Path("dr_assessment.html")
            html_content = f"""<!DOCTYPE html>
<html>
<head><title>DR Readiness Report</title>
<style>
body {{ font-family: -apple-system, sans-serif; max-width: 800px; margin: 0 auto; padding: 20px; }}
.score {{ font-size: 48px; color: {"green" if result.score >= 80 else "orange" if result.score >= 60 else "red"}; }}
.metric {{ background: #f5f5f5; padding: 10px; margin: 10px 0; border-radius: 4px; }}
</style>
</head>
<body>
<h1>DR Readiness Assessment</h1>
<p class="score">{result.score}/100</p>
<div class="metric"><strong>Current Tier:</strong> {result.current_tier.display_name}</div>
<div class="metric"><strong>Estimated RTO:</strong> {result.estimated_rto_minutes} minutes</div>
<div class="metric"><strong>Estimated RPO:</strong> {result.estimated_rpo_minutes} minutes</div>
<h2>Coverage</h2>
{"".join(f'<div class="metric">{cat}: {cov.percentage:.0f}%</div>' for cat, cov in result.coverage.items())}
</body>
</html>"""
            with open(output_path, "w") as f:
                f.write(html_content)
            output.success(f"Saved to {output_path}")
            open_in_browser(output_path, console=stderr_console)

        output.log("")

    @dr_app.command("scorecard")
    @enhanced_cli_error_handler
    def dr_scorecard(
        ctx: typer.Context,
        output_file: Path | None = typer.Option(
            None,
            "--output",
            "-o",
            help="Output file path",
            rich_help_panel="Output",
        ),
    ) -> None:
        """Generate DR readiness scorecard for all regions."""
        # Get V3 output manager from parent context
        output = _get_output_manager(ctx)

        # Profile available from context for future use
        _ = ctx.obj.get("profile") if ctx.obj else None

        output.log("[dim]Generating multi-region DR scorecard...[/dim]")
        output.warn("This feature requires scanning multiple regions.")
        output.log("Use 'replimap dr assess -r <region>' for single-region assessment.")

    return dr_app


def register(app: typer.Typer, panel: str | None = None) -> None:
    """Register the dr command group with the Typer app."""
    dr_app = create_dr_app()
    app.add_typer(dr_app, name="dr", rich_help_panel=panel)
