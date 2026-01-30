"""
Snapshot table display with pagination and FOMO styling.

V3 Architecture:
- Functions accept optional console_out for CLI integration
- When called from commands, pass ctx.obj.output's console for stdout hygiene
- Default uses module console for standalone usage
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from rich import box
from rich.console import Console
from rich.table import Table
from rich.text import Text

if TYPE_CHECKING:
    from replimap.core.unified_storage import (
        PaginatedResult,
        Snapshot,
        SnapshotSummary,
    )

from .console import console as default_console
from .snapshot_panels import show_locked_snapshots_fomo


def show_snapshot_list(
    result: PaginatedResult[Snapshot],
    plan: str,
    summary: SnapshotSummary,
    console_out: Console | None = None,
) -> None:
    """
    Display paginated snapshot list with FOMO.

    Args:
        result: Paginated snapshot results
        plan: Current user plan
        summary: Snapshot summary with lock counts
        console_out: Optional console override for CLI integration

    Shows:
    1. Header with plan retention
    2. Pagination info ("Showing 1-50 of 10,482")
    3. Snapshot table with lock styling
    4. Pagination hint if more available
    5. FOMO panel if locked snapshots exist
    """
    from replimap.core.unified_storage.sqlite_backend import SQLiteBackend

    output = console_out or default_console
    retention = SQLiteBackend.RETENTION_DAYS.get(plan.lower(), 7)

    # Header
    output.print()
    output.print(
        f"[bold]📸 Snapshots[/bold] "
        f"[dim]({retention}-day retention on {plan.upper()})[/dim]"
    )

    # Pagination info
    if result.total_count > 0:
        start, end = result.get_display_range()
        output.print(f"[dim]Showing {start}-{end} of {result.total_count:,}[/dim]")
    output.print()

    # Table
    if result.items:
        table = create_snapshot_table(result.items)
        output.print(table)
    else:
        output.print(
            "[dim]No snapshots found. Run 'replimap scan' to create one.[/dim]"
        )
        return

    # Pagination hint
    if result.has_more:
        remaining = result.total_count - (result.offset + len(result.items))
        output.print()
        output.print(
            f"[dim]... and {remaining:,} more. "
            f"Use --limit {result.limit * 2} or --all to see more.[/dim]"
        )

    # FOMO panel (DYNAMIC based on current plan)
    if summary.locked_count > 0:
        output.print()
        show_locked_snapshots_fomo(summary, plan, console_out=output)


def create_snapshot_table(snapshots: list[Snapshot]) -> Table:
    """Create Rich table with FOMO styling for locked rows."""
    table = Table(
        box=box.ROUNDED,
        show_header=True,
        header_style="bold cyan",
    )

    table.add_column("ID", style="dim", width=10)
    table.add_column("Name", width=20)
    table.add_column("Date", width=18)
    table.add_column("Resources", justify="right", width=10)
    table.add_column("Account", width=14)
    table.add_column("Status", justify="center", width=14)

    for snap in snapshots:
        if snap.is_locked:
            # LOCKED: Dim style for FOMO effect
            table.add_row(
                Text(f"{snap.id[:8]}...", style="dim"),
                Text(snap.name or "-", style="dim"),
                Text(
                    snap.created_at.strftime("%Y-%m-%d %H:%M")
                    if snap.created_at
                    else "-",
                    style="dim",
                ),
                Text(str(snap.resource_count), style="dim"),
                Text(
                    f"{snap.aws_account_id[:12]}..." if snap.aws_account_id else "-",
                    style="dim",
                ),
                Text("🔒 LOCKED", style="yellow"),
            )
        else:
            # AVAILABLE: Normal style
            table.add_row(
                f"{snap.id[:8]}...",
                snap.name or "-",
                snap.created_at.strftime("%Y-%m-%d %H:%M") if snap.created_at else "-",
                str(snap.resource_count),
                f"{snap.aws_account_id[:12]}..." if snap.aws_account_id else "-",
                Text("✅ Available", style="green"),
            )

    return table


def show_summary_table(
    summary: SnapshotSummary,
    plan: str,
    console_out: Console | None = None,
) -> None:
    """
    Display snapshot summary.

    Args:
        summary: Snapshot summary with lock counts
        plan: Current user plan
        console_out: Optional console override for CLI integration
    """
    from replimap.core.unified_storage.sqlite_backend import SQLiteBackend

    output = console_out or default_console
    retention = SQLiteBackend.RETENTION_DAYS.get(plan.lower(), 7)

    table = Table(
        box=box.SIMPLE,
        show_header=False,
        padding=(0, 2),
    )

    table.add_column("Label", style="dim")
    table.add_column("Value", style="bold")

    table.add_row("Total Snapshots", str(summary.total_count))
    table.add_row("Available", f"[green]{summary.available_count}[/green]")

    if summary.locked_count > 0:
        table.add_row("Locked", f"[yellow]{summary.locked_count}[/yellow]")

    table.add_row("Retention", f"{retention} days ({plan})")

    output.print(table)
