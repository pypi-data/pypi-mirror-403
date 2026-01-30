"""
RepliMap UI Module.

Rich console output utilities for CLI.
"""

from replimap.ui.console import (
    console,
    print_dim,
    print_error,
    print_info,
    print_success,
    print_warning,
)
from replimap.ui.rich_output import (
    print_audit_findings_fomo,
    print_audit_summary_fomo,
    print_finding_title,
    print_remediation_preview,
    print_upgrade_cta,
)
from replimap.ui.snapshot_panels import (
    show_locked_snapshots_fomo,
    show_snapshot_locked_error,
    show_upgrade_panel,
)
from replimap.ui.snapshot_tables import (
    create_snapshot_table,
    show_snapshot_list,
    show_summary_table,
)

__all__ = [
    # rich_output (audit FOMO)
    "print_audit_findings_fomo",
    "print_audit_summary_fomo",
    "print_finding_title",
    "print_remediation_preview",
    "print_upgrade_cta",
    # console utilities
    "console",
    "print_success",
    "print_error",
    "print_warning",
    "print_info",
    "print_dim",
    # snapshot panels (Phase 2 FOMO)
    "show_locked_snapshots_fomo",
    "show_snapshot_locked_error",
    "show_upgrade_panel",
    # snapshot tables (Phase 2 pagination)
    "show_snapshot_list",
    "create_snapshot_table",
    "show_summary_table",
]
