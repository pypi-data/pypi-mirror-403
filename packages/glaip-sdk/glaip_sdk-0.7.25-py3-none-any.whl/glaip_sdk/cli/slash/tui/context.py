"""Shared context for all TUI components.

This module provides the TUIContext dataclass, which serves as the Python equivalent
of OpenCode's nested provider pattern. It provides a single container for all TUI
services and state that can be injected into components.

Authors:
    Raymond Christopher (raymond.christopher@gdplabs.id)
"""

from __future__ import annotations

import os
from dataclasses import dataclass

from glaip_sdk.cli.account_store import get_account_store
from glaip_sdk.cli.slash.tui.clipboard import ClipboardAdapter
from glaip_sdk.cli.slash.tui.keybind_registry import KeybindRegistry
from glaip_sdk.cli.slash.tui.terminal import TerminalCapabilities
from glaip_sdk.cli.slash.tui.theme import ThemeManager
from glaip_sdk.cli.slash.tui.toast import ToastBus
from glaip_sdk.cli.tui_settings import load_tui_settings


@dataclass
class TUIContext:
    """Shared context for all TUI components (Python equivalent of OpenCode's providers).

    This context provides access to all TUI services and state. Components that will
    be implemented in later phases are typed as Optional and will be None initially.

    Attributes:
        terminal: Terminal capability detection results.
        keybinds: Central keybind registry (Phase 3).
        theme: Theme manager for light/dark mode and color tokens (Phase 2).
        toasts: Toast notification bus (Phase 4).
        clipboard: Clipboard adapter with OSC 52 support (Phase 4).
    """

    terminal: TerminalCapabilities
    keybinds: KeybindRegistry | None = None
    theme: ThemeManager | None = None
    toasts: ToastBus | None = None
    clipboard: ClipboardAdapter | None = None

    @classmethod
    async def create(cls, *, detect_osc11: bool = True) -> TUIContext:
        """Create a TUIContext instance with detected terminal capabilities.

        This factory method detects terminal capabilities asynchronously and
        returns a populated TUIContext instance with all services initialized
        (keybinds, theme, toasts, clipboard).

        Args:
            detect_osc11: When False, skip OSC 11 background detection.

        Returns:
            TUIContext instance with all services initialized.
        """
        terminal = await TerminalCapabilities.detect(detect_osc11=detect_osc11)
        store = get_account_store()
        settings = load_tui_settings(store=store)

        env_theme = os.getenv("AIP_TUI_THEME")
        env_theme = env_theme.strip() if env_theme else None
        if env_theme and env_theme.lower() == "default":
            env_theme = None

        env_mouse = os.getenv("AIP_TUI_MOUSE_CAPTURE")
        mouse_capture = settings.mouse_capture
        if env_mouse is not None:
            mouse_capture = env_mouse.lower() == "true"

        terminal.mouse = mouse_capture

        theme_name = env_theme or settings.theme_name
        theme = ThemeManager(
            terminal,
            mode=settings.theme_mode,
            theme=theme_name,
            settings_store=store,
        )
        keybinds = KeybindRegistry()
        toasts = ToastBus()
        clipboard = ClipboardAdapter(terminal=terminal)
        return cls(
            terminal=terminal,
            keybinds=keybinds,
            theme=theme,
            toasts=toasts,
            clipboard=clipboard,
        )
