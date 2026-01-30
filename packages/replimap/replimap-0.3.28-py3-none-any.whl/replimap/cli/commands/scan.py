"""
Scan command - AWS resource discovery and dependency graph building.

V3 Architecture:
- Uses @enhanced_cli_error_handler for structured error handling
- Uses ctx.obj.output for stdout hygiene (NEVER use console.print directly)
- JSON mode available via global --format flag
"""

from __future__ import annotations

import time
import uuid
from pathlib import Path
from typing import TYPE_CHECKING

import typer
from rich.progress import (
    BarColumn,
    Progress,
    SpinnerColumn,
    TaskProgressColumn,
    TextColumn,
    TimeElapsedColumn,
)

from replimap import __version__
from replimap.cli.errors import enhanced_cli_error_handler
from replimap.cli.utils import (
    get_available_profiles,
    get_aws_session,
    logger,
    print_graph_stats_to_output,
    print_next_steps_to_output,
    resolve_effective_region,
)
from replimap.core import (
    GraphEngine,
    ScanCache,
    ScanFilter,
    SelectionStrategy,
    apply_filter_to_graph,
    apply_selection,
    build_subgraph_from_selection,
    update_cache_from_graph,
)
from replimap.core.cache_manager import save_graph_to_cache
from replimap.core.rate_limiter import get_limiter
from replimap.licensing import Feature, check_scan_allowed, get_scans_remaining
from replimap.licensing.manager import get_license_manager
from replimap.licensing.tracker import get_usage_tracker
from replimap.scanners.base import get_total_scanner_count, run_all_scanners

if TYPE_CHECKING:
    from replimap.cli.context import GlobalContext


