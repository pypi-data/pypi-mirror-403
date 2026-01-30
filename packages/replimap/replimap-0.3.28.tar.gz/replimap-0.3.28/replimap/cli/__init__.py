"""
RepliMap CLI Module.

This module provides the command-line interface for RepliMap.
It exports the Typer app instance and shared utilities.

V3 Architecture Integration:
- GlobalContext is created via app callback and stored in ctx.obj
- Commands can access context via get_context(ctx)
- OutputManager ensures stdout hygiene (JSON mode writes only once)
- All progress/log output goes to stderr via console
"""

from __future__ import annotations

import logging

import typer

from replimap import __version__
from replimap.cli.commands import register_all_commands
from replimap.cli.context import GlobalContext
from replimap.cli.output import OutputFormat
from replimap.cli.utils import (
    console,
    get_available_profiles,
    get_aws_session,
    get_profile_region,
    logger,
)


def version_callback(value: bool) -> None:
    """Print version and exit."""
    if value:
        console.print(f"[bold cyan]RepliMap[/] v{__version__}")
        raise typer.Exit()


def create_app() -> typer.Typer:
    """
    Create and configure the CLI application.

    Returns:
        Configured Typer application with all commands registered.
    """
    app = typer.Typer(
        name="replimap",
        help=(
            "[bold cyan]AWS Infrastructure Intelligence Engine[/bold cyan]\n\n"
            "Scan, analyze, and transform your AWS infrastructure.\n\n"
            "[dim]Quick start:[/dim]\n"
            "  replimap scan -r us-east-1      [dim]# Scan and visualize[/dim]\n"
            "  replimap codify -r us-east-1    [dim]# Generate Terraform[/dim]\n"
            "  replimap audit -r us-east-1     [dim]# Security audit[/dim]"
        ),
        add_completion=True,  # Enable shell completion (install via --install-completion)
        rich_markup_mode="rich",
        context_settings={"help_option_names": ["-h", "--help"]},
    )

    @app.callback()
    def main(
        ctx: typer.Context,
        version: bool = typer.Option(
            False,
            "--version",
            "-V",
            callback=version_callback,
            is_eager=True,
            help="Show version and exit",
        ),
        profile: str | None = typer.Option(
            None,
            "--profile",
            "-p",
            envvar="AWS_PROFILE",
            help="AWS profile name",
        ),
        region: str | None = typer.Option(
            None,
            "--region",
            "-r",
            envvar="AWS_DEFAULT_REGION",
            help="AWS region",
        ),
        output_format: str = typer.Option(
            "text",
            "--format",
            "-f",
            help="Output format: text, json, table, quiet",
        ),
        verbose: int = typer.Option(
            0,
            "--verbose",
            "-v",
            count=True,
            help="Increase verbosity (-v, -vv for debug)",
        ),
        quiet: bool = typer.Option(
            False,
            "--quiet",
            "-q",
            help="Suppress output (errors only)",
        ),
    ) -> None:
        """AWS Infrastructure Intelligence Engine."""
        # Handle quiet as format override
        effective_format = "quiet" if quiet else output_format

        # Validate format
        try:
            OutputFormat(effective_format)
        except ValueError:
            raise typer.BadParameter(
                f"Invalid format '{effective_format}'. "
                f"Choose from: text, json, table, quiet"
            ) from None

        # Create and assign global context (V3 architecture)
        ctx.obj = GlobalContext.from_cli(
            profile=profile,
            region=region,
            output_format=effective_format,
            verbose=verbose,
        )

        # Also configure legacy logging based on verbosity
        if quiet:
            # 🚨 v3.7.18 FIX: Suppress ALL logs including WARNING when -q is used
            # User expects quiet mode to show only errors, not warnings
            logging.getLogger("replimap").setLevel(logging.ERROR)
        elif verbose >= 2:
            logging.getLogger().setLevel(logging.DEBUG)
        elif verbose >= 1:
            logging.getLogger().setLevel(logging.INFO)

    # Register all commands
    register_all_commands(app)

    return app


# Create the app instance
app = create_app()


def get_context(ctx: typer.Context) -> GlobalContext:
    """
    Get GlobalContext from Typer context.

    This is a convenience function for commands that need
    type-safe access to the context.

    Args:
        ctx: Typer context

    Returns:
        GlobalContext instance

    Raises:
        RuntimeError: If context is not properly initialized
    """
    if ctx.obj is None:
        raise RuntimeError(
            "GlobalContext not initialized. Ensure the app callback was called."
        )

    if not isinstance(ctx.obj, GlobalContext):
        raise RuntimeError(
            f"Expected GlobalContext, got {type(ctx.obj).__name__}. "
            "Ensure the app callback was called."
        )

    return ctx.obj


__all__ = [
    # App
    "app",
    "create_app",
    # V3 Context
    "get_context",
    "GlobalContext",
    # Utilities
    "console",
    "logger",
    "get_aws_session",
    "get_available_profiles",
    "get_profile_region",
]
