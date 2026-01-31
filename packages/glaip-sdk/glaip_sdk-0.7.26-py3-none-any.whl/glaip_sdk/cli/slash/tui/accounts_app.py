"""Textual UI for the /accounts command.

Provides a minimal interactive list with the same columns/order as the Rich
fallback (name, API URL, masked key, status) and keyboard navigation.

Integrates with TUI foundation services:
- KeybindRegistry: Centralized keybind registration with scoped actions
- ClipboardAdapter: Cross-platform clipboard operations with OSC 52 support
- ToastBus: Non-blocking toast notifications for user feedback

Authors:
    Raymond Christopher (raymond.christopher@gdplabs.id)
"""

from __future__ import annotations

import asyncio
import logging
from collections.abc import Callable
from dataclasses import dataclass
from typing import Any, cast

from glaip_sdk.cli.account_store import AccountStore, AccountStoreError, get_account_store
from glaip_sdk.cli.commands.common_config import check_connection_with_reason
from glaip_sdk.cli.slash.accounts_shared import (
    build_account_rows,
    build_account_status_string,
    env_credentials_present,
)
from glaip_sdk.cli.slash.tui.background_tasks import BackgroundTaskMixin
from glaip_sdk.cli.slash.tui.clipboard import ClipboardAdapter, ClipboardResult
from glaip_sdk.cli.slash.tui.context import TUIContext
from glaip_sdk.cli.slash.tui.indicators import PulseIndicator
from glaip_sdk.cli.slash.tui.keybind_registry import KeybindRegistry
from glaip_sdk.cli.slash.tui.layouts.harlequin import HarlequinScreen
from glaip_sdk.cli.slash.tui.loading import hide_loading_indicator, show_loading_indicator
from glaip_sdk.cli.slash.tui.terminal import TerminalCapabilities
from glaip_sdk.cli.slash.tui.theme.catalog import _BUILTIN_THEMES

from glaip_sdk.cli.slash.tui.toast import (
    ClipboardToastMixin,
    Toast,
    ToastBus,
    ToastContainer,
    ToastHandlerMixin,
    ToastVariant,
)
from glaip_sdk.cli.validators import validate_api_key
from glaip_sdk.utils.validation import validate_url

from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal, Vertical
from textual.coordinate import Coordinate
from textual.screen import ModalScreen
from textual.suggester import SuggestFromList
from textual.theme import Theme
from textual.widgets import Button, Checkbox, DataTable, Footer, Input, Static

# Harlequin layout requires specific widget support
TEXTUAL_SUPPORTED = True

# Use standard Textual base classes
_AccountFormBase = ModalScreen[dict[str, Any] | None]
_ConfirmDeleteBase = ModalScreen[str | None]
_AppBase = App[None]

# Widget IDs for Textual UI
ACCOUNTS_TABLE_ID = "#accounts-table"
FILTER_INPUT_ID = "#filter-input"
STATUS_ID = "#status"
ACCOUNTS_LOADING_ID = "#accounts-loading"
FORM_KEY_ID = "#form-key"

# CSS file name
CSS_FILE_NAME = "accounts.tcss"

KEYBIND_SCOPE = "accounts"
KEYBIND_CATEGORY = "Accounts"


@dataclass
class KeybindDef:
    """Keybind definition with action, key, and description."""

    action: str
    key: str
    description: str


KEYBIND_DEFINITIONS: tuple[KeybindDef, ...] = (
    KeybindDef("switch_row", "enter", "Switch"),
    KeybindDef("focus_filter", "/", "Filter"),
    KeybindDef("add_account", "a", "Add"),
    KeybindDef("edit_account", "e", "Edit"),
    KeybindDef("delete_account", "d", "Delete"),
    KeybindDef("copy_account", "c", "Copy"),
    KeybindDef("clear_or_exit", "escape", "Close"),
    KeybindDef("app_exit", "q", "Close"),
)


@dataclass
class AccountsTUICallbacks:
    """Callbacks invoked by the Textual UI."""

    switch_account: Callable[[str], tuple[bool, str]]


def _build_account_rows_from_store(
    store: AccountStore,
    env_lock: bool,
) -> tuple[list[dict[str, str | bool]], str | None]:
    """Load account rows with masking and active flag."""
    accounts = store.list_accounts()
    active = store.get_active_account()
    rows = build_account_rows(accounts, active, env_lock)
    return rows, active


def _prepare_account_payload(
    *,
    name: str,
    api_url_input: str,
    api_key_input: str,
    existing_url: str | None,
    existing_key: str | None,
    existing_names: set[str],
    mode: str,
    should_test: bool,
    validate_name: Callable[[str], None],
    connection_tester: Callable[[str, str], tuple[bool, str]],
) -> tuple[dict[str, Any] | None, str | None]:
    """Validate and build payload for add/edit operations."""
    name = name.strip()
    api_url_raw = api_url_input.strip()
    api_key_raw = api_key_input.strip()

    error = _validate_account_name(name, existing_names, mode, validate_name)
    if error:
        return None, error

    api_url_candidate = api_url_raw or (existing_url or "")
    api_key_candidate = api_key_raw or (existing_key or "")

    api_url_validated, error = _validate_and_prepare_url(api_url_candidate)
    if error:
        return None, error

    api_key_validated, error = _validate_and_prepare_key(api_key_candidate)
    if error:
        return None, error

    if should_test:
        error = _test_connection(api_url_validated, api_key_validated, connection_tester)
        if error:
            return None, error

    payload: dict[str, Any] = {
        "name": name,
        "api_url": api_url_validated,
        "api_key": api_key_validated,
        "should_test": should_test,
        "mode": mode,
    }
    return payload, None


def _validate_account_name(
    name: str,
    existing_names: set[str],
    mode: str,
    validate_name: Callable[[str], None],
) -> str | None:
    """Validate account name."""
    if not name:
        return "Account name cannot be empty."

    try:
        validate_name(name)
    except Exception as exc:
        return str(exc)

    if mode == "add" and name in existing_names:
        return f"Account '{name}' already exists. Choose a unique name."

    return None


def _validate_and_prepare_url(api_url_candidate: str) -> tuple[str, str | None]:
    """Validate and prepare API URL."""
    if not api_url_candidate:
        return "", "API URL is required."
    try:
        return validate_url(api_url_candidate), None
    except Exception as exc:
        return "", str(exc)


def _validate_and_prepare_key(api_key_candidate: str) -> tuple[str, str | None]:
    """Validate and prepare API key."""
    if not api_key_candidate:
        return "", "API key is required."
    try:
        return validate_api_key(api_key_candidate), None
    except Exception as exc:
        return "", str(exc)


def _test_connection(
    api_url: str,
    api_key: str,
    connection_tester: Callable[[str, str], tuple[bool, str]],
) -> str | None:
    """Test API connection."""
    ok, reason = connection_tester(api_url, api_key)
    if not ok:
        detail = reason or "connection_failed"
        return f"Connection test failed: {detail}"
    return None


def run_accounts_textual(
    rows: list[dict[str, str | bool]],
    *,
    active_account: str | None,
    env_lock: bool,
    callbacks: AccountsTUICallbacks,
    ctx: TUIContext | None = None,
) -> None:
    """Launch the Textual accounts browser if dependencies are available."""
    if not TEXTUAL_SUPPORTED:
        return
    app = AccountsTextualApp(rows, active_account, env_lock, callbacks, ctx=ctx)
    app.run()


