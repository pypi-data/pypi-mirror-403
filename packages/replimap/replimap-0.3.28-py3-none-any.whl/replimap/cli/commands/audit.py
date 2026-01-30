"""Audit command for RepliMap CLI.

V3 Architecture:
- Uses @enhanced_cli_error_handler for structured error handling
- Console output goes to stderr for stdout hygiene
- JSON mode available via global --format flag
"""

from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path
from typing import TYPE_CHECKING

import typer
from rich.progress import Progress, SpinnerColumn, TextColumn

from replimap.audit.terminal_reporter import print_audit_summary
from replimap.cli.errors import enhanced_cli_error_handler
from replimap.cli.utils import get_aws_session, resolve_effective_region
from replimap.core.browser import open_in_browser
from replimap.licensing import check_audit_ci_mode_allowed, check_audit_fix_allowed
from replimap.ui import print_audit_findings_fomo

if TYPE_CHECKING:
    from replimap.audit.checkov_runner import CheckovResults
    from replimap.cli.context import GlobalContext
    from replimap.cli.output import OutputManager


def _output_audit_json(
    results: CheckovResults,
    output_path: Path,
    region: str,
    profile: str | None,
    vpc_id: str | None,
) -> Path:
    """
    Output audit results as JSON.

    Args:
        results: Checkov scan results
        output_path: Base path for output (will change extension to .json)
        region: AWS region
        profile: AWS profile name
        vpc_id: VPC ID if specified

    Returns:
        Path to the generated JSON file
    """
    from replimap.audit.fix_suggestions import FIX_SUGGESTIONS
    from replimap.audit.soc2_mapping import get_soc2_mapping

    # Build SOC2 summary
    soc2_summary: dict = {}
    for f in results.findings:
        if f.check_result != "FAILED":
            continue
        mapping = get_soc2_mapping(f.check_id)
        if mapping:
            control = mapping.control
            if control not in soc2_summary:
                soc2_summary[control] = {
                    "control": control,
                    "category": mapping.category,
                    "count": 0,
                    "checks": [],
                }
            soc2_summary[control]["count"] += 1
            if f.check_id not in soc2_summary[control]["checks"]:
                soc2_summary[control]["checks"].append(f.check_id)

    # Build JSON output
    json_output = {
        "summary": {
            "score": results.score,
            "grade": results.grade,
            "passed": results.passed,
            "failed": results.failed,
            "skipped": results.skipped,
            "total": results.total,
            "high_severity_count": len(results.high_severity),
        },
        "metadata": {
            "account_id": "N/A",  # Would need to pass this through
            "region": region,
            "profile": profile,
            "vpc_id": vpc_id,
            "generated_at": datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ"),
        },
        "severity_breakdown": {
            "critical": len(results.findings_by_severity["CRITICAL"]),
            "high": len(results.findings_by_severity["HIGH"]),
            "medium": len(results.findings_by_severity["MEDIUM"]),
            "low": len(results.findings_by_severity["LOW"]),
        },
        "findings": [
            {
                "check_id": f.check_id,
                "check_name": f.check_name,
                "severity": f.severity,
                "result": f.check_result,
                "resource": f.resource,
                "file_path": f.file_path,
                "line_range": list(f.file_line_range),
                "soc2_mapping": (
                    {
                        "control": m.control,
                        "category": m.category,
                        "description": m.description,
                    }
                    if (m := get_soc2_mapping(f.check_id))
                    else None
                ),
                "has_fix_suggestion": f.check_id in FIX_SUGGESTIONS,
                "guideline": f.guideline,
            }
            for f in results.findings
            if f.check_result == "FAILED"
        ],
        "soc2_summary": soc2_summary,
    }

    # Determine output path
    json_path = output_path.with_suffix(".json")
    json_path.parent.mkdir(parents=True, exist_ok=True)
    json_path.write_text(json.dumps(json_output, indent=2))

    return json_path


