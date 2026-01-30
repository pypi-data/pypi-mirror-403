"""Snapshot command group for RepliMap CLI.

V3 Architecture:
- Uses @enhanced_cli_error_handler for structured error handling
- Uses ctx.obj.output for stdout hygiene (stderr for progress, stdout for results)
- JSON mode available via global --format flag
"""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

import typer
from rich.prompt import Confirm
from rich.table import Table

from replimap.cli.errors import enhanced_cli_error_handler
from replimap.cli.utils import get_aws_session, resolve_effective_region

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


def create_snapshot_app() -> typer.Typer:
    """Create and return the snapshot subcommand app."""
    snapshot_app = typer.Typer(
        help="Infrastructure snapshots for change tracking",
        context_settings={"help_option_names": ["-h", "--help"]},
    )

    @snapshot_app.callback()
    def snapshot_callback(
        ctx: typer.Context,
        profile: str | None = typer.Option(
            None, "--profile", "-p", help="AWS profile name"
        ),
        region: str | None = typer.Option(None, "--region", "-r", help="AWS region"),
    ) -> None:
        """
        Infrastructure snapshots for change tracking.

        Common options (--profile, --region) can be specified before the subcommand
        or at the global level (e.g., replimap -p prod snapshot save).

        Examples:
            replimap -p prod snapshot save -n "before-deploy"
            replimap snapshot -p prod save -n "before-deploy"
            replimap snapshot -p prod list
            replimap snapshot -p prod diff --baseline v1 --current v2
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

    @snapshot_app.command("save")
    @enhanced_cli_error_handler
    def snapshot_save(
        ctx: typer.Context,
        name: str = typer.Option(..., "--name", "-n", help="Snapshot name"),
        vpc: str | None = typer.Option(
            None,
            "--vpc",
            "-v",
            help="VPC ID to scope the snapshot (optional)",
            rich_help_panel="Selection",
        ),
        output_file: Path | None = typer.Option(
            None,
            "--output",
            "-o",
            help="Custom output file path",
            rich_help_panel="Output",
        ),
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
        """Save an infrastructure snapshot."""
        from replimap.core import GraphEngine
        from replimap.core.cache_manager import get_or_load_graph, save_graph_to_cache
        from replimap.scanners.base import run_all_scanners
        from replimap.snapshot import InfraSnapshot, ResourceSnapshot, SnapshotStore

        # Get V3 output manager from parent context
        output = _get_output_manager(ctx)
        stderr_console = output._stderr_console

        # Get profile and region from context (set by callback)
        profile = ctx.obj.get("profile") if ctx.obj else None
        region = ctx.obj.get("region") if ctx.obj else None
        effective_profile = profile or "default"

        # Determine region using consolidated resolution
        effective_region, region_source = resolve_effective_region(
            region, effective_profile
        )

        output.log("")
        config_content = (
            f"[bold blue]📸 Creating Infrastructure Snapshot[/bold blue]\n\n"
            f"Name: [cyan]{name}[/]\n"
            f"Region: [cyan]{effective_region}[/] [dim](from {region_source})[/]\n"
            f"Profile: [cyan]{effective_profile}[/]"
            + (f"\nVPC: [cyan]{vpc}[/]" if vpc else "")
        )
        output.panel(config_content, border_style="blue")

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
            vpc=vpc,
        )

        if cached_graph is not None:
            graph = cached_graph
        else:
            with output.spinner("Scanning infrastructure..."):
                graph = GraphEngine()
                run_all_scanners(session, effective_region, graph)

            # Save to cache
            save_graph_to_cache(
                graph=graph,
                profile=effective_profile,
                region=effective_region,
                console=stderr_console,
                vpc=vpc,
            )

        if vpc:
            filtered_resources = []
            for resource in graph.get_all_resources():
                resource_vpc = resource.config.get("vpc_id") or resource.config.get(
                    "VpcId"
                )
                if (
                    resource_vpc == vpc
                    or resource.id == vpc
                    or vpc in resource.dependencies
                ):
                    filtered_resources.append(resource)
            resources = filtered_resources
        else:
            resources = graph.get_all_resources()

        output.log(f"[dim]Found {len(resources)} resources[/dim]")

        resource_snapshots = []
        for r in resources:
            rs = ResourceSnapshot(
                id=r.id,
                type=str(r.resource_type),
                arn=r.arn,
                name=r.original_name,
                region=effective_region,
                config=r.config,
                tags=r.tags,
            )
            resource_snapshots.append(rs)

        snapshot = InfraSnapshot(
            name=name,
            region=effective_region,
            vpc_id=vpc,
            profile=effective_profile,
            resources=resource_snapshots,
        )

        if output_file:
            snapshot.save(output_file)
            filepath = output_file
        else:
            store = SnapshotStore()
            filepath = store.save(snapshot)

        output.log("")
        output.panel(
            f"[bold]Snapshot Saved[/bold]\n\n"
            f"[green]✓ Name:[/] {snapshot.name}\n"
            f"[green]✓ Resources:[/] {snapshot.resource_count}\n"
            f"[green]✓ Created:[/] {snapshot.created_at[:19]}\n"
            f"[green]✓ Path:[/] {filepath}",
            title="📸 Snapshot Complete",
            border_style="green",
        )

        by_type = snapshot.resource_types()
        if by_type:
            output.log("")
            output.log("[bold]Resources by Type:[/bold]")
            for rtype, count in sorted(by_type.items(), key=lambda x: -x[1])[:10]:
                output.log(f"  {rtype}: {count}")
            if len(by_type) > 10:
                output.log(f"  [dim]... and {len(by_type) - 10} more types[/dim]")

    @snapshot_app.command("list")
    @enhanced_cli_error_handler
    def snapshot_list(
        ctx: typer.Context,
        profile: str | None = typer.Option(
            None, "--profile", "-p", help="AWS profile name (for filtering)"
        ),
        region: str | None = typer.Option(
            None, "--region", "-r", help="AWS region (for filtering)"
        ),
    ) -> None:
        """List saved snapshots."""
        from replimap.snapshot import SnapshotStore

        # Get V3 output manager from parent context
        output = _get_output_manager(ctx)
        stderr_console = output._stderr_console

        # Priority: local option > snapshot callback > global context
        ctx_region = ctx.obj.get("region") if ctx.obj else None
        effective_region = region or ctx_region

        store = SnapshotStore()
        snapshots = store.list(region=effective_region)

        if not snapshots:
            output.log("[dim]No snapshots found[/dim]")
            return

        table = Table(title="Saved Snapshots")
        table.add_column("Name")
        table.add_column("Region")
        table.add_column("Resources", justify="right")
        table.add_column("Created")

        for snap in snapshots:
            table.add_row(
                snap["name"],
                snap.get("region", "-"),
                str(snap.get("resource_count", 0)),
                snap.get("created_at", "-")[:19],
            )

        stderr_console.print(table)

    @snapshot_app.command("show")
    @enhanced_cli_error_handler
    def snapshot_show(
        ctx: typer.Context,
        name: str = typer.Argument(..., help="Snapshot name or path"),
        profile: str | None = typer.Option(
            None, "--profile", "-p", help="AWS profile name (unused, for consistency)"
        ),
        region: str | None = typer.Option(
            None, "--region", "-r", help="AWS region (unused, for consistency)"
        ),
    ) -> None:
        """Show snapshot details."""
        from replimap.snapshot import SnapshotStore

        # Get V3 output manager from parent context
        output = _get_output_manager(ctx)

        store = SnapshotStore()
        snapshot = store.load(name)

        if not snapshot:
            output.error(f"Snapshot not found: {name}")
            raise typer.Exit(1)

        output.log("")
        output.log(f"[bold]Snapshot: {snapshot.name}[/bold]")
        output.log("")
        output.log(f"Created: {snapshot.created_at[:19]}")
        output.log(f"Region: {snapshot.region}")
        output.log(f"Profile: {snapshot.profile}")
        if snapshot.vpc_id:
            output.log(f"VPC: {snapshot.vpc_id}")
        output.log(f"Resources: {snapshot.resource_count}")
        output.log(f"Version: {snapshot.version}")

        by_type = snapshot.resource_types()
        if by_type:
            output.log("")
            output.log("[bold]Resources by Type:[/bold]")
            for rtype, count in sorted(by_type.items(), key=lambda x: -x[1]):
                output.log(f"  {rtype}: {count}")

    @snapshot_app.command("diff")
    @enhanced_cli_error_handler
    def snapshot_diff(
        ctx: typer.Context,
        baseline: str = typer.Option(
            ..., "--baseline", "-b", help="Baseline snapshot name or path"
        ),
        current: str | None = typer.Option(
            None,
            "--current",
            "-c",
            help="Current snapshot to compare (or live scan if not specified)",
        ),
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
        verbose: bool = typer.Option(
            False,
            "--verbose",
            "-V",
            help="Show detailed changes",
            rich_help_panel="Output",
        ),
        fail_on_change: bool = typer.Option(
            False,
            "--fail-on-change",
            help="Exit with code 1 if any changes detected",
            rich_help_panel="CI/CD Integration",
        ),
        fail_on_critical: bool = typer.Option(
            False,
            "--fail-on-critical",
            help="Exit with code 1 if critical changes detected",
            rich_help_panel="CI/CD Integration",
        ),
        no_cache: bool = typer.Option(
            False,
            "--no-cache",
            help="Don't use cached credentials",
            rich_help_panel="Cache & Performance",
        ),
    ) -> None:
        """Compare snapshots to find infrastructure changes."""
        from replimap.core import GraphEngine
        from replimap.scanners.base import run_all_scanners
        from replimap.snapshot import (
            InfraSnapshot,
            ResourceSnapshot,
            SnapshotDiffer,
            SnapshotReporter,
            SnapshotStore,
        )

        # Get V3 output manager from parent context
        output = _get_output_manager(ctx)

        # Get profile and region from context
        profile = ctx.obj.get("profile") if ctx.obj else None
        region = ctx.obj.get("region") if ctx.obj else None

        store = SnapshotStore()
        baseline_snap = store.load(baseline)
        if not baseline_snap:
            output.error(f"Baseline snapshot not found: {baseline}")
            raise typer.Exit(1)

        # Use baseline region if not specified
        if not region:
            region = baseline_snap.region

        output.log("")
        output.panel(
            f"[bold blue]📸 Comparing Infrastructure Snapshots[/bold blue]\n\n"
            f"Baseline: [cyan]{baseline_snap.name}[/] ({baseline_snap.created_at[:19]})\n"
            f"Region: [cyan]{region}[/]",
            border_style="blue",
        )

        if current:
            current_snap = store.load(current)
            if not current_snap:
                output.error(f"Current snapshot not found: {current}")
                raise typer.Exit(1)
            output.log(
                f"Current: [cyan]{current_snap.name}[/] ({current_snap.created_at[:19]})"
            )
        else:
            output.log("")
            output.log("[dim]Scanning current infrastructure...[/dim]")

            session = get_aws_session(profile, region, use_cache=not no_cache)

            # Global signal handler handles Ctrl-C
            with output.spinner("Scanning..."):
                graph = GraphEngine()
                run_all_scanners(session, region, graph)

            if baseline_snap.vpc_id:
                filtered_resources = []
                for resource in graph.get_all_resources():
                    resource_vpc = resource.config.get("vpc_id") or resource.config.get(
                        "VpcId"
                    )
                    if (
                        resource_vpc == baseline_snap.vpc_id
                        or resource.id == baseline_snap.vpc_id
                        or baseline_snap.vpc_id in resource.dependencies
                    ):
                        filtered_resources.append(resource)
                resources = filtered_resources
            else:
                resources = graph.get_all_resources()

            resource_snapshots = [
                ResourceSnapshot(
                    id=r.id,
                    type=str(r.resource_type),
                    arn=r.arn,
                    name=r.original_name,
                    region=region,
                    config=r.config,
                    tags=r.tags,
                )
                for r in resources
            ]

            current_snap = InfraSnapshot(
                name="current",
                region=region,
                vpc_id=baseline_snap.vpc_id,
                resources=resource_snapshots,
            )

        output.log("")
        differ = SnapshotDiffer()
        diff_result = differ.diff(baseline_snap, current_snap)

        reporter = SnapshotReporter()

        if report_format == "console":
            reporter.to_console(diff_result, verbose=verbose)
        elif report_format == "json":
            output_path = output_file or Path("snapshot_diff.json")
            reporter.to_json(diff_result, output_path)
        elif report_format in ("md", "markdown"):
            output_path = output_file or Path("snapshot_diff.md")
            reporter.to_markdown(diff_result, output_path)
        elif report_format == "html":
            output_path = output_file or Path("snapshot_diff.html")
            reporter.to_html(diff_result, output_path)
        else:
            reporter.to_console(diff_result, verbose=verbose)
            if output_file:
                reporter.to_json(diff_result, output_file)

        exit_code = 0

        if fail_on_change and diff_result.has_changes:
            output.log("")
            output.error(f"CI/CD FAILED: {diff_result.total_changes} changes detected")
            exit_code = 1

        if fail_on_critical and diff_result.has_critical_changes:
            output.log("")
            output.error(
                f"CI/CD FAILED: {len(diff_result.critical_changes)} critical/high changes detected"
            )
            exit_code = 1

        if exit_code == 0 and (fail_on_change or fail_on_critical):
            output.log("")
            output.success("CI/CD PASSED")

        output.log("")

        if exit_code != 0:
            raise typer.Exit(exit_code)

    @snapshot_app.command("delete")
    @enhanced_cli_error_handler
    def snapshot_delete(
        ctx: typer.Context,
        name: str = typer.Argument(..., help="Snapshot name to delete"),
        force: bool = typer.Option(False, "--force", "-f", help="Skip confirmation"),
        profile: str | None = typer.Option(
            None, "--profile", "-p", help="AWS profile name (unused, for consistency)"
        ),
        region: str | None = typer.Option(
            None, "--region", "-r", help="AWS region (unused, for consistency)"
        ),
    ) -> None:
        """Delete a saved snapshot."""
        from replimap.snapshot import SnapshotStore

        # Get V3 output manager from parent context
        output = _get_output_manager(ctx)

        store = SnapshotStore()

        if not store.exists(name):
            output.error(f"Snapshot not found: {name}")
            raise typer.Exit(1)

        if not force:
            if not Confirm.ask(f"Delete snapshot '{name}'?"):
                output.log("[dim]Cancelled[/dim]")
                raise typer.Exit(0)

        if store.delete(name):
            output.success(f"Deleted snapshot: {name}")
        else:
            output.error(f"Failed to delete snapshot: {name}")
            raise typer.Exit(1)

    return snapshot_app


def register(app: typer.Typer, panel: str | None = None) -> None:
    """Register the snapshot command group with the Typer app."""
    snapshot_app = create_snapshot_app()
    app.add_typer(snapshot_app, name="snapshot", rich_help_panel=panel)