class AccountFormModal(_AccountFormBase):  # pragma: no cover - interactive
    """Modal form for add/edit account."""

    CSS_PATH = CSS_FILE_NAME

    def __init__(
        self,
        *,
        mode: str,
        existing: dict[str, str] | None,
        existing_names: set[str],
        connection_tester: Callable[[str, str], tuple[bool, str]],
        validate_name: Callable[[str], None],
    ) -> None:
        """Initialize the account form modal.

        Args:
            mode: Form mode, either "add" or "edit".
            existing: Existing account data for edit mode.
            existing_names: Set of existing account names for validation.
            connection_tester: Callable to test API connection.
            validate_name: Callable to validate account name.
        """
        super().__init__()
        self._mode = mode
        self._existing = existing or {}
        self._existing_names = existing_names
        self._connection_tester = connection_tester
        self._validate_name = validate_name

    def _get_api_url_suggestions(self, _value: str) -> list[str]:
        """Get API URL suggestions from existing accounts.

        Args:
            _value: Current input value (unused, but required by Textual's suggestor API).

        Returns:
            List of unique API URLs from existing accounts.
        """
        try:
            store = get_account_store()
            accounts = store.list_accounts()
            # Extract unique API URLs, excluding the current account's URL in edit mode
            existing_url = self._existing.get("api_url", "")
            urls = {account.get("api_url", "") for account in accounts.values() if account.get("api_url")}
            if existing_url in urls:
                urls.remove(existing_url)
            return sorted(urls)
        except Exception:  # pragma: no cover - defensive
            return []

    def compose(self) -> ComposeResult:
        """Render the form controls."""
        title = "Add account" if self._mode == "add" else "Edit account"
        name_input = Input(
            value=self._existing.get("name", ""),
            placeholder="account-name",
            id="form-name",
            disabled=self._mode == "edit",
        )
        # Get API URL suggestions and create suggester
        url_suggestions = self._get_api_url_suggestions("")
        url_suggester = None
        if SuggestFromList and url_suggestions:
            url_suggester = SuggestFromList(url_suggestions, case_sensitive=False)
        url_input = Input(
            value=self._existing.get("api_url", ""),
            placeholder="https://api.example.com",
            id="form-url",
            suggester=url_suggester,
        )
        key_input = Input(value="", placeholder="sk-...", password=True, id="form-key")
        test_checkbox = Checkbox(
            "Test connection before save",
            value=True,
            id="form-test",
        )
        status = Static("", id="form-status")

        yield Static(title, id="form-title")
        yield Static("Name", classes="form-label")
        yield name_input
        yield Static("API URL", classes="form-label")
        yield url_input
        yield Static("API Key", classes="form-label")
        yield key_input
        yield Horizontal(
            Button("Show key", id="toggle-key"),
            Button("Clear key", id="clear-key"),
            id="form-key-actions",
        )
        yield test_checkbox
        yield Horizontal(
            Button("Save", id="form-save", variant="primary"),
            Button("Cancel", id="form-cancel"),
            id="form-actions",
        )
        yield status

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button presses."""
        btn_id = event.button.id or ""
        if btn_id == "form-cancel":
            self.dismiss(None)
            return
        if btn_id == "toggle-key":
            key_input = self.query_one(FORM_KEY_ID, Input)
            key_input.password = not key_input.password
            key_input.focus()
            return
        if btn_id == "clear-key":
            key_input = self.query_one(FORM_KEY_ID, Input)
            key_input.value = ""
            key_input.focus()
            return
        if btn_id == "form-save":
            self._handle_submit()

    def on_input_submitted(self, _event: Input.Submitted) -> None:
        """Handle Enter key to save."""
        self._handle_submit()

    def _handle_submit(self) -> None:
        """Validate inputs and dismiss with payload on success."""
        status = self.query_one("#form-status", Static)
        name_input = self.query_one("#form-name", Input)
        url_input = self.query_one("#form-url", Input)
        key_input = self.query_one(FORM_KEY_ID, Input)
        test_checkbox = self.query_one("#form-test", Checkbox)

        payload, error = _prepare_account_payload(
            name=name_input.value or "",
            api_url_input=url_input.value or "",
            api_key_input=key_input.value or "",
            existing_url=self._existing.get("api_url"),
            existing_key=self._existing.get("api_key"),
            existing_names=self._existing_names,
            mode=self._mode,
            should_test=bool(test_checkbox.value),
            validate_name=self._validate_name,
            connection_tester=self._connection_tester,
        )
        if error:
            status.update(f"[red]{error}[/]")
            if error.startswith("Connection test failed") and hasattr(self.app, "_set_status"):
                try:
                    # Surface a status-bar cue so errors remain visible after closing the modal.
                    self.app._set_status(error, "yellow")  # type: ignore[attr-defined]
                except Exception:
                    pass
            return
        status.update("[green]Saving...[/]")
        self.dismiss(payload)


class ConfirmDeleteModal(_ConfirmDeleteBase):  # pragma: no cover - interactive
    """Modal requiring typed confirmation for delete."""

    CSS_PATH = CSS_FILE_NAME

    def __init__(self, name: str) -> None:
        """Initialize the delete confirmation modal.

        Args:
            name: Name of the account to delete.
        """
        super().__init__()
        self._name = name

    def compose(self) -> ComposeResult:
        """Render confirmation form."""
        yield Static(f"Type '{self._name}' to confirm deletion. This cannot be undone.", id="confirm-text")
        yield Input(placeholder=self._name, id="confirm-input")
        yield Horizontal(
            Button("Delete", id="confirm-delete", variant="error"),
            Button("Cancel", id="confirm-cancel"),
            id="confirm-actions",
        )
        yield Static("", id="confirm-status")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle confirmation buttons."""
        btn_id = event.button.id or ""
        if btn_id == "confirm-cancel":
            self.dismiss(None)
            return
        if btn_id == "confirm-delete":
            self._handle_confirm()

    def on_input_submitted(self, _event: Input.Submitted) -> None:
        """Handle Enter key in confirmation input."""
        self._handle_confirm()

    def _handle_confirm(self) -> None:
        """Dismiss with name when confirmation matches."""
        status = self.query_one("#confirm-status", Static)
        input_widget = self.query_one("#confirm-input", Input)
        if (input_widget.value or "").strip() != self._name:
            status.update(f"[yellow]Name does not match; type '{self._name}' to confirm.[/]")
            input_widget.focus()
            return
        self.dismiss(self._name)


# Widget IDs for Harlequin layout
HARLEQUIN_ACCOUNTS_LIST_ID = "#harlequin-accounts-list"
HARLEQUIN_DETAIL_ID = "#harlequin-detail"
HARLEQUIN_DETAIL_URL_ID = "#harlequin-detail-url"
HARLEQUIN_DETAIL_KEY_ID = "#harlequin-detail-key"
HARLEQUIN_DETAIL_STATUS_ID = "#harlequin-detail-status"
HARLEQUIN_DETAIL_ACTIONS_ID = "#harlequin-detail-actions"