def _generate_remediation(
    results: CheckovResults, output_dir: Path, output: OutputManager
) -> None:
    """
    Generate Terraform remediation code from audit results.

    Args:
        results: Checkov scan results containing findings
        output_dir: Directory to write remediation files
        output: OutputManager for V3 compliance
    """
    from rich.panel import Panel

    from replimap.audit.remediation import RemediationGenerator
    from replimap.audit.remediation.models import RemediationSeverity

    output.log("")
    output._stderr_console.print(
        Panel(
            "[bold blue]Generating Remediation Code[/bold blue]\n\n"
            f"Output: [cyan]{output_dir}[/]",
            border_style="blue",
        )
    )

    generator = RemediationGenerator(results.findings, output_dir)
    plan = generator.generate()

    if plan.files:
        # Write all files
        plan.write_all(output_dir)

        output.log("")
        output._stderr_console.print(
            Panel(
                f"[bold]Remediation Generated[/bold]\n\n"
                f"[green]✓ Files:[/] {len(plan.files)}\n"
                f"[green]✓ Coverage:[/] {plan.coverage_percent}%\n"
                f"[dim]Skipped:[/] {plan.skipped_findings} (no template available)",
                title="Remediation Summary",
                border_style="green",
            )
        )

        # Show by severity
        by_severity = plan.files_by_severity()

        severity_info = []
        if by_severity[RemediationSeverity.CRITICAL]:
            severity_info.append(
                f"[red]CRITICAL: {len(by_severity[RemediationSeverity.CRITICAL])}[/]"
            )
        if by_severity[RemediationSeverity.HIGH]:
            severity_info.append(
                f"[orange1]HIGH: {len(by_severity[RemediationSeverity.HIGH])}[/]"
            )
        if by_severity[RemediationSeverity.MEDIUM]:
            severity_info.append(
                f"[yellow]MEDIUM: {len(by_severity[RemediationSeverity.MEDIUM])}[/]"
            )
        if by_severity[RemediationSeverity.LOW]:
            severity_info.append(
                f"[green]LOW: {len(by_severity[RemediationSeverity.LOW])}[/]"
            )

        if severity_info:
            output.log(f"  Fixes by severity: {' | '.join(severity_info)}")

        output.log("")
        output.success(f"Remediation: {output_dir.absolute()}")
        output.success(f"README: {output_dir.absolute()}/README.md")

        if plan.has_imports:
            output.warn(f"Import script: {output_dir.absolute()}/import.sh")
            output.log("")
            output.log(
                "[dim]Some fixes require terraform import. "
                "Run import.sh before terraform apply.[/dim]"
            )

        if plan.warnings:
            output.log("")
            for warning in plan.warnings:
                output.warn(warning)
    else:
        output.log("")
        output.warn("No remediation templates available for the detected findings.")


