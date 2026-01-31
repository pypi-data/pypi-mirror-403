"""Layout components for TUI applications.

This package provides reusable layout components following the Harlequin pattern
for multi-pane data-rich screens.
"""

from __future__ import annotations

try:  # pragma: no cover - optional dependency
    from glaip_sdk.cli.slash.tui.layouts.harlequin import HarlequinScreen
except Exception:  # pragma: no cover - optional dependency
    HarlequinScreen = None  # type: ignore[assignment, misc]

__all__ = ["HarlequinScreen"]