class AccountsHarlequinScreen(  # pragma: no cover - interactive
    ToastHandlerMixin, ClipboardToastMixin, BackgroundTaskMixin, HarlequinScreen
):
    """Harlequin layout screen for account management.

    Implements Phase 1 of the TUI Harlequin Layout spec:
    - Left pane (25%): Account Profile names list
    - Right pane (75%): URL, API Key (hidden by default), Connection Status, Action Palette
    """

    CSS_PATH = CSS_FILE_NAME

    BINDINGS = [
        Binding("enter", "switch_account", "Switch", show=True) if Binding else None,
        Binding("return", "switch_account", "Switch", show=False) if Binding else None,
        Binding("/", "focus_filter", "Filter", show=True) if Binding else None,
        Binding("a", "add_account", "Add", show=True) if Binding else None,
        Binding("e", "edit_account", "Edit", show=True) if Binding else None,
        Binding("d", "delete_account", "Delete", show=True) if Binding else None,
        Binding("c", "copy_account", "Copy", show=True) if Binding else None,
        Binding("escape", "clear_or_exit", "Close", priority=True) if Binding else None,
        Binding("q", "app_exit", "Close", priority=True) if Binding else None,
    ]
    BINDINGS = [b for b in BINDINGS if b is not None]

    def __init__(
        self,
        rows: list[dict[str, str | bool]],
        active_account: str | None,
        env_lock: bool,
        callbacks: AccountsTUICallbacks,
        ctx: TUIContext | None = None,
    ) -> None:
        """Initialize the Harlequin accounts screen.

        Args:
            rows: Account data rows to display.
            active_account: Name of the currently active account.
            env_lock: Whether environment credentials are locking account switching.
            callbacks: Callbacks for account switching operations.
            ctx: Shared TUI context.
        """
        super().__init__(ctx=ctx)
        self._ctx = ctx
        self._store = get_account_store()
        self._all_rows = rows
        self._active_account = active_account
        self._env_lock = env_lock
        self._account_callbacks = callbacks
        self._keybinds: KeybindRegistry | None = None
        self._toast_bus: ToastBus | None = None
        self._clip_cache: ClipboardAdapter | None = None
        self._filter_text: str = ""
        self._is_switching = False
        self._selected_account: dict[str, str | bool] | None = None
        self._key_visible = False
        self._initialize_context_services()

    def compose(self) -> ComposeResult:  # type: ignore[return]
        """Compose the Harlequin layout with account list and detail panes."""
        if not TEXTUAL_SUPPORTED or Horizontal is None or Vertical is None or Static is None:
            return  # type: ignore[return-value]

        # Main container with horizontal split (25/75)
        with Horizontal(id="harlequin-container"):
            # Left pane (25% width) with account list
            with Vertical(id="left-pane"):
                yield Static("Accounts", id="left-pane-title")
                yield Input(placeholder="Filter...", id="harlequin-filter")
                yield DataTable(id=HARLEQUIN_ACCOUNTS_LIST_ID.lstrip("#"))
            # Right pane (75% width) with account details
            with Vertical(id="right-pane"):
                yield Static("Account Details", id="right-pane-title")
                yield Static("", id=HARLEQUIN_DETAIL_ID.lstrip("#"))
                with Vertical(id="detail-fields"):
                    yield Static("URL:", classes="detail-label")
                    yield Static("", id=HARLEQUIN_DETAIL_URL_ID.lstrip("#"))
                    yield Static("API Key:", classes="detail-label")
                    yield Static("", id=HARLEQUIN_DETAIL_KEY_ID.lstrip("#"))
                    yield Static("Status:", classes="detail-label")
                    yield Static("", id=HARLEQUIN_DETAIL_STATUS_ID.lstrip("#"))
                with Horizontal(id=HARLEQUIN_DETAIL_ACTIONS_ID.lstrip("#")):
                    yield Button("(a) Add", id="action-add")
                    yield Button("(e) Edit", id="action-edit")
                    yield Button("(d) Delete", id="action-delete")
                    yield Button("(c) Copy", id="action-copy")
                yield PulseIndicator(id="harlequin-loading")
                yield Static("", id="harlequin-status")
                # Help text showing keyboard shortcuts at the bottom
                yield Static(
                    "[dim]↑↓ Navigate | Enter Switch | a Add | e Edit | d Delete | c Copy | q/Esc Exit[/dim]",
                    id="help-text",
                )

        # Toast container for notifications
        if Toast is not None and ToastContainer is not None:
            yield ToastContainer(Toast(), id="toast-container")

    def on_mount(self) -> None:
        """Configure the screen after mount."""
        if not TEXTUAL_SUPPORTED:
            return

        self._apply_theme()
        table = self.query_one(HARLEQUIN_ACCOUNTS_LIST_ID, DataTable)
        table.add_column("Account", width=None)
        table.cursor_type = "row"
        table.zebra_stripes = True
        self._reload_accounts_list()
        table.focus()
        self._prepare_toasts()
        self._register_keybinds()
        self._update_detail_pane()
        self._hide_loading()

    def _initialize_context_services(self) -> None:
        """Initialize TUI context services."""

        def _notify(message: ToastBus.Changed) -> None:
            self.post_message(message)

        ctx = self.ctx if hasattr(self, "ctx") else self._ctx
        if ctx:
            if ctx.keybinds is None:
                ctx.keybinds = KeybindRegistry()
            if ctx.toasts is None and ToastBus is not None:
                ctx.toasts = ToastBus(on_change=_notify)
            if ctx.clipboard is None:
                ctx.clipboard = ClipboardAdapter(terminal=ctx.terminal)
            self._keybinds = ctx.keybinds
            self._toast_bus = ctx.toasts
            self._clip_cache = ctx.clipboard
        else:
            terminal = TerminalCapabilities(
                tty=True, ansi=True, osc52=False, osc11_bg=None, mouse=False, truecolor=False
            )
            self._clip_cache = ClipboardAdapter(terminal=terminal)
            if ToastBus is not None:
                self._toast_bus = ToastBus(on_change=_notify)

    def _prepare_toasts(self) -> None:
        """Prepare toast system."""
        if self._toast_bus:
            self._toast_bus.clear()

    def _register_keybinds(self) -> None:
        """Register keybinds with the registry."""
        if not self._keybinds:
            return
        for keybind_def in KEYBIND_DEFINITIONS:
            scoped_action = f"{KEYBIND_SCOPE}.{keybind_def.action}"
            if self._keybinds.get(scoped_action):
                continue
            try:
                self._keybinds.register(
                    action=scoped_action,
                    key=keybind_def.key,
                    description=keybind_def.description,
                    category=KEYBIND_CATEGORY,
                )
            except ValueError as e:
                logging.debug(f"Skipping duplicate keybind registration: {scoped_action}", exc_info=e)
                continue

    def _reload_accounts_list(self, preferred_name: str | None = None) -> None:
        """Reload the accounts list in the left pane."""
        if not TEXTUAL_SUPPORTED:
            return

        table = self.query_one(HARLEQUIN_ACCOUNTS_LIST_ID, DataTable)
        table.clear()

        filtered = self._filtered_rows()
        for row in filtered:
            name = str(row.get("name", ""))
            # Highlight active account
            if row.get("name") == self._active_account:
                name = f"[green]●[/] {name}"
            table.add_row(name)

        # Move cursor to active or preferred account
        cursor_idx = 0
        target_name = preferred_name or self._active_account
        for idx, row in enumerate(filtered):
            if row.get("name") == target_name:
                cursor_idx = idx
                break

        if filtered:
            table.cursor_coordinate = (cursor_idx, 0)
            self._update_selected_account(filtered[cursor_idx] if cursor_idx < len(filtered) else None)
        else:
            self._update_selected_account(None)
            self._set_status("No accounts match the current filter.", "yellow")

    def _filtered_rows(self) -> list[dict[str, str | bool]]:
        """Return filtered account rows."""
        if not self._filter_text:
            return list(self._all_rows)

        needle = self._filter_text.lower()
        filtered = [
            row
            for row in self._all_rows
            if needle in str(row.get("name", "")).lower() or needle in str(row.get("api_url", "")).lower()
        ]

        def score(row: dict[str, str | bool]) -> tuple[int, str]:
            name = str(row.get("name", "")).lower()
            url = str(row.get("api_url", "")).lower()
            name_hit = needle in name
            url_hit = needle in url
            priority = 0 if name_hit else (1 if url_hit else 2)
            return (priority, name)

        return sorted(filtered, key=score)

    def _update_selected_account(self, account: dict[str, str | bool] | None) -> None:
        """Update the selected account and refresh detail pane."""
        self._selected_account = account
        self._update_detail_pane()

    def _update_detail_pane(self) -> None:
        """Update the right pane with selected account details."""
        if not TEXTUAL_SUPPORTED:
            return

        if not self._selected_account:
            detail = self.query_one(HARLEQUIN_DETAIL_ID, Static)
            detail.update("[dim]Select an account to view details[/]")
            url_widget = self.query_one(HARLEQUIN_DETAIL_URL_ID, Static)
            url_widget.update("")
            key_widget = self.query_one(HARLEQUIN_DETAIL_KEY_ID, Static)
            key_widget.update("")
            status_widget = self.query_one(HARLEQUIN_DETAIL_STATUS_ID, Static)
            status_widget.update("")
            return

        account = self._selected_account
        name = str(account.get("name", ""))
        url = str(account.get("api_url", ""))
        masked_key = str(account.get("masked_key", ""))
        api_key = str(account.get("api_key", ""))

        # Update detail header
        detail = self.query_one(HARLEQUIN_DETAIL_ID, Static)
        detail.update(f"[bold]{name}[/]")

        # Update URL
        url_widget = self.query_one(HARLEQUIN_DETAIL_URL_ID, Static)
        url_widget.update(url)

        # Update API Key (hidden by default, toggle with button)
        key_widget = self.query_one(HARLEQUIN_DETAIL_KEY_ID, Static)
        if self._key_visible and api_key:
            key_widget.update(api_key)
        else:
            key_widget.update(masked_key)

        # Update Status
        row_for_status = dict(account)
        row_for_status["active"] = row_for_status.get("name") == self._active_account
        status_str = build_account_status_string(row_for_status, use_markup=True)
        status_widget = self.query_one(HARLEQUIN_DETAIL_STATUS_ID, Static)
        status_widget.update(status_str)

    def _set_status(self, message: str, style: str) -> None:
        """Update status message."""
        if not TEXTUAL_SUPPORTED:
            return
        status = self.query_one("#harlequin-status", Static)
        status.update(f"[{style}]{message}[/]")

    def _get_selected_name(self) -> str | None:
        """Get the name of the currently selected account."""
        if not TEXTUAL_SUPPORTED or not self._selected_account:
            return None
        return str(self._selected_account.get("name", ""))

    def _show_loading(self, message: str | None = None) -> None:
        show_loading_indicator(self, "#harlequin-loading", message=message, set_status=self._set_status)

    def _hide_loading(self) -> None:
        hide_loading_indicator(self, "#harlequin-loading")

    def action_switch_account(self) -> None:
        """Switch to the currently selected account."""
        if self._env_lock:
            self._set_status("Switching disabled: env credentials in use.", "yellow")
            return

        # Ensure account is selected from cursor position if not explicitly selected
        if not self._selected_account:
            try:
                table = self.query_one(HARLEQUIN_ACCOUNTS_LIST_ID, DataTable)
                cursor_row = table.cursor_row
                if cursor_row is not None and cursor_row >= 0:
                    filtered = self._filtered_rows()
                    if cursor_row < len(filtered):
                        self._update_selected_account(filtered[cursor_row])
            except Exception:
                pass

        name = self._get_selected_name()
        if not name:
            self._set_status("No account selected.", "yellow")
            return

        if self._is_switching:
            self._set_status("Already switching...", "yellow")
            return

        self._is_switching = True
        host = self._get_host_for_name(name)
        message = f"Connecting to '{name}' ({host})..." if host else f"Connecting to '{name}'..."
        self._set_status(message, "cyan")
        self._queue_switch(name)

    def _get_host_for_name(self, name: str | None) -> str | None:
        """Return shortened API URL for a given account name."""
        if not name:
            return None
        for row in self._all_rows:
            if row.get("name") == name:
                url = str(row.get("api_url", ""))
                return url if len(url) <= 40 else f"{url[:37]}..."
        return None

    def _queue_switch(self, name: str) -> None:
        """Run switch in background."""

        async def perform() -> None:
            try:
                switched, message = await asyncio.to_thread(self._account_callbacks.switch_account, name)
            except Exception as exc:
                self._set_status(f"Switch failed: {exc}", "red")
                return
            finally:
                self._hide_loading()
                self._is_switching = False

            if switched:
                # Refresh active account from store to ensure consistency
                self._active_account = self._store.get_active_account() or name
                status_msg = message or f"Switched to '{name}'."
                if self._toast_bus:
                    self._toast_bus.show(message=status_msg, variant="success")
                self._set_status(status_msg, "green")
                # Reload accounts list to update green indicator
                self._reload_accounts_list(preferred_name=name)
                self._update_detail_pane()
            else:
                self._set_status(message or "Switch failed; kept previous account.", "yellow")

        try:
            self._show_loading(f"Connecting to '{name}'...")
            self.track_task(perform(), logger=logging.getLogger(__name__))
        except Exception as exc:
            self._hide_loading()
            self._is_switching = False
            self._set_status(f"Switch failed to start: {exc}", "red")

    def on_data_table_row_selected(self, event: DataTable.RowSelected) -> None:  # type: ignore[override]
        """Handle row selection in the accounts list."""
        if not TEXTUAL_SUPPORTED:
            return
        table = self.query_one(HARLEQUIN_ACCOUNTS_LIST_ID, DataTable)
        try:
            table.cursor_coordinate = (event.cursor_row, 0)
        except Exception:
            return
        filtered = self._filtered_rows()
        if event.cursor_row < len(filtered):
            self._update_selected_account(filtered[event.cursor_row])
        if not self._is_switching:
            self.action_switch_account()

    def on_data_table_cell_selected(self, event: DataTable.CellSelected) -> None:  # type: ignore[override]
        """Handle mouse click selection by triggering switch."""
        if not TEXTUAL_SUPPORTED:
            return
        table = self.query_one(HARLEQUIN_ACCOUNTS_LIST_ID, DataTable)
        try:
            table.cursor_coordinate = (event.coordinate.row, 0)
        except Exception:
            return
        filtered = self._filtered_rows()
        if event.coordinate.row < len(filtered):
            self._update_selected_account(filtered[event.coordinate.row])
        if not self._is_switching:
            self.action_switch_account()

    def on_data_table_cursor_row_changed(self, event: DataTable.CursorRowChanged) -> None:  # type: ignore[override]
        """Handle cursor movement in the accounts list."""
        if not TEXTUAL_SUPPORTED:
            return
        filtered = self._filtered_rows()
        if event.cursor_row is not None and event.cursor_row < len(filtered):
            self._update_selected_account(filtered[event.cursor_row])

    def action_focus_filter(self) -> None:
        """Focus the filter input."""
        if not TEXTUAL_SUPPORTED:
            return
        filter_input = self.query_one("#harlequin-filter", Input)
        filter_input.value = self._filter_text
        filter_input.focus()

    def on_input_changed(self, event: Input.Changed) -> None:
        """Handle filter input changes."""
        if not TEXTUAL_SUPPORTED:
            return
        if event.input.id == "harlequin-filter":
            self._filter_text = (event.value or "").strip()
            self._reload_accounts_list()

    def on_input_submitted(self, event: Input.Submitted) -> None:
        """Handle Enter key in Harlequin filter input."""
        if event.input.id == "harlequin-filter":
            try:
                table = self.query_one(HARLEQUIN_ACCOUNTS_LIST_ID, DataTable)
                table.focus()
            except Exception:
                pass

    def action_add_account(self) -> None:
        """Open add account modal."""
        if self._check_env_lock():
            return
        existing_names = {str(row.get("name", "")) for row in self._all_rows}
        modal = AccountFormModal(
            mode="add",
            existing=None,
            existing_names=existing_names,
            connection_tester=lambda url, key: check_connection_with_reason(url, key, abort_on_error=False),
            validate_name=self._store.validate_account_name,
        )
        self.app.push_screen(modal, self._on_form_result)

    def action_edit_account(self) -> None:
        """Open edit account modal."""
        if self._check_env_lock():
            return
        # Get account from cursor position if not explicitly selected
        self._ensure_account_selected_from_cursor()
        name = self._get_selected_name()
        if not name:
            self._set_status("Select an account to edit.", "yellow")
            return
        account = self._store.get_account(name)
        if not account:
            self._set_status(f"Account '{name}' not found.", "red")
            return
        existing_names = {str(row.get("name", "")) for row in self._all_rows if str(row.get("name", "")) != name}
        modal = AccountFormModal(
            mode="edit",
            existing={"name": name, "api_url": account.get("api_url", ""), "api_key": account.get("api_key", "")},
            existing_names=existing_names,
            connection_tester=lambda url, key: check_connection_with_reason(url, key, abort_on_error=False),
            validate_name=self._store.validate_account_name,
        )
        self.app.push_screen(modal, self._on_form_result)

    def action_delete_account(self) -> None:
        """Open delete confirmation modal."""
        if self._check_env_lock():
            return
        # Get account from cursor position if not explicitly selected
        self._ensure_account_selected_from_cursor()
        name = self._get_selected_name()
        if not name:
            self._set_status("Select an account to delete.", "yellow")
            return
        accounts = self._store.list_accounts()
        if len(accounts) <= 1:
            self._set_status("Cannot remove the last remaining account.", "red")
            return
        self.app.push_screen(ConfirmDeleteModal(name), self._on_delete_result)

    def _ensure_account_selected_from_cursor(self) -> None:
        """Ensure an account is selected, using cursor position if needed."""
        if self._selected_account:
            return
        try:
            table = self.query_one(HARLEQUIN_ACCOUNTS_LIST_ID, DataTable)
            cursor_row = table.cursor_row
            if cursor_row is not None and cursor_row >= 0:
                row = table.get_row_at(cursor_row)
                if row:
                    account_name = str(row[0])
                    # Find the account data
                    for account_data in self._all_rows:
                        if str(account_data.get("name", "")) == account_name:
                            self._selected_account = account_data
                            self._update_detail_pane()
                            break
        except Exception:
            pass

    def action_copy_account(self) -> None:
        """Copy selected account to clipboard."""
        # Get account from cursor position if not explicitly selected
        self._ensure_account_selected_from_cursor()

        name = self._get_selected_name()
        if not name:
            self._set_status("Select an account to copy.", "yellow")
            return

        account = self._store.get_account(name)
        if not account:
            return

        text = f"Account: {name}\nURL: {account.get('api_url', '')}"
        adapter = self._clip_adapter()
        writer = self._osc52_writer()
        if writer:
            result = adapter.copy(text, writer=writer)
        else:
            result = adapter.copy(text)
        self._handle_copy_result(name, result)

    def _handle_copy_result(self, name: str, result: ClipboardResult) -> None:
        """Handle copy operation result."""
        if result.success:
            if self._toast_bus:
                self._toast_bus.copy_success(f"Account '{name}'")
            self._set_status(f"Copied '{name}' to clipboard.", "green")
        else:
            if self._toast_bus and ToastVariant is not None:
                self._toast_bus.show(message=f"Copy failed: {result.message}", variant=ToastVariant.WARNING)
            self._set_status(f"Copy failed: {result.message}", "red")

    def _clip_adapter(self) -> ClipboardAdapter:
        """Get clipboard adapter."""
        ctx = self.ctx if hasattr(self, "ctx") else getattr(self, "_ctx", None)
        if ctx is not None and ctx.clipboard is not None:
            return cast(ClipboardAdapter, ctx.clipboard)
        if self._clip_cache is not None:
            return self._clip_cache
        adapter = ClipboardAdapter(terminal=ctx.terminal if ctx else None)
        if ctx is not None:
            ctx.clipboard = adapter
        else:
            self._clip_cache = adapter
        return adapter

    def _osc52_writer(self) -> Callable[[str], Any] | None:
        """Get OSC52 writer if available."""
        try:
            console = getattr(self, "console", None)
        except Exception:
            return None
        if console is None:
            return None
        output = getattr(console, "file", None)
        if output is None:
            return None

        def _write(sequence: str, _output: Any = output) -> None:
            _output.write(sequence)
            _output.flush()

        return _write

    def _check_env_lock(self) -> bool:
        """Check if env lock prevents mutations."""
        if not self._is_env_locked():
            return False
        self._env_lock = True
        self._set_status("Disabled by env-lock.", "yellow")
        self._refresh_rows()
        return True

    def _is_env_locked(self) -> bool:
        """Check if environment credentials are locking operations."""
        return env_credentials_present(partial=True)

    def _on_form_result(self, payload: dict[str, Any] | None) -> None:
        """Handle add/edit modal result."""
        if payload is None:
            self._set_status("Edit/add cancelled.", "yellow")
            return
        self._save_account(payload)

    def _on_delete_result(self, confirmed_name: str | None) -> None:
        """Handle delete confirmation result."""
        if not confirmed_name:
            self._set_status("Delete cancelled.", "yellow")
            return
        try:
            self._store.remove_account(confirmed_name)
        except AccountStoreError as exc:
            self._set_status(f"Delete failed: {exc}", "red")
            return
        except Exception as exc:
            self._set_status(f"Unexpected delete error: {exc}", "red")
            return

        self._set_status(f"Account '{confirmed_name}' deleted.", "green")
        self._refresh_rows()

    def _save_account(self, payload: dict[str, Any]) -> None:
        """Save account from modal payload."""
        if self._is_env_locked():
            self._set_status("Disabled by env-lock.", "yellow")
            return

        name = str(payload.get("name", ""))
        api_url = str(payload.get("api_url", ""))
        api_key = str(payload.get("api_key", ""))
        set_active = bool(payload.get("set_active", payload.get("mode") == "add"))
        is_edit = payload.get("mode") == "edit"

        try:
            self._store.add_account(name, api_url, api_key, overwrite=is_edit)
        except AccountStoreError as exc:
            self._set_status(f"Save failed: {exc}", "red")
            return
        except Exception as exc:
            self._set_status(f"Unexpected save error: {exc}", "red")
            return

        if set_active:
            try:
                self._store.set_active_account(name)
                self._active_account = name
            except Exception as exc:
                self._set_status(f"Saved but could not set active: {exc}", "yellow")
            else:
                if self._toast_bus:
                    self._toast_bus.show(message=f"Switched to '{name}'", variant="success")

        self._set_status(f"Account '{name}' saved.", "green")
        self._refresh_rows(preferred_name=name)

    def _refresh_rows(self, preferred_name: str | None = None) -> None:
        """Refresh account rows from store."""
        self._env_lock = self._is_env_locked()
        self._all_rows, self._active_account = _build_account_rows_from_store(self._store, self._env_lock)
        self._reload_accounts_list(preferred_name=preferred_name)
        if self._selected_account:
            # Refresh selected account details
            name = str(self._selected_account.get("name", ""))
            for row in self._all_rows:
                if row.get("name") == name:
                    self._update_selected_account(row)
                    break

    def action_clear_or_exit(self) -> None:
        """Clear filter or exit."""
        if not TEXTUAL_SUPPORTED:
            return
        filter_input = self.query_one("#harlequin-filter", Input)
        if filter_input.has_focus:
            if filter_input.value or self._filter_text:
                filter_input.value = ""
                self._filter_text = ""
                self._reload_accounts_list()
            table = self.query_one(HARLEQUIN_ACCOUNTS_LIST_ID, DataTable)
            table.focus()
            return
        self.dismiss()

    def action_app_exit(self) -> None:
        """Exit the application."""
        self.dismiss()

    def _apply_theme(self) -> None:
        """Apply theme from context."""
        ctx = self.ctx if hasattr(self, "ctx") else getattr(self, "_ctx", None)
        if not ctx or not ctx.theme or Theme is None:
            return

        app = self.app
        if app is None:
            return

        for name, tokens in _BUILTIN_THEMES.items():
            app.register_theme(
                Theme(
                    name=name,
                    primary=tokens.primary,
                    secondary=tokens.secondary,
                    accent=tokens.accent,
                    warning=tokens.warning,
                    error=tokens.error,
                    success=tokens.success,
                    background=tokens.background,
                    surface=tokens.background_panel,
                )
            )

        app.theme = ctx.theme.theme_name