def audit_command(
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
        help="AWS region to audit",
    ),
    vpc: str | None = typer.Option(
        None,
        "--vpc",
        "-v",
        help="VPC ID to scope the audit (optional)",
    ),
    output_file: Path = typer.Option(
        Path("./audit_report.html"),
        "--output",
        "-o",
        help="Path for HTML/JSON report",
    ),
    report_format: str = typer.Option(
        "html",
        "--format",
        "-f",
        help="Output format: html or json",
    ),
    # === Output Options ===
    terraform_dir: Path = typer.Option(
        Path("./audit_output"),
        "--terraform-dir",
        "-t",
        help="Directory for generated Terraform files",
        rich_help_panel="Output",
    ),
    open_report: bool = typer.Option(
        True,
        "--open/--no-open",
        help="Open report in browser after generation",
        rich_help_panel="Output",
    ),
    verbose: bool = typer.Option(
        False,
        "--verbose",
        "-V",
        help="Show all findings in terminal (default: summary only)",
        rich_help_panel="Output",
    ),
    # === CI/CD Integration ===
    fail_on_high: bool = typer.Option(
        False,
        "--fail-on-high",
        help="Exit with code 1 if HIGH/CRITICAL issues found (for CI/CD)",
        rich_help_panel="CI/CD Integration",
    ),
    fail_on_score: int | None = typer.Option(
        None,
        "--fail-on-score",
        help="Exit with code 1 if score below threshold (e.g., --fail-on-score 70)",
        rich_help_panel="CI/CD Integration",
    ),
    # === Remediation ===
    fix: bool = typer.Option(
        False,
        "--fix",
        help="Generate Terraform remediation code for findings",
        rich_help_panel="Remediation",
    ),
    fix_output: Path = typer.Option(
        Path("./remediation"),
        "--fix-output",
        help="Directory for remediation Terraform files",
        rich_help_panel="Remediation",
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
    """Run security audit on AWS infrastructure.

    \b

    Scans your AWS environment, generates a forensic Terraform snapshot,
    runs Checkov security analysis, and produces an HTML report with
    findings mapped to SOC2 controls.

    \b

    Requires Checkov to be installed: pip install checkov

    \b

    Examples:

        replimap audit --region us-east-1

        replimap audit -p prod -r ap-southeast-2 -v vpc-abc123

        replimap audit -r us-west-2 --no-open

        replimap audit -r us-east-1 --fail-on-high --no-open  # CI/CD mode

        replimap audit -r us-east-1 --fail-on-score 70 --no-open

        replimap audit -r us-east-1 --format json

        replimap audit -r us-east-1 --fix --fix-output ./remediation

        replimap audit -r us-east-1 --verbose  # Show all findings
    """
    from rich.panel import Panel

    from replimap.audit import AuditEngine, CheckovNotInstalledError

    # Get V3 context
    gctx: GlobalContext = ctx.obj
    output = gctx.output

    # Determine region: flag > profile config > default
    effective_region, region_source = resolve_effective_region(region, profile)

    output.log("")
    output._stderr_console.print(
        Panel(
            f"[bold blue]RepliMap Security Audit[/bold blue]\n\n"
            f"Region: [cyan]{effective_region}[/] [dim](from {region_source})[/]\n"
            f"Profile: [cyan]{profile or 'default'}[/]\n"
            + (f"VPC: [cyan]{vpc}[/]\n" if vpc else "")
            + f"Output: [cyan]{output_file}[/]\n"
            f"Terraform: [cyan]{terraform_dir}[/]",
            border_style="blue",
        )
    )

    # Get AWS session
    session = get_aws_session(profile, effective_region, use_cache=not no_cache)

    # Check Checkov is installed
    try:
        engine = AuditEngine(
            session=session,
            region=effective_region,
            profile=profile,
            vpc_id=vpc,
        )
    except CheckovNotInstalledError:
        output.log("")
        output._stderr_console.print(
            Panel(
                "[red]Checkov is not installed.[/]\n\n"
                "Install Checkov with:\n"
                "  [bold]pipx install checkov[/]  (recommended)\n\n"
                "Or:\n"
                "  [bold]pip install checkov[/]",
                title="Missing Dependency",
                border_style="red",
            )
        )
        raise typer.Exit(1)

    # Try to load from cache first
    from replimap.core import GraphEngine
    from replimap.core.cache_manager import get_or_load_graph, save_graph_to_cache
    from replimap.scanners.base import run_all_scanners

    # Try to load from cache first (global signal handler handles Ctrl-C)
    output.log("")
    stderr_console = output._stderr_console
    cached_graph, cache_meta = get_or_load_graph(
        profile=profile or "default",
        region=effective_region,
        console=stderr_console,
        refresh=refresh,
        vpc=vpc,
    )

    # If no cached graph, do the scan and cache it
    graph = cached_graph
    if graph is None:
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=stderr_console,
        ) as progress:
            task = progress.add_task("Scanning AWS resources...", total=None)
            graph = GraphEngine()
            run_all_scanners(session, effective_region, graph)
            progress.update(task, completed=True)

        # Apply VPC filter if specified
        if vpc:
            from replimap.core import ScanFilter, apply_filter_to_graph

            filter_config = ScanFilter(
                vpc_ids=[vpc],
                include_vpc_resources=True,
            )
            graph = apply_filter_to_graph(graph, filter_config)

        # Save to cache (cache is per vpc if specified)
        save_graph_to_cache(
            graph=graph,
            profile=profile or "default",
            region=effective_region,
            console=stderr_console,
            vpc=vpc,
        )

    # Apply VPC filter if specified (for cached graph)
    if cached_graph is not None and vpc:
        from replimap.core import ScanFilter, apply_filter_to_graph

        filter_config = ScanFilter(
            vpc_ids=[vpc],
            include_vpc_resources=True,
        )
        graph = apply_filter_to_graph(graph, filter_config)

    # Run audit with the graph (skip scanning since we have it)
    output.log("")
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=stderr_console,
    ) as progress:
        task = progress.add_task("Running security checks...", total=None)

        try:
            results, report_path = engine.run(
                output_dir=terraform_dir,
                report_path=output_file,
                skip_scan=True,
                graph=graph,
            )
        except Exception as e:
            from rich.panel import Panel

            progress.stop()
            output.log("")
            stderr_console.print(
                Panel(
                    f"[red]Audit failed:[/]\n{e}",
                    title="Error",
                    border_style="red",
                )
            )
            raise typer.Exit(1)

        progress.update(task, completed=True)

    # Handle JSON output format
    if report_format.lower() == "json":
        json_path = _output_audit_json(
            results, output_file, effective_region, profile, vpc
        )
        output.log("")
        output.success(f"JSON Report: {json_path.absolute()}")
        output.success(f"Terraform: {terraform_dir.absolute()}")
    else:
        # Display results based on verbosity
        output.log("")
        if verbose:
            # Verbose mode: Show all findings with FOMO design
            # This shows ALL issue titles (even for FREE users)
            # First CRITICAL gets 2-line remediation preview
            # Remaining remediation details are gated by plan
            print_audit_findings_fomo(results, console_out=stderr_console)
        else:
            # Default: Compact summary + top 5 critical issues
            print_audit_summary(results, stderr_console, verbose=False)

        # Output paths
        output.log("")
        output.success(f"Report: {report_path.absolute()}")
        output.success(f"Terraform: {terraform_dir.absolute()}")

        # Open report in browser (only for HTML format)
        if open_report:
            output.log("")
            open_in_browser(report_path, console=stderr_console)

    # Generate remediation if requested (PRO+ feature)
    if fix:
        fix_gate = check_audit_fix_allowed()
        if not fix_gate.allowed:
            output.log(fix_gate.prompt)
            raise typer.Exit(1)
        if results.findings:
            _generate_remediation(results, fix_output, output)

    # CI/CD checks (PRO+ feature)
    exit_code = 0

    if fail_on_high or fail_on_score is not None:
        ci_gate = check_audit_ci_mode_allowed()
        if not ci_gate.allowed:
            output.log(ci_gate.prompt)
            raise typer.Exit(1)

    if fail_on_high and results.high_severity:
        output.log("")
        output.error(
            f"CI/CD FAILED: {len(results.high_severity)} HIGH/CRITICAL issues found"
        )
        for f in results.high_severity[:5]:
            output.log(f"   • {f.check_id}: {f.check_name}")
        if len(results.high_severity) > 5:
            output.log(f"   ... and {len(results.high_severity) - 5} more")
        exit_code = 1

    if fail_on_score is not None and results.score < fail_on_score:
        output.log("")
        output.error(
            f"CI/CD FAILED: Score {results.score} below threshold {fail_on_score}"
        )
        exit_code = 1

    if exit_code == 0 and (fail_on_high or fail_on_score is not None):
        output.log("")
        output.success("CI/CD PASSED")

    output.log("")

    if exit_code != 0:
        raise typer.Exit(exit_code)


def register(app: typer.Typer, panel: str | None = None) -> None:
    """Register the audit command with the Typer app."""
    app.command(name="audit", rich_help_panel=panel)(
        enhanced_cli_error_handler(audit_command)
    )
