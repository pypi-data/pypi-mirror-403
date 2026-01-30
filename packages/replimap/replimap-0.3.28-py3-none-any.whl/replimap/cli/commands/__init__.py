"""
CLI Commands Module.

This module contains all CLI command implementations for RepliMap.
Commands are organized into separate files for maintainability.

Usage:
    from replimap.cli.commands import register_all_commands

    app = typer.Typer()
    register_all_commands(app)
"""

from __future__ import annotations

import typer

# Import individual command modules
from replimap.cli.commands import (
    analyze,
    audit,
    cache,
    clone,
    codify,
    completion,
    cost,
    deps,
    doctor,
    dr,
    drift,
    explain,
    graph,
    iam,
    license,
    load,
    profiles,
    remediate,
    scan,
    snapshot,
    transfer,
    trends,
    trust_center,
    unused,
    upgrade,
    validate,
)
from replimap.decisions.cli import create_decisions_app


def register_all_commands(app: typer.Typer) -> None:
    """
    Register all commands with the Typer app.

    This function imports and registers all command modules.
    Each module should have a `register(app)` function.

    Commands are organized into groups for better help output:
    - Core Commands: scan, graph, load, profiles
    - Infrastructure as Code: clone, codify, remediate
    - Analysis: analyze, deps, drift, validate
    - Cost Optimization: cost, unused, trends, transfer
    - Security & Compliance: audit, iam, trust-center
    - Disaster Recovery: snapshot, dr
    - Configuration: cache, scan-cache, doctor, license, upgrade, decisions, completion

    Args:
        app: The Typer application instance
    """
    # ========================================
    # Core Commands (most commonly used)
    # ========================================
    scan.register(app, panel="Core Commands")
    graph.register(app, panel="Core Commands")
    load.register(app, panel="Core Commands")
    profiles.register(app, panel="Core Commands")

    # ========================================
    # Infrastructure as Code
    # ========================================
    clone.register(app, panel="Infrastructure as Code")
    codify.register(app, panel="Infrastructure as Code")
    remediate.register(app, panel="Infrastructure as Code")

    # ========================================
    # Analysis
    # ========================================
    analyze.register(app, panel="Analysis")
    deps.register(app, panel="Analysis")
    drift.register(app, panel="Analysis")
    validate.register(app, panel="Analysis")

    # ========================================
    # Cost Optimization
    # ========================================
    cost.register(app, panel="Cost Optimization")
    unused.register(app, panel="Cost Optimization")
    trends.register(app, panel="Cost Optimization")
    transfer.register(app, panel="Cost Optimization")

    # ========================================
    # Security & Compliance
    # ========================================
    audit.register(app, panel="Security & Compliance")
    iam.register(app, panel="Security & Compliance")
    trust_center.register(app, panel="Security & Compliance")

    # ========================================
    # Disaster Recovery
    # ========================================
    snapshot.register(app, panel="Disaster Recovery")
    dr.register(app, panel="Disaster Recovery")

    # ========================================
    # Configuration & Utilities
    # ========================================
    cache.register(app, panel="Configuration")
    doctor.register(app, panel="Configuration")
    license.register(app, panel="Configuration")
    upgrade.register(app, panel="Configuration")
    completion.register(app, panel="Configuration")
    app.add_typer(create_decisions_app(), rich_help_panel="Configuration")

    # ========================================
    # Help & Debugging
    # ========================================
    explain.register(app, panel="Help & Debugging")


__all__ = [
    "register_all_commands",
    "scan",
    "clone",
    "codify",
    "analyze",
    "load",
    "profiles",
    "audit",
    "graph",
    "drift",
    "deps",
    "cost",
    "remediate",
    "validate",
    "unused",
    "trends",
    "transfer",
    "cache",
    "iam",
    "license",
    "upgrade",
    "snapshot",
    "trust_center",
    "dr",
    "completion",
    "doctor",
    "explain",
]
