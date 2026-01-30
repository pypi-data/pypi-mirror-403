"""
Snapshot FOMO panels with DYNAMIC upgrade messaging.

CRITICAL: Upgrade tier determined by current plan, NOT hardcoded.

V3 Architecture:
- Functions accept optional console_out for CLI integration
- When called from commands, pass ctx.obj.output's console for stdout hygiene
- Default uses module console for standalone usage
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import TYPE_CHECKING

from rich.console import Console
from rich.panel import Panel

if TYPE_CHECKING:
    from replimap.core.unified_storage import SnapshotSummary

from .console import console as default_console


def show_locked_snapshots_fomo(
    summary: SnapshotSummary,
    current_plan: str,
    console_out: Console | None = None,
) -> None:
    """
    Display FOMO panel with DYNAMIC upgrade messaging.

    Args:
        summary: Snapshot summary with lock counts
        current_plan: Current user plan (community, pro, team, sovereign)
        console_out: Optional console override for CLI integration

    Upgrade paths:
    - COMMUNITY -> "Upgrade to PRO"
    - PRO -> "Upgrade to TEAM"
    - TEAM -> "Upgrade to SOVEREIGN"
    - SOVEREIGN -> Special panel (top tier)
    """
    output = console_out or default_console

    if summary.locked_count == 0:
        return

    # Ensure upgrade info is set
    summary.set_upgrade_info(current_plan)

    if summary.unlock_plan is None:
        # SOVEREIGN - top tier
        _show_sovereign_panel(summary, output)
        return

    # Get retention for current plan
    from replimap.core.unified_storage.sqlite_backend import SQLiteBackend

    current_retention = SQLiteBackend.RETENTION_DAYS.get(current_plan.lower(), 7)

    lines = [
        f"[bold yellow]🔒 {summary.locked_count:,} snapshot"
        f"{'s' if summary.locked_count != 1 else ''} locked[/bold yellow]",
        "",
        "[dim]Your data is safe, encrypted, and stored locally.[/dim]",
        f"[dim]It is outside your {current_plan.upper()} plan's "
        f"{current_retention}-day retention.[/dim]",
        "",
    ]

    # Date range of locked data
    if summary.newest_locked:
        try:
            now = datetime.now(UTC)
            newest = summary.newest_locked
            if newest.tzinfo is None:
                newest = newest.replace(tzinfo=UTC)
            age_days = (now - newest).days
            lines.append(
                f"[dim]Most recent locked: {newest.strftime('%Y-%m-%d')} "
                f"({age_days} days ago)[/dim]"
            )
            lines.append("")
        except (ValueError, AttributeError):
            # Skip date display if parsing fails
            lines.append("")

    # Dynamic upgrade messaging
    lines.extend(
        [
            f"[bold]Unlock with {summary.unlock_plan.upper()} "
            f"(${summary.unlock_price}/mo):[/bold]",
            f"✓ {summary.unlock_retention_days}-day history retention",
            f"✓ Access all {summary.locked_count:,} locked snapshots instantly",
        ]
    )

    # Tier-specific benefits
    if summary.unlock_plan == "pro":
        lines.extend(
            [
                "✓ Cost Diff between snapshots",
                "✓ Remove watermarks from exports",
            ]
        )
    elif summary.unlock_plan == "team":
        lines.extend(
            [
                "✓ Drift detection & multi-channel alerts",
                "✓ CI/CD --fail-on-drift blocking",
            ]
        )
    elif summary.unlock_plan == "sovereign":
        lines.extend(
            [
                "✓ Digital signatures for audit",
                "✓ Offline air-gap deployment",
            ]
        )

    lines.extend(
        [
            "",
            f"[dim]→ replimap upgrade {summary.unlock_plan}[/dim]",
        ]
    )

    output.print(
        Panel(
            "\n".join(lines),
            border_style="yellow",
            padding=(1, 2),
        )
    )


def _show_sovereign_panel(summary: SnapshotSummary, output: Console) -> None:
    """Special panel for SOVEREIGN users (top tier)."""
    lines = [
        f"[bold yellow]🔒 {summary.locked_count:,} snapshot"
        f"{'s' if summary.locked_count != 1 else ''} locked[/bold yellow]",
        "",
        "[dim]Your data is safe and stored locally.[/dim]",
        "[dim]These snapshots are older than your SOVEREIGN plan's "
        "365-day retention.[/dim]",
        "",
        "[bold]You're on the top tier.[/bold]",
        "Contact support for extended archive options.",
        "",
        "[dim]→ support@replimap.com[/dim]",
    ]

    output.print(
        Panel(
            "\n".join(lines),
            border_style="blue",
            padding=(1, 2),
        )
    )


def show_snapshot_locked_error(
    snapshot_id: str,
    current_plan: str,
    created_at: datetime,
    console_out: Console | None = None,
) -> None:
    """
    Display error when accessing locked snapshot.

    Args:
        snapshot_id: The locked snapshot ID
        current_plan: Current user plan
        created_at: When the snapshot was created
        console_out: Optional console override for CLI integration
    """
    from replimap.core.unified_storage import get_next_tier
    from replimap.core.unified_storage.sqlite_backend import SQLiteBackend

    output = console_out or default_console
    current_retention = SQLiteBackend.RETENTION_DAYS.get(current_plan.lower(), 7)
    next_plan, next_price, next_retention = get_next_tier(current_plan)

    try:
        now = datetime.now(UTC)
        if created_at.tzinfo is None:
            created_at = created_at.replace(tzinfo=UTC)
        age_days = (now - created_at).days
    except (ValueError, AttributeError):
        age_days = 0

    lines = [
        "[bold red]🔒 Snapshot Locked[/bold red]",
        "",
        f"[dim]Snapshot ID:[/dim] {snapshot_id}",
        f"[dim]Created:[/dim] {created_at.strftime('%Y-%m-%d %H:%M')} "
        f"({age_days} days ago)",
        "",
        f"This snapshot is outside your {current_plan.upper()} plan's",
        f"{current_retention}-day retention window.",
        "",
        "[bold]Your data is safe and can be unlocked.[/bold]",
    ]

    if next_plan:
        lines.extend(
            [
                "",
                f"[bold]Upgrade to {next_plan.upper()} (${next_price}/mo):[/bold]",
                f"✓ {next_retention}-day history retention",
                "✓ Unlock this and all older snapshots",
                "",
                f"[dim]→ replimap upgrade {next_plan}[/dim]",
            ]
        )

    output.print(
        Panel(
            "\n".join(lines),
            border_style="red",
            padding=(1, 2),
        )
    )


def show_upgrade_panel(
    current_plan: str,
    feature_name: str = "this feature",
    console_out: Console | None = None,
) -> None:
    """
    Display generic upgrade panel.

    Args:
        current_plan: Current user plan
        feature_name: Name of the feature requiring upgrade
        console_out: Optional console override for CLI integration
    """
    from replimap.core.unified_storage import get_next_tier

    output = console_out or default_console
    next_plan, next_price, _ = get_next_tier(current_plan)

    if next_plan is None:
        return

    lines = [
        f"[bold yellow]🔒 {feature_name} requires upgrade[/bold yellow]",
        "",
        f"Your {current_plan.upper()} plan doesn't include {feature_name}.",
        "",
        f"[bold]Upgrade to {next_plan.upper()} (${next_price}/mo)[/bold]",
        "",
        f"[dim]→ replimap upgrade {next_plan}[/dim]",
    ]

    output.print(
        Panel(
            "\n".join(lines),
            border_style="yellow",
            padding=(1, 2),
        )
    )