def register(app: typer.Typer, panel: str | None = None) -> None:
    """Register the scan command with the app."""

    @app.command(rich_help_panel=panel)
    @enhanced_cli_error_handler
    def scan(
        ctx: typer.Context,
        # === Common Options ===
        profile: str | None = typer.Option(
            None,
            "--profile",
            "-p",
            help="AWS profile name (uses 'default' if not specified)",
        ),
        region: str | None = typer.Option(
            None,
            "--region",
            "-r",
            help="AWS region to scan (uses profile's region or us-east-1)",
        ),
        output_file: Path | None = typer.Option(
            None,
            "--output",
            "-o",
            help="Output path for graph JSON (optional)",
        ),
        # === Selection Options ===
        scope: str | None = typer.Option(
            None,
            "--scope",
            "-s",
            help="Selection scope: vpc:<id>, vpc-name:<pattern>, or VPC ID directly",
            rich_help_panel="Selection",
        ),
        entry: str | None = typer.Option(
            None,
            "--entry",
            "-e",
            help="Entry point: tag:Key=Value, <type>:<name>, or resource ID",
            rich_help_panel="Selection",
        ),
        config: Path | None = typer.Option(
            None,
            "--config",
            "-c",
            help="Path to YAML selection config file",
            rich_help_panel="Selection",
        ),
        vpc: str | None = typer.Option(
            None,
            "--vpc",
            help="Filter by VPC ID(s), comma-separated",
            rich_help_panel="Selection",
        ),
        vpc_name: str | None = typer.Option(
            None,
            "--vpc-name",
            help="Filter by VPC name pattern (supports wildcards)",
            rich_help_panel="Selection",
        ),
        types: str | None = typer.Option(
            None,
            "--types",
            "-t",
            help="Filter by resource types, comma-separated",
            rich_help_panel="Selection",
        ),
        tag: list[str] | None = typer.Option(
            None,
            "--tag",
            help="Select by tag (Key=Value), can be repeated",
            rich_help_panel="Selection",
        ),
        # === Exclusion Options ===
        exclude_types: str | None = typer.Option(
            None,
            "--exclude-types",
            help="Exclude resource types, comma-separated",
            rich_help_panel="Exclusions",
        ),
        exclude_tag: list[str] | None = typer.Option(
            None,
            "--exclude-tag",
            help="Exclude by tag (Key=Value), can be repeated",
            rich_help_panel="Exclusions",
        ),
        exclude_patterns: str | None = typer.Option(
            None,
            "--exclude-patterns",
            help="Exclude by name patterns, comma-separated (supports wildcards)",
            rich_help_panel="Exclusions",
        ),
        # === Cache & Performance ===
        interactive: bool = typer.Option(
            False,
            "--interactive",
            "-i",
            help="Interactive mode - prompt for missing options",
            rich_help_panel="Cache & Performance",
        ),
        no_cache: bool = typer.Option(
            False,
            "--no-cache",
            help="Don't use cached credentials (re-authenticate)",
            rich_help_panel="Cache & Performance",
        ),
        use_scan_cache: bool = typer.Option(
            False,
            "--cache",
            help="Use scan result cache for faster incremental scans",
            rich_help_panel="Cache & Performance",
        ),
        refresh_cache: bool = typer.Option(
            False,
            "--refresh-cache",
            help="Force refresh of scan cache (re-scan all resources)",
            rich_help_panel="Cache & Performance",
        ),
        incremental: bool = typer.Option(
            False,
            "--incremental",
            help="Use incremental scanning (only detect changes since last scan)",
            rich_help_panel="Cache & Performance",
        ),
        # === Auditing & Compliance ===
        trust_center: bool = typer.Option(
            False,
            "--trust-center",
            "--audit",
            help="Enable Trust Center API auditing for compliance",
            rich_help_panel="Auditing & Compliance",
        ),
    ) -> None:
        """Scan AWS resources and build dependency graph.

        \b

        The region is determined in this order:

        1. --region flag (if provided)

        2. Profile's configured region (from ~/.aws/config)

        3. AWS_DEFAULT_REGION environment variable

        4. us-east-1 (fallback)

        \b

        Examples:

            replimap scan --profile prod

            replimap scan --profile prod --region us-west-2

            replimap scan -i  # Interactive mode

            replimap scan --profile prod --output graph.db

        \b

        Selection Examples (Graph-Based - Recommended):

            replimap scan --profile prod --scope vpc:vpc-12345678

            replimap scan --profile prod --scope vpc-name:Production*

            replimap scan --profile prod --entry alb:my-app-alb

            replimap scan --profile prod --entry tag:Application=MyApp

            replimap scan --profile prod --tag Environment=Production

        \b

        Filter Examples (Legacy, still supported):

            replimap scan --profile prod --vpc vpc-12345678

            replimap scan --profile prod --types vpc,subnet,ec2,rds

            replimap scan --profile prod --exclude-types sns,sqs

        \b

        Advanced Examples:

            replimap scan --profile prod --scope vpc:vpc-123
                --exclude-patterns "test-*"

            replimap scan --profile prod --config selection.yaml

        \b

        Cache Examples:

            replimap scan --profile prod --cache  # Use cached results

            replimap scan --profile prod --cache --refresh-cache  # Force refresh

        \b

        Trust Center Examples:

            replimap scan --profile prod --trust-center  # Enable API auditing

            replimap trust-center report  # Generate compliance report

        \b

        Incremental Scanning Examples:

            replimap scan --profile prod  # First scan (full)

            replimap scan --profile prod --incremental  # Subsequent scans (fast)
        """
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
                region_source = "user input"

        # Check license and quotas
        manager = get_license_manager()
        tracker = get_usage_tracker()
        features = manager.current_features

        # Check scan frequency limit (NOT resource count - resources are unlimited!)
        gate_result = check_scan_allowed()
        if not gate_result.allowed:
            output.error(gate_result.prompt)
            raise typer.Exit(1)

        # Show plan badge with dev mode indicator
        if manager.is_dev_mode:
            plan_badge = "[yellow](dev mode)[/]"
        else:
            plan_badge = f"[dim]({manager.current_plan.value})[/]"

        output.panel(
            f"[bold]RepliMap Scanner[/] v{__version__} {plan_badge}\n"
            f"Region: [cyan]{effective_region}[/] [dim](from {region_source})[/]"
            + (
                f"\nProfile: [cyan]{profile}[/]"
                if profile
                else "\nProfile: [cyan]default[/]"
            ),
            title="Configuration",
            border_style="cyan",
        )

        # Get AWS session
        session = get_aws_session(profile, effective_region, use_cache=not no_cache)

        # Get account ID for cache key
        account_id = "unknown"
        if use_scan_cache:
            try:
                sts = session.client("sts")
                account_id = sts.get_caller_identity()["Account"]
            except Exception as e:
                logger.debug(f"Could not get AWS account ID for cache key: {e}")

        # Initialize graph
        graph = GraphEngine()

        # Enable Trust Center auditing if requested (P1-9)
        tc_session_id = None
        if trust_center:
            from replimap.audit import TrustCenter

            tc = TrustCenter.get_instance()
            tc.enable(session)
            tc_session_id = tc.start_session(f"scan_{effective_region}")
            output.progress("Trust Center API auditing enabled")

        # Handle incremental scanning (P3-1)
        if incremental:
            from replimap.scanners.incremental import IncrementalScanner, ScanStateStore

            output.progress("Using incremental scanning mode...")
            state_store = ScanStateStore()
            inc_scanner = IncrementalScanner(session, effective_region, state_store)

            # Detect changes
            changes = inc_scanner.detect_changes()
            if changes:
                created = sum(1 for c in changes if c.change_type.value == "created")
                modified = sum(1 for c in changes if c.change_type.value == "modified")
                deleted = sum(1 for c in changes if c.change_type.value == "deleted")
                output.progress(
                    f"Incremental scan: {created} created, {modified} modified, "
                    f"{deleted} deleted, {len(changes) - created - modified - deleted} unchanged"
                )
            else:
                output.progress("No previous scan state found - performing full scan")

        # Load scan cache if enabled
        scan_cache: ScanCache | None = None
        cached_count = 0

        if use_scan_cache and not refresh_cache:
            scan_cache = ScanCache.load(
                account_id=account_id,
                region=effective_region,
            )
            stats = scan_cache.get_stats()
            cached_count = stats["total_resources"]
            if cached_count > 0:
                output.progress(f"Loaded {cached_count} resources from cache")
                # Populate graph from cache
                from replimap.core import populate_graph_from_cache

                populate_graph_from_cache(scan_cache, graph)

        # Run all registered scanners with progress
        # Use parallel scanning if license allows (ASYNC_SCANNING feature)
        use_parallel = features.has_feature(Feature.ASYNC_SCANNING)
        scan_mode = "parallel" if use_parallel else "sequential"
        scan_start = time.time()

        # If using cache and we have cached data, show that we're doing incremental scan
        if cached_count > 0:
            output.progress("Performing incremental scan for updated resources...")

        total_scanners = get_total_scanner_count()

        # Always show progress bar (--quiet only suppresses INFO logs)
        # Use stderr console for V3 stdout hygiene
        with Progress(
            SpinnerColumn(),
            TextColumn("[bold cyan]{task.description}"),
            BarColumn(bar_width=30),
            TaskProgressColumn(),
            TextColumn(
                "[dim]• {task.fields[resource_count]:,} resources • {task.fields[dep_count]:,} dependencies"
            ),
            TimeElapsedColumn(),
            console=output._stderr_console,
            transient=False,
        ) as progress:
            task = progress.add_task(
                f"Scanning AWS resources ({scan_mode})...",
                total=total_scanners,
                resource_count=0,
                dep_count=0,
            )

            def on_scanner_complete(scanner_name: str, success: bool) -> None:
                """Update progress bar when a scanner completes."""
                progress.update(
                    task,
                    advance=1,
                    resource_count=graph.node_count,
                    dep_count=graph.edge_count,
                )

            results = run_all_scanners(
                session,
                effective_region,
                graph,
                parallel=use_parallel,
                on_scanner_complete=on_scanner_complete,
            )

            # Final update with completion state
            progress.update(
                task,
                description="[bold green]✓ Scan complete",
                resource_count=graph.node_count,
                dep_count=graph.edge_count,
            )
        scan_duration = time.time() - scan_start

        # Update scan cache with new results
        if use_scan_cache:
            if scan_cache is None:
                scan_cache = ScanCache(
                    account_id=account_id,
                    region=effective_region,
                )
            update_cache_from_graph(scan_cache, graph)
            cache_path = scan_cache.save()
            output.progress(f"Scan cache saved to {cache_path}")

        # Apply selection or filters
        # Check if new graph-based selection is being used
        use_new_selection = scope or entry or config

        if use_new_selection:
            # Load config from YAML if provided
            if config and config.exists():
                import yaml

                with open(config) as f:
                    config_data = yaml.safe_load(f)
                selection_strategy = SelectionStrategy.from_dict(
                    config_data.get("selection", {})
                )
            else:
                # Build strategy from CLI args
                selection_strategy = SelectionStrategy.from_cli_args(
                    scope=scope,
                    entry=entry,
                    tag=tag,
                    exclude_types=exclude_types,
                    exclude_patterns=exclude_patterns,
                )

            if not selection_strategy.is_empty():
                output.progress(f"Applying selection: {selection_strategy.describe()}")
                pre_select_count = graph.statistics()["total_resources"]

                # Apply graph-based selection
                selection_result = apply_selection(graph, selection_strategy)

                # Build subgraph from selection
                graph = build_subgraph_from_selection(graph, selection_result)

                post_select_count = graph.statistics()["total_resources"]
                output.progress(
                    f"Selected: {post_select_count} of {pre_select_count} resources "
                    f"({selection_result.summary()['clone']} to clone, "
                    f"{selection_result.summary()['reference']} to reference)"
                )

        else:
            # Legacy filter support (backwards compatibility)
            scan_filter = ScanFilter.from_cli_args(
                vpc=vpc,
                vpc_name=vpc_name,
                types=types,
                tags=tag,
                exclude_types=exclude_types,
                exclude_tags=exclude_tag,
            )

            if not scan_filter.is_empty():
                output.progress(f"Applying filters: {scan_filter.describe()}")
                pre_filter_count = graph.statistics()["total_resources"]
                removed_count = apply_filter_to_graph(
                    graph, scan_filter, retain_dependencies=True
                )
                output.progress(
                    f"Filtered: {pre_filter_count} → "
                    f"{pre_filter_count - removed_count} resources"
                )

        # Get resource stats (no limits - resources are unlimited!)
        stats = graph.statistics()
        resource_count = stats["total_resources"]

        # Record usage
        tracker.record_scan(
            scan_id=str(uuid.uuid4()),
            region=effective_region,
            resource_count=resource_count,
            resource_types=stats.get("resources_by_type", {}),
            duration_seconds=scan_duration,
            profile=profile,
            success=True,
        )

        # Save to graph cache for use by other commands (graph, audit, cost, etc.)
        save_graph_to_cache(
            graph=graph,
            profile=profile or "default",
            region=effective_region,
            console=output._stderr_console,
            vpc=vpc,
            account_id=account_id if use_scan_cache else None,
        )

        # Print rate limiter statistics (uses logger, not console)
        output.log("")
        limiter = get_limiter()
        limiter.print_stats()

        # Report any failed scanners (only show errors, not successes)
        failed = [name for name, err in results.items() if err is not None]
        if failed:
            output.log("")
            output.error(f"Failed scanners: {', '.join(failed)}")
            for name, err in results.items():
                if err:
                    output.log(f"  [red]-[/] {name}: {err}")

        # Print resource breakdown table
        output.log("")
        print_graph_stats_to_output(graph, output)

        # Show next steps
        print_next_steps_to_output(output)

        # Show remaining scans for FREE users
        remaining = get_scans_remaining()
        if remaining >= 0:
            output.progress(
                f"Scans remaining this month: "
                f"{remaining}/{features.max_scans_per_month}"
            )

        # Save output if requested
        if output_file:
            graph.save(output_file)
            output.success(f"Graph saved to {output_file}")

        # Close Trust Center session if enabled (P1-9)
        if trust_center and tc_session_id:
            from replimap.audit import TrustCenter

            tc = TrustCenter.get_instance()
            tc.end_session(tc_session_id)
            session_info = tc.get_session(tc_session_id)
            if session_info:
                output.progress(
                    f"Trust Center: {session_info.total_calls} API calls captured "
                    f"({session_info.read_only_percentage:.1f}% read-only)"
                )
                output.progress(
                    "Run 'replimap trust-center report' to generate compliance report"
                )

        output.log("")