class AccountsTextualApp(  # pragma: no cover - interactive
    ToastHandlerMixin, ClipboardToastMixin, BackgroundTaskMixin, _AppBase
):
    """Textual application for browsing accounts."""

    CSS_PATH = CSS_FILE_NAME
    BINDINGS = [
        Binding("enter", "switch_row", "Switch", show=True) if Binding else None,
        Binding("return", "switch_row", "Switch", show=False) if Binding else None,
        Binding("/", "focus_filter", "Filter", show=True) if Binding else None,
        Binding("a", "add_account", "Add", show=True) if Binding else None,
        Binding("e", "edit_account", "Edit", show=True) if Binding else None,
        Binding("d", "delete_account", "Delete", show=True) if Binding else None,
        Binding("c", "copy_account", "Copy", show=True) if Binding else None,
        # Esc clears filter when focused/non-empty; otherwise exits
        Binding("escape", "clear_or_exit", "Close", priority=True) if Binding else None,
        Binding("q", "app_exit", "Close", priority=True) if Binding else None,
    ]
    BINDINGS = [b for b in BINDINGS if b is not None]

    def __init__(
        self,
        rows: list[dict[str, str | bool]],
        active_account: str | None,
        env_lock: bool,
        callbacks: AccountsTUICallbacks,
        ctx: TUIContext | None = None,
    ) -> None:
        """Initialize the Textual accounts app.

        Args:
            rows: Account data rows to display.
            active_account: Name of the currently active account.
            env_lock: Whether environment credentials are locking account switching.
            callbacks: Callbacks for account switching operations.
            ctx: Shared TUI context.
        """
        super().__init__()
        self._store = get_account_store()
        self._all_rows = rows
        self._active_account = active_account
        self._env_lock = env_lock
        self._account_callbacks = callbacks
        self._ctx = ctx
        self._keybinds: KeybindRegistry | None = None
        self._toast_bus: ToastBus | None = None
        self._clip_cache: ClipboardAdapter | None = None
        self._filter_text: str = ""
        self._is_switching = False
        self._initialize_context_services()

    @property
    def clipboard(self) -> str:
        """Return clipboard text for Input paste actions."""
        result = self._clip_adapter().read()
        if result.success:
            return result.text
        return super().clipboard

    @clipboard.setter
    def clipboard(self, value: str) -> None:
        setter = App.clipboard.fset
        if setter is not None:
            setter(self, value)

    def compose(self) -> ComposeResult:
        """Build the Textual app (empty, screen is pushed on mount)."""
        # The app itself is empty; AccountsHarlequinScreen is pushed on mount
        if not TEXTUAL_SUPPORTED or Footer is None:
            return  # type: ignore[return-value]
        yield Footer()

    def on_mount(self) -> None:
        """Push the Harlequin accounts screen on mount."""
        self._apply_theme()
        harlequin_screen = AccountsHarlequinScreen(
            rows=self._all_rows,
            active_account=self._active_account,
            env_lock=self._env_lock,
            callbacks=self._account_callbacks,
            ctx=self._ctx,
        )
        self.push_screen(harlequin_screen)

    def _initialize_context_services(self) -> None:
        def _notify(message: ToastBus.Changed) -> None:
            self.post_message(message)

        if self._ctx:
            if self._ctx.keybinds is None:
                self._ctx.keybinds = KeybindRegistry()
            if self._ctx.toasts is None and ToastBus is not None:
                self._ctx.toasts = ToastBus(on_change=_notify)
            if self._ctx.clipboard is None:
                self._ctx.clipboard = ClipboardAdapter(terminal=self._ctx.terminal)
            self._keybinds = self._ctx.keybinds
            self._toast_bus = self._ctx.toasts
            self._clip_cache = self._ctx.clipboard
        else:
            # Fallback: create services independently when ctx is None
            terminal = TerminalCapabilities(
                tty=True, ansi=True, osc52=False, osc11_bg=None, mouse=False, truecolor=False
            )
            self._clip_cache = ClipboardAdapter(terminal=terminal)
            if ToastBus is not None:
                self._toast_bus = ToastBus(on_change=_notify)

    def _prepare_toasts(self) -> None:
        """Prepare toast system by clearing any existing toasts."""
        if self._toast_bus:
            self._toast_bus.clear()

    def _register_keybinds(self) -> None:
        if not self._keybinds:
            return
        for keybind_def in KEYBIND_DEFINITIONS:
            scoped_action = f"{KEYBIND_SCOPE}.{keybind_def.action}"
            if self._keybinds.get(scoped_action):
                continue
            try:
                self._keybinds.register(
                    action=scoped_action,
                    key=keybind_def.key,
                    description=keybind_def.description,
                    category=KEYBIND_CATEGORY,
                )
            except ValueError as e:
                # Expected: duplicate registration (already registered by another component)
                # Silently skip to allow multiple apps to register same keybinds
                logging.debug(f"Skipping duplicate keybind registration: {scoped_action}", exc_info=e)
                continue

    def _header_text(self) -> str:
        """Build header text with active account and host."""
        host = self._get_active_host() or "Not configured"
        lock_icon = " [yellow]🔒[/]" if self._env_lock else ""
        active = self._active_account or "None"
        return f"[green]Active:[/] [bold]{active}[/] ([cyan]{host}[/]){lock_icon}"

    def _get_active_host(self) -> str | None:
        """Return the API host for the active account (shortened)."""
        return self._get_host_for_name(self._active_account)

    def _get_host_for_name(self, name: str | None) -> str | None:
        """Return shortened API URL for a given account name."""
        if not name:
            return None
        for row in self._all_rows:
            if row.get("name") == name:
                url = str(row.get("api_url", ""))
                return url if len(url) <= 40 else f"{url[:37]}..."
        return None

    def action_focus_filter(self) -> None:
        """Focus the filter input and clear previous text."""
        # Skip if Harlequin screen is active (it handles its own filter focus)
        if isinstance(self.screen, AccountsHarlequinScreen):
            return
        try:
            filter_input = self.query_one(FILTER_INPUT_ID, Input)
            filter_input.value = self._filter_text
            filter_input.focus()
        except Exception:
            # Filter input doesn't exist, skip
            pass

    def action_switch_row(self) -> None:
        """Switch to the currently selected account.

        Note: This action is for the old table layout. When using HarlequinScreen,
        the screen handles switching directly. This gracefully skips if the
        old table doesn't exist.
        """
        try:
            table = self.query_one(ACCOUNTS_TABLE_ID, DataTable)
        except Exception:
            # Harlequin screen is active, let it handle the action
            return
        if self._env_lock:
            self._set_status("Switching disabled: env credentials in use.", "yellow")
            return
        if table.cursor_row is None:
            self._set_status("No account selected.", "yellow")
            return
        try:
            row_key = table.get_row_at(table.cursor_row)[0]
        except Exception:
            self._set_status("Unable to read selected row.", "red")
            return
        name = str(row_key)
        if self._is_switching:
            self._set_status("Already switching...", "yellow")
            return
        self._is_switching = True
        host = self._get_host_for_name(name)
        if host:
            self._show_loading(f"Connecting to '{name}' ({host})...")
        else:
            self._show_loading(f"Connecting to '{name}'...")
        self._queue_switch(name)

    def on_data_table_row_selected(self, event: DataTable.RowSelected) -> None:  # type: ignore[override]
        """Handle row selection by triggering switch."""
        self._handle_table_click(self._event_row(event))

    def on_data_table_cell_selected(self, event: DataTable.CellSelected) -> None:  # type: ignore[override]
        """Handle mouse click selection by triggering switch."""
        self._handle_table_click(self._event_row(event))

    def _event_row(self, event: object) -> int | None:
        """Extract the row index from a DataTable event."""
        row = getattr(event, "cursor_row", None)
        if row is not None:
            return int(row)
        coordinate = getattr(event, "coordinate", None)
        return getattr(coordinate, "row", None) if coordinate is not None else None

    def _handle_table_click(self, row: int | None) -> None:
        """Move the cursor to a clicked row and trigger the switch action."""
        if row is None:
            return
        try:
            table = self.query_one(ACCOUNTS_TABLE_ID, DataTable)
        except Exception:
            # Harlequin screen is active, let it handle the action
            return
        try:
            # Move cursor to clicked row then switch
            table.cursor_coordinate = Coordinate(row, 0)
        except Exception:
            return
        self.action_switch_row()

    def on_input_submitted(self, event: Input.Submitted) -> None:
        """Apply filter when user presses Enter inside filter input."""
        # Skip if a screen other than the default app screen is active (e.g., Harlequin or Modal)
        if self.screen.id != "_default":
            return

        self._filter_text = (event.value or "").strip()
        self._reload_rows()
        try:
            table = self.query_one(ACCOUNTS_TABLE_ID, DataTable)
            table.focus()
        except Exception:
            pass
        self._update_filter_button_visibility()

    def on_input_changed(self, event: Input.Changed) -> None:
        """Apply filter live as the user types."""
        # Skip if a screen other than the default app screen is active (e.g., Harlequin or Modal)
        if self.screen.id != "_default":
            return
        self._filter_text = (event.value or "").strip()
        self._reload_rows()
        self._update_filter_button_visibility()

    def _reload_rows(self, preferred_name: str | None = None) -> None:
        """Refresh table rows based on current filter/active state."""
        # Skip if Harlequin screen is active (it handles its own reloading)
        try:
            if isinstance(self.screen, AccountsHarlequinScreen):
                return
        except Exception:  # pragma: no cover - defensive (e.g., ScreenStackError in tests)
            # App not fully initialized or no screen pushed, continue with normal reload
            pass
        # Work on a copy to avoid mutating the backing rows list
        rows_copy = [dict(row) for row in self._all_rows]
        for row in rows_copy:
            row["active"] = row.get("name") == self._active_account

        try:
            table = self.query_one(ACCOUNTS_TABLE_ID, DataTable)
        except Exception:
            # Harlequin screen is active, skip
            return
        table.clear()
        filtered = self._filtered_rows(rows_copy)
        for row in filtered:
            row_for_status = dict(row)
            row_for_status["active"] = row_for_status.get("name") == self._active_account
            # Use markup to align status colors with Rich fallback (green active badge).
            status = build_account_status_string(row_for_status, use_markup=True)
            # pylint: disable=duplicate-code
            # Reuses shared status builder; columns mirror accounts_controller Rich table.
            table.add_row(
                str(row.get("name", "")),
                str(row.get("api_url", "")),
                str(row.get("masked_key", "")),
                status,
            )
        # Move cursor to active or first row
        cursor_idx = 0
        target_name = preferred_name or self._active_account
        for idx, row in enumerate(filtered):
            if row.get("name") == target_name:
                cursor_idx = idx
                break
        if filtered:
            table.cursor_coordinate = (cursor_idx, 0)
        else:
            self._set_status("No accounts match the current filter.", "yellow")
            return

        # Update status to reflect filter state
        if self._filter_text:
            self._set_status(f"Filtered: {self._filter_text}", "cyan")
        else:
            self._set_status("", "white")

    def _filtered_rows(self, rows: list[dict[str, str | bool]] | None = None) -> list[dict[str, str | bool]]:
        """Return rows filtered by name or API URL substring."""
        base_rows = rows if rows is not None else [dict(row) for row in self._all_rows]
        if not self._filter_text:
            return list(base_rows)
        needle = self._filter_text.lower()
        filtered = [
            row
            for row in base_rows
            if needle in str(row.get("name", "")).lower() or needle in str(row.get("api_url", "")).lower()
        ]

        # Sort so name matches surface first, then URL matches, then alphabetically
        def score(row: dict[str, str | bool]) -> tuple[int, str]:
            name = str(row.get("name", "")).lower()
            url = str(row.get("api_url", "")).lower()
            name_hit = needle in name
            url_hit = needle in url
            # Extract nested conditional into clear statement
            if name_hit:
                priority = 0
            elif url_hit:
                priority = 1
            else:
                priority = 2
            return (priority, name)

        return sorted(filtered, key=score)

    def _set_status(self, message: str, style: str) -> None:
        """Update status line with message."""
        status = self.query_one(STATUS_ID, Static)
        status.update(f"[{style}]{message}[/]")

    def _show_loading(self, message: str | None = None) -> None:
        """Show the loading indicator and optional status message."""
        show_loading_indicator(self, ACCOUNTS_LOADING_ID, message=message, set_status=self._set_status)

    def _hide_loading(self) -> None:
        """Hide the loading indicator."""
        hide_loading_indicator(self, ACCOUNTS_LOADING_ID)

    def _handle_switch_scheduling_error(self, exc: Exception) -> None:
        """Handle errors when scheduling the switch task fails.

        Args:
            exc: The exception that occurred during task scheduling.
        """
        self._hide_loading()
        self._is_switching = False
        error_msg = f"Switch failed to start: {exc}"
        if self._toast_bus:
            self._toast_bus.show(message=error_msg, variant="error")
        try:
            self._set_status(error_msg, "red")
        except Exception:
            # App not mounted yet, status update not possible
            logging.error(error_msg, exc_info=exc)
        logging.getLogger(__name__).debug("Failed to schedule switch task", exc_info=exc)

    def _clear_filter(self) -> None:
        """Clear the filter input and reset filter state."""
        # Skip if Harlequin screen is active (it handles its own filtering)
        if isinstance(self.screen, AccountsHarlequinScreen):
            return
        try:
            filter_input = self.query_one(FILTER_INPUT_ID, Input)
            filter_input.value = ""
            self._filter_text = ""
        except Exception:
            # Filter input doesn't exist, just clear the text
            self._filter_text = ""
        self._update_filter_button_visibility()

    def _queue_switch(self, name: str) -> None:
        """Run switch in background to keep UI responsive."""

        async def perform() -> None:
            try:
                switched, message = await asyncio.to_thread(self._account_callbacks.switch_account, name)
            except Exception as exc:  # pragma: no cover - defensive
                self._set_status(f"Switch failed: {exc}", "red")
                return
            finally:
                self._hide_loading()
                self._is_switching = False

            if switched:
                self._active_account = name
                status_msg = message or f"Switched to '{name}'."
                if self._toast_bus:
                    self._toast_bus.show(message=status_msg, variant="success")
                self._update_header()
                self._reload_rows()
            else:
                self._set_status(message or "Switch failed; kept previous account.", "yellow")

        try:
            self.track_task(perform(), logger=logging.getLogger(__name__))
        except Exception as exc:
            self._handle_switch_scheduling_error(exc)

    def _update_header(self) -> None:
        """Refresh header text to reflect active/lock state."""
        header = self.query_one("#header-info", Static)
        header.update(self._header_text())

    def action_clear_or_exit(self) -> None:
        """Clear or exit filter when focused; otherwise exit app.

        UX note: helps users reset the list without leaving the TUI.
        """
        # Skip if Harlequin screen is active (it handles its own exit)
        if isinstance(self.screen, AccountsHarlequinScreen):
            self.exit()
            return
        try:
            filter_input = self.query_one(FILTER_INPUT_ID, Input)
            if filter_input.has_focus:
                # Clear when there is text; otherwise just move focus back to the table
                if filter_input.value or self._filter_text:
                    self._clear_filter()
                    self._reload_rows()
                try:
                    table = self.query_one(ACCOUNTS_TABLE_ID, DataTable)
                    table.focus()
                except Exception:
                    pass
                return
        except Exception:
            # Filter input doesn't exist, just exit
            pass
        self.exit()

    def action_app_exit(self) -> None:
        """Exit the application regardless of focus state."""
        self.exit()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle filter bar buttons."""
        if event.button.id == "filter-clear":
            self._clear_filter()
            self._reload_rows()
            table = self.query_one(ACCOUNTS_TABLE_ID, DataTable)
            table.focus()

    def action_add_account(self) -> None:
        """Open add account modal."""
        if self._check_env_lock_hotkey():
            return
        if self._should_block_actions():
            return
        existing_names = {str(row.get("name", "")) for row in self._all_rows}
        modal = AccountFormModal(
            mode="add",
            existing=None,
            existing_names=existing_names,
            connection_tester=lambda url, key: check_connection_with_reason(url, key, abort_on_error=False),
            validate_name=self._store.validate_account_name,
        )
        self.push_screen(modal, self._on_form_result)

    def action_edit_account(self) -> None:
        """Open edit account modal for selected row."""
        if self._check_env_lock_hotkey():
            return
        if self._should_block_actions():
            return
        name = self._get_selected_name()
        if not name:
            self._set_status("Select an account to edit.", "yellow")
            return
        account = self._store.get_account(name)
        if not account:
            self._set_status(f"Account '{name}' not found.", "red")
            return
        existing_names = {str(row.get("name", "")) for row in self._all_rows if str(row.get("name", "")) != name}
        modal = AccountFormModal(
            mode="edit",
            existing={"name": name, "api_url": account.get("api_url", ""), "api_key": account.get("api_key", "")},
            existing_names=existing_names,
            connection_tester=lambda url, key: check_connection_with_reason(url, key, abort_on_error=False),
            validate_name=self._store.validate_account_name,
        )
        self.push_screen(modal, self._on_form_result)

    def action_delete_account(self) -> None:
        """Open delete confirmation modal."""
        if self._check_env_lock_hotkey():
            return
        if self._should_block_actions():
            return
        name = self._get_selected_name()
        if not name:
            self._set_status("Select an account to delete.", "yellow")
            return
        accounts = self._store.list_accounts()
        if len(accounts) <= 1:
            self._set_status("Cannot remove the last remaining account.", "red")
            return
        self.push_screen(ConfirmDeleteModal(name), self._on_delete_result)

    def action_copy_account(self) -> None:
        """Copy selected account name and URL to clipboard."""
        name = self._get_selected_name()
        if not name:
            self._set_status("Select an account to copy.", "yellow")
            return

        account = self._store.get_account(name)
        if not account:
            return

        text = f"Account: {name}\nURL: {account.get('api_url', '')}"
        adapter = self._clip_adapter()
        writer = self._osc52_writer()
        if writer:
            result = adapter.copy(text, writer=writer)
        else:
            result = adapter.copy(text)
        self._handle_copy_result(name, result)

    def _handle_copy_result(self, name: str, result: ClipboardResult) -> None:
        """Update UI state after a copy attempt."""
        if result.success:
            if self._toast_bus:
                self._toast_bus.copy_success(f"Account '{name}'")
            self._set_status(f"Copied '{name}' to clipboard.", "green")
        else:
            if self._toast_bus and ToastVariant is not None:
                self._toast_bus.show(message=f"Copy failed: {result.message}", variant=ToastVariant.WARNING)
            self._set_status(f"Copy failed: {result.message}", "red")

    def _clip_adapter(self) -> ClipboardAdapter:
        if self._ctx is not None and self._ctx.clipboard is not None:
            return cast(ClipboardAdapter, self._ctx.clipboard)
        if self._clip_cache is not None:
            return self._clip_cache
        adapter = ClipboardAdapter(terminal=self._ctx.terminal if self._ctx else None)
        if self._ctx is not None:
            self._ctx.clipboard = adapter
        else:
            self._clip_cache = adapter
        return adapter

    def _osc52_writer(self) -> Callable[[str], Any] | None:
        try:
            console = getattr(self, "console", None)
        except Exception:
            return None
        if console is None:
            return None
        output = getattr(console, "file", None)
        if output is None:
            return None

        def _write(sequence: str, _output: Any = output) -> None:
            _output.write(sequence)
            _output.flush()

        return _write

    def _check_env_lock_hotkey(self) -> bool:
        """Prevent mutations when env credentials are present."""
        if not self._is_env_locked():
            return False
        self._env_lock = True
        self._set_status("Disabled by env-lock.", "yellow")
        # Refresh UI to reflect env-lock state (header/banners/rows)
        self._refresh_rows(preferred_name=self._active_account)
        return True

    def _on_form_result(self, payload: dict[str, Any] | None) -> None:
        """Handle add/edit modal result."""
        if payload is None:
            self._set_status("Edit/add cancelled.", "yellow")
            return
        self._save_account(payload)

    def _on_delete_result(self, confirmed_name: str | None) -> None:
        """Handle delete confirmation result."""
        if not confirmed_name:
            self._set_status("Delete cancelled.", "yellow")
            return
        try:
            self._store.remove_account(confirmed_name)
        except AccountStoreError as exc:
            self._set_status(f"Delete failed: {exc}", "red")
            return
        except Exception as exc:  # pragma: no cover - defensive
            self._set_status(f"Unexpected delete error: {exc}", "red")
            return

        self._set_status(f"Account '{confirmed_name}' deleted.", "green")
        # Clear filter before refresh to show all accounts
        self._clear_filter()
        # Refresh rows without preferred name to show all accounts
        # Active account will be cleared if the deleted account was active
        self._refresh_rows(preferred_name=None)
        table = self.query_one(ACCOUNTS_TABLE_ID, DataTable)
        table.focus()

    def _save_account(self, payload: dict[str, Any]) -> None:
        """Persist account data from modal payload."""
        if self._is_env_locked():
            self._set_status("Disabled by env-lock.", "yellow")
            return

        name = str(payload.get("name", ""))
        api_url = str(payload.get("api_url", ""))
        api_key = str(payload.get("api_key", ""))
        set_active = bool(payload.get("set_active", payload.get("mode") == "add"))
        is_edit = payload.get("mode") == "edit"

        try:
            self._store.add_account(name, api_url, api_key, overwrite=is_edit)
        except AccountStoreError as exc:
            self._set_status(f"Save failed: {exc}", "red")
            return
        except Exception as exc:  # pragma: no cover - defensive
            self._set_status(f"Unexpected save error: {exc}", "red")
            return

        if set_active:
            try:
                self._store.set_active_account(name)
                self._active_account = name
            except Exception as exc:  # pragma: no cover - defensive
                self._set_status(f"Saved but could not set active: {exc}", "yellow")
            else:
                self._announce_active_change(name)
                self._update_header()

        self._set_status(f"Account '{name}' saved.", "green")
        # Clear filter before refresh to show all accounts
        self._clear_filter()
        # Refresh rows with preferred name to highlight the saved account
        self._refresh_rows(preferred_name=name)
        # Return focus to the table for immediate hotkey use
        table = self.query_one(ACCOUNTS_TABLE_ID, DataTable)
        table.focus()

    def _refresh_rows(self, preferred_name: str | None = None) -> None:
        """Reload rows from store and preserve filter/cursor."""
        self._env_lock = self._is_env_locked()
        self._all_rows, self._active_account = _build_account_rows_from_store(self._store, self._env_lock)
        self._reload_rows(preferred_name=preferred_name)
        self._update_header()

    def _get_selected_name(self) -> str | None:
        """Return selected account name, if any."""
        table = self.query_one(ACCOUNTS_TABLE_ID, DataTable)
        if table.cursor_row is None:
            return None
        try:
            row = table.get_row_at(table.cursor_row)
        except Exception:
            return None
        return str(row[0]) if row else None

    def _is_env_locked(self) -> bool:
        """Return True when env credentials are set (even partially)."""
        return env_credentials_present(partial=True)

    def _announce_active_change(self, name: str) -> None:
        """Surface active account change in status bar."""
        account = self._store.get_account(name) or {}
        host = account.get("api_url", "")
        host_suffix = f" • {host}" if host else ""
        self._set_status(f"Active account ➜ {name}{host_suffix}", "green")

    def _should_block_actions(self) -> bool:
        """Return True when mutating hotkeys are blocked by filter focus."""
        filter_input = self.query_one(FILTER_INPUT_ID, Input)
        if filter_input.has_focus:
            self._set_status("Exit filter (Esc or Clear) to add/edit/delete.", "yellow")
            return True
        return False

    def _update_filter_button_visibility(self) -> None:
        """Show clear button only when filter has content."""
        # Skip if Harlequin screen is active (it doesn't have this button)
        if isinstance(self.screen, AccountsHarlequinScreen):
            return
        try:
            filter_input = self.query_one(FILTER_INPUT_ID, Input)
            clear_btn = self.query_one("#filter-clear", Button)
            clear_btn.display = bool(filter_input.value or self._filter_text)
        except Exception:
            # Filter input or clear button doesn't exist, skip
            pass

    def _apply_theme(self) -> None:
        """Register built-in themes and set the active one from context."""
        if not self._ctx or not self._ctx.theme or Theme is None:
            return

        for name, tokens in _BUILTIN_THEMES.items():
            self.register_theme(
                Theme(
                    name=name,
                    primary=tokens.primary,
                    secondary=tokens.secondary,
                    accent=tokens.accent,
                    warning=tokens.warning,
                    error=tokens.error,
                    success=tokens.success,
                )
            )

        self.theme = self._ctx.theme.theme_name
