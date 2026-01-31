"""Textual UI for the /runs command.

This module provides a lightweight Textual application that mirrors the remote
run browser experience using rich widgets (DataTable, modals, footer hints).

Authors:
    Raymond Christopher (raymond.christopher@gdplabs.id)
"""

from __future__ import annotations

import asyncio
import json
import logging
from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from rich.text import Text

from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal, Vertical
from textual.coordinate import Coordinate
from textual.reactive import ReactiveError
from textual.screen import ModalScreen
from textual.widgets import DataTable, Footer, Header, RichLog, Static

from glaip_sdk.cli.slash.tui.clipboard import ClipboardAdapter
from glaip_sdk.cli.slash.tui.context import TUIContext
from glaip_sdk.cli.slash.tui.indicators import PulseIndicator
from glaip_sdk.cli.slash.tui.loading import hide_loading_indicator, show_loading_indicator
from glaip_sdk.cli.slash.tui.toast import ClipboardToastMixin, Toast, ToastBus, ToastContainer, ToastHandlerMixin

logger = logging.getLogger(__name__)

RUNS_TABLE_ID = "runs"
RUNS_LOADING_ID = "runs-loading"
RUNS_TABLE_SELECTOR = f"#{RUNS_TABLE_ID}"
RUNS_LOADING_SELECTOR = f"#{RUNS_LOADING_ID}"


@dataclass
class RemoteRunsTUICallbacks:
    """Callbacks invoked by the Textual UI for data operations."""

    fetch_page: Callable[[int, int], Any | None]
    fetch_detail: Callable[[str], Any | None]
    export_run: Callable[[str, Any | None], bool]


def run_remote_runs_textual(
    initial_page: Any,
    cursor_idx: int,
    callbacks: RemoteRunsTUICallbacks,
    *,
    agent_name: str | None = None,
    agent_id: str | None = None,
    ctx: TUIContext | None = None,
) -> tuple[int, int, int]:
    """Launch the Textual application and return the final pagination state.

    Args:
        initial_page: RunsPage instance loaded before launching the UI.
        cursor_idx: Previously selected row index.
        callbacks: Data provider callback bundle.
        agent_name: Optional agent name for display purposes.
        agent_id: Optional agent ID for display purposes.
        ctx: Shared TUI context.

    Returns:
        Tuple of (page, limit, cursor_index) after the UI exits.
    """
    app = RemoteRunsTextualApp(
        initial_page,
        cursor_idx,
        callbacks,
        agent_name=agent_name,
        agent_id=agent_id,
        ctx=ctx,
    )
    app.run()
    current_page = getattr(app, "current_page", initial_page)
    return current_page.page, current_page.limit, app.cursor_index


class RunDetailScreen(ToastHandlerMixin, ClipboardToastMixin, ModalScreen[None]):
    """Modal screen displaying run metadata and output timeline."""

    CSS = """
    Screen { layout: vertical; layers: base toasts; }
    #toast-container {
        width: 100%;
        height: auto;
        dock: top;
        align: right top;
        layer: toasts;
    }
    """

    BINDINGS = [
        Binding("escape", "dismiss", "Close", priority=True),
        Binding("q", "dismiss_modal", "Close", priority=True),
        Binding("up", "scroll_up", "Up"),
        Binding("down", "scroll_down", "Down"),
        Binding("pageup", "page_up", "PgUp"),
        Binding("pagedown", "page_down", "PgDn"),
        Binding("c", "copy_run_id", "Copy ID"),
        Binding("C", "copy_detail_json", "Copy JSON"),
        Binding("e", "export_detail", "Export"),
    ]

    def __init__(
        self,
        detail: Any,
        on_export: Callable[[Any], None] | None = None,
        ctx: TUIContext | None = None,
    ) -> None:
        """Initialize the run detail screen."""
        super().__init__()
        self.detail = detail
        self._on_export = on_export
        self._ctx = ctx
        self._clip_cache: ClipboardAdapter | None = None
        self._local_toasts: ToastBus | None = None

    def compose(self) -> ComposeResult:
        """Render metadata and events."""
        meta_text = Text()

        def add_meta(label: str, value: Any | None, value_style: str | None = None) -> None:
            if value in (None, ""):
                return
            if len(meta_text) > 0:
                meta_text.append("\n")
            meta_text.append(f"{label}: ", style="bold cyan")
            meta_text.append(str(value), style=value_style)

        add_meta("Run ID", self.detail.id)
        add_meta("Agent ID", getattr(self.detail, "agent_id", "-"))
        add_meta("Type", getattr(self.detail, "run_type", "-"), "bold yellow")
        status_value = getattr(self.detail, "status", "-")
        add_meta("Status", status_value, self._status_style(status_value))
        add_meta("Started", getattr(self.detail, "started_at", None))
        add_meta("Completed", getattr(self.detail, "completed_at", None))
        duration = self.detail.duration_formatted() if getattr(self.detail, "duration_formatted", None) else None
        add_meta("Duration", duration, "bold")

        main_content = Vertical(
            Static(meta_text, id="detail-meta"),
            RichLog(id="detail-events", wrap=False),
        )
        yield main_content
        yield ToastContainer(Toast(), id="toast-container")
        yield Footer()

    def on_mount(self) -> None:
        """Populate and focus the log."""
        self._ensure_toast_bus()
        log = self.query_one("#detail-events", RichLog)
        log.can_focus = True
        log.write(Text("Events", style="bold"))
        for chunk in getattr(self.detail, "output", []):
            event_type = chunk.get("event_type", "event")
            status = chunk.get("status", "-")
            timestamp = chunk.get("received_at") or "-"
            header = Text()
            header.append(timestamp, style="cyan")
            header.append(" ")
            header.append(event_type, style=self._event_type_style(event_type))
            header.append(" ")
            header.append("[")
            header.append(status, style=self._status_style(status))
            header.append("]")
            log.write(header)

            payload = Text(json.dumps(chunk, indent=2, ensure_ascii=False), style="dim")
            log.write(payload)
            log.write(Text(""))
        log.focus()

    def _log(self) -> RichLog:
        return self.query_one("#detail-events", RichLog)

    def action_copy_run_id(self) -> None:
        """Copy the run id to the clipboard."""
        run_id = getattr(self.detail, "id", None)
        if not run_id:
            self._announce_status("Run ID unavailable.")
            return
        self._copy_to_clipboard(str(run_id), label="Run ID")

    def action_copy_detail_json(self) -> None:
        """Copy the run detail JSON to the clipboard."""
        payload = self._detail_json_payload()
        if payload is None:
            return
        self._copy_to_clipboard(payload, label="Run JSON")

    def _detail_json_payload(self) -> str | None:
        detail = self.detail
        if detail is None:
            self._announce_status("Run detail unavailable.")
            return None
        if isinstance(detail, str):
            return detail
        if isinstance(detail, dict):
            payload = detail
        elif hasattr(detail, "model_dump"):
            payload = detail.model_dump(mode="json")
        elif hasattr(detail, "dict"):
            payload = detail.dict()
        else:
            payload = getattr(detail, "__dict__", {"value": detail})
        try:
            return json.dumps(payload, indent=2, ensure_ascii=False, default=str)
        except Exception as exc:
            self._announce_status(f"Failed to serialize run detail: {exc}")
            return None

    def _append_copy_fallback(self, text: str) -> None:
        try:
            log = self._log()
        except Exception:
            self._announce_status(text)
            return
        log.write(Text(text))
        log.write(Text(""))

    def _ensure_toast_bus(self) -> None:
        """Ensure toast bus is initialized and connected to message handler."""
        if self._local_toasts is not None:
            return  # pragma: no cover - early return when already initialized

        def _notify(m: ToastBus.Changed) -> None:
            self.post_message(m)

        self._local_toasts = ToastBus(on_change=_notify)

    @staticmethod
    def _status_style(status: str | None) -> str:
        """Return a Rich style name for the status pill."""
        if not status:
            return "dim"
        normalized = str(status).lower()
        if normalized in {"success", "succeeded", "completed", "ok"}:
            return "green"
        if normalized in {"failed", "error", "errored", "cancelled"}:
            return "red"
        if normalized in {"running", "in_progress", "queued"}:
            return "yellow"
        return "cyan"

    @staticmethod
    def _event_type_style(event_type: str | None) -> str:
        """Return a highlight color for the event type label."""
        if not event_type:
            return "white"
        normalized = str(event_type).lower()
        if "error" in normalized or "fail" in normalized:
            return "red"
        if "status" in normalized:
            return "magenta"
        if "tool" in normalized:
            return "yellow"
        if "stream" in normalized:
            return "cyan"
        return "green"

    def action_dismiss_modal(self) -> None:
        """Allow q binding to close the modal like Esc."""
        self.dismiss(None)

    def action_scroll_up(self) -> None:
        """Scroll the log view up."""
        self._log().action_scroll_up()

    def action_scroll_down(self) -> None:
        """Scroll the log view down."""
        self._log().action_scroll_down()

    def action_page_up(self) -> None:
        """Scroll the log view up one page."""
        self._log().action_page_up()

    def action_page_down(self) -> None:
        """Scroll the log view down one page."""
        self._log().action_page_down()

    def action_export_detail(self) -> None:
        """Trigger export from the detail modal."""
        if self._on_export is None:
            self._announce_status("Export unavailable in this terminal mode.")
            return
        try:
            self._on_export(self.detail)
        except Exception as exc:  # pragma: no cover - defensive
            self._announce_status(f"Export failed: {exc}")

    def _announce_status(self, message: str) -> None:
        """Send status text to the parent app when available."""
        try:
            app = self.app
        except AttributeError:
            return
        update_status = getattr(app, "_update_status", None)
        if callable(update_status):
            update_status(message, append=True)


class RemoteRunsTextualApp(ToastHandlerMixin, App[None]):
    """Textual application for browsing remote runs."""

    CSS = f"""
    #toast-container {{
        width: 100%;
        height: auto;
        dock: top;
        align: right top;
        layer: toasts;
    }}
    #{RUNS_LOADING_ID} {{
        width: auto;
        display: none;
    }}
    #status-bar {{
        height: 3;
        padding: 0 1;
    }}
    """

    BINDINGS = [
        Binding("q", "close_view", "Quit", priority=True),
        Binding("escape", "close_view", "Quit", show=False, priority=True),
        Binding("left", "page_left", "Prev page", priority=True),
        Binding("right", "page_right", "Next page", priority=True),
        Binding("enter", "open_detail", "Select Run", priority=True),
    ]

    def __init__(
        self,
        initial_page: Any,
        cursor_idx: int,
        callbacks: RemoteRunsTUICallbacks,
        *,
        agent_name: str | None = None,
        agent_id: str | None = None,
        ctx: TUIContext | None = None,
    ):
        """Initialize the remote runs Textual application.

        Args:
            initial_page: RunsPage instance to display initially.
            cursor_idx: Initial cursor position in the table.
            callbacks: Callback bundle for data operations.
            agent_name: Optional agent name for display purposes.
            agent_id: Optional agent ID for display purposes.
            ctx: Shared TUI context.
        """
        super().__init__()
        self.current_page = initial_page
        self.cursor_index = max(0, min(cursor_idx, max(len(initial_page.data) - 1, 0)))
        self.callbacks = callbacks
        self.status_text = ""
        self.current_rows = initial_page.data[:]
        self.agent_name = (agent_name or "").strip()
        self.agent_id = (agent_id or "").strip()
        self._ctx = ctx
        self._clip_cache: ClipboardAdapter | None = None
        self._active_export_tasks: set[asyncio.Task[None]] = set()
        self._page_loader_task: asyncio.Task[Any] | None = None
        self._detail_loader_task: asyncio.Task[Any] | None = None
        self._table_spinner_active = False

    @property
    def clipboard(self) -> str:
        """Return clipboard text for Input paste actions."""
        if self._ctx is not None:
            adapter = self._ctx.clipboard
            if adapter is None:
                adapter = ClipboardAdapter(terminal=self._ctx.terminal)
                self._ctx.clipboard = adapter
            result = adapter.read()
            if result.success:
                return result.text
        if self._ctx is None and self._clip_cache is None:
            self._clip_cache = ClipboardAdapter(terminal=None)
        if self._clip_cache is not None:
            result = self._clip_cache.read()
            if result.success:
                return result.text
        return super().clipboard

    @clipboard.setter
    def clipboard(self, value: str) -> None:
        setter = App.clipboard.fset
        if setter is not None:
            setter(self, value)

    def compose(self) -> ComposeResult:
        """Build layout."""
        yield Header()
        yield ToastContainer(Toast(), id="toast-container")
        table = DataTable(id=RUNS_TABLE_ID)  # pragma: no cover - mocked in tests
        table.cursor_type = "row"  # pragma: no cover - mocked in tests
        table.add_columns(  # pragma: no cover - mocked in tests
            "Run UUID",
            "Type",
            "Status",
            "Started (UTC)",
            "Completed (UTC)",
            "Duration",
            "Input Preview",
        )
        yield table  # pragma: no cover - interactive UI, tested via integration
        yield Horizontal(  # pragma: no cover - interactive UI, tested via integration
            PulseIndicator(id=RUNS_LOADING_ID),
            Static(id="status"),
            id="status-bar",
        )
        yield Footer()  # pragma: no cover - interactive UI, tested via integration

    def _ensure_toast_bus(self) -> None:
        if self._ctx is None or self._ctx.toasts is not None:
            return

        def _notify(m: ToastBus.Changed) -> None:
            self.post_message(m)

        self._ctx.toasts = ToastBus(on_change=_notify)

    def on_mount(self) -> None:
        """Render the initial page."""
        self._ensure_toast_bus()
        self._hide_loading()
        self._render_page(self.current_page)

    def _render_page(self, runs_page: Any) -> None:
        """Populate table rows for a RunsPage."""
        table = self.query_one(RUNS_TABLE_SELECTOR, DataTable)
        table.clear()
        self.current_rows = runs_page.data[:]
        for run in self.current_rows:
            table.add_row(
                str(run.id),
                str(run.run_type).title(),
                str(run.status).upper(),
                run.started_at.strftime("%Y-%m-%d %H:%M:%S") if run.started_at else "—",
                run.completed_at.strftime("%Y-%m-%d %H:%M:%S") if run.completed_at else "—",
                run.duration_formatted(),
                run.input_preview(),
            )
        if self.current_rows:
            self.cursor_index = max(0, min(self.cursor_index, len(self.current_rows) - 1))
            table.focus()
            table.cursor_coordinate = Coordinate(self.cursor_index, 0)
        self.current_page = runs_page
        total_pages = max(1, (runs_page.total + runs_page.limit - 1) // runs_page.limit)
        agent_display = self.agent_name or "Runs"
        header = f"{agent_display} • Page {runs_page.page}/{total_pages} • Page size={runs_page.limit}"
        try:
            self.sub_title = header
        except ReactiveError:
            # App not fully initialized (common in tests), skip setting sub_title
            logger.debug("Cannot set sub_title: app not fully initialized")
        self._clear_status()

    def _agent_context_label(self) -> str:
        """Return a descriptive label for the active agent."""
        name = self.agent_name
        identifier = self.agent_id
        if name and identifier:
            return f"Agent: {name} ({identifier})"
        if name:
            return f"Agent: {name}"
        if identifier:
            return f"Agent: {identifier}"
        return "Agent runs"

    def _update_status(self, message: str, *, append: bool = False) -> None:
        """Update the footer status text."""
        try:
            static = self.query_one("#status", Static)
        except (AttributeError, RuntimeError) as e:
            # App not fully initialized (common in tests), just update status_text
            logger.debug("Cannot update status widget: app not fully initialized (%s)", type(e).__name__)
            if append:
                self.status_text = f"{self.status_text}\n{message}"
            else:
                self.status_text = message
            return
        if append:
            self.status_text = f"{self.status_text}\n{message}"
        else:
            self.status_text = message
        static.update(self.status_text)

    def _clear_status(self) -> None:
        """Clear any status message."""
        self.status_text = ""
        try:
            static = self.query_one("#status", Static)
            static.update("")
        except (AttributeError, RuntimeError) as e:
            # App not fully initialized (common in tests), skip widget update
            logger.debug("Cannot clear status widget: app not fully initialized (%s)", type(e).__name__)

    def on_data_table_row_highlighted(self, event: DataTable.RowHighlighted) -> None:  # pragma: no cover - UI hook
        """Track cursor position when DataTable selection changes."""
        self.cursor_index = getattr(event, "cursor_row", self.cursor_index)

    def _handle_table_click(self, row: int | None) -> None:
        if row is None:
            return
        table = self.query_one(RUNS_TABLE_SELECTOR, DataTable)
        self.cursor_index = row
        try:
            table.cursor_coordinate = Coordinate(row, 0)
        except Exception:
            return
        self.action_open_detail()

    def on_data_table_row_selected(self, event: DataTable.RowSelected) -> None:  # pragma: no cover - UI hook
        """Handle row selection event from DataTable."""
        self._handle_table_click(getattr(event, "cursor_row", None))

    def on_data_table_cell_selected(self, event: DataTable.CellSelected) -> None:  # pragma: no cover - UI hook
        """Handle cell selection event from DataTable."""
        row = getattr(event.coordinate, "row", None) if event.coordinate else None
        self._handle_table_click(row)

    def action_page_left(self) -> None:
        """Navigate to the previous page."""
        if not self.current_page.has_prev:
            self._update_status("Already at the first page.", append=True)
            return
        target_page = max(1, self.current_page.page - 1)
        self._queue_page_load(
            target_page,
            loading_message="Loading previous page…",
            failure_message="Failed to load previous page.",
        )

    def action_page_right(self) -> None:
        """Navigate to the next page."""
        if not self.current_page.has_next:
            self._update_status("This is the last page.", append=True)
            return
        target_page = self.current_page.page + 1
        self._queue_page_load(
            target_page,
            loading_message="Loading next page…",
            failure_message="Failed to load next page.",
        )

    def _selected_run(self) -> Any | None:
        """Return the currently highlighted run."""
        if not self.current_rows:
            return None
        if self.cursor_index < 0 or self.cursor_index >= len(self.current_rows):
            return None
        return self.current_rows[self.cursor_index]

    def action_open_detail(self) -> None:
        """Open detail modal for the selected run."""
        run = self._selected_run()
        if not run:
            self._update_status("No run selected.", append=True)
            return
        if self._detail_loader_task and not self._detail_loader_task.done():
            self._update_status("Already loading run detail. Please wait…", append=True)
            return
        run_id = str(run.id)
        self._show_loading("Loading run detail…", table_spinner=False, footer_message=False)
        self._queue_detail_load(run_id)

    async def action_export_run(self) -> None:
        """Export the selected run via callback."""
        run = self._selected_run()
        if not run:
            self._update_status("No run selected.", append=True)
            return
        detail = self.callbacks.fetch_detail(str(run.id))
        if detail is None:
            self._update_status("Failed to load run detail for export.", append=True)
            return
        self._queue_export_job(str(run.id), detail)

    def action_close_view(self) -> None:
        """Handle quit bindings by closing detail views first, otherwise exiting."""
        try:
            if isinstance(self.screen, RunDetailScreen):
                self.pop_screen()
                self._clear_status()
                return
        except (AttributeError, RuntimeError) as e:
            # App not fully initialized (common in tests), skip screen check
            logger.debug("Cannot check screen state: app not fully initialized (%s)", type(e).__name__)
        self.exit()

    def _queue_page_load(self, target_page: int, *, loading_message: str, failure_message: str) -> None:
        """Show a loading indicator and fetch a page after the next refresh."""
        limit = self.current_page.limit
        self._show_loading(loading_message, footer_message=False)

        if self._page_loader_task and not self._page_loader_task.done():
            self._update_status("Already loading a page. Please wait…", append=True)
            return

        loader_coro = self._load_page_async(target_page, limit, failure_message)
        try:
            task = asyncio.create_task(loader_coro, name="remote-runs-fetch")
        except RuntimeError:
            logger.debug("No running event loop; loading page synchronously.")
            loader_coro.close()
            self._load_page_sync(target_page, limit, failure_message)
            return
        except Exception:
            loader_coro.close()
            raise
        task.add_done_callback(self._on_page_loader_done)
        self._page_loader_task = task

    def _queue_detail_load(self, run_id: str) -> None:
        """Fetch run detail asynchronously with spinner feedback."""
        loader_coro = self._load_detail_async(run_id)
        try:
            task = asyncio.create_task(loader_coro, name=f"remote-runs-detail-{run_id}")
        except RuntimeError:
            logger.debug("No running event loop; loading run detail synchronously.")
            loader_coro.close()
            self._load_detail_sync(run_id)
            return
        except Exception:
            loader_coro.close()
            raise
        task.add_done_callback(self._on_detail_loader_done)
        self._detail_loader_task = task

    async def _load_page_async(self, page: int, limit: int, failure_message: str) -> None:
        """Fetch the requested page in the background to keep the UI responsive."""
        try:
            new_page = await asyncio.to_thread(self.callbacks.fetch_page, page, limit)
        except Exception as exc:  # pragma: no cover - defensive logging for unexpected errors
            logger.exception("Failed to fetch remote runs page %s: %s", page, exc)
            new_page = None
        finally:
            self._hide_loading()

        if new_page is None:
            self._update_status(failure_message)
            return
        self._render_page(new_page)

    def _load_page_sync(self, page: int, limit: int, failure_message: str) -> None:
        """Fallback for fetching a page when asyncio isn't active (tests)."""
        try:
            new_page = self.callbacks.fetch_page(page, limit)
        except Exception as exc:  # pragma: no cover - defensive logging for unexpected errors
            logger.exception("Failed to fetch remote runs page %s: %s", page, exc)
            new_page = None
        finally:
            self._hide_loading()

        if new_page is None:
            self._update_status(failure_message)
            return
        self._render_page(new_page)

    def _on_page_loader_done(self, task: asyncio.Task[Any]) -> None:
        """Reset loader state and surface unexpected failures."""
        self._page_loader_task = None
        if task.cancelled():
            return
        exc = task.exception()
        if exc:
            logger.debug("Page loader encountered an error: %s", exc)

    def _on_detail_loader_done(self, task: asyncio.Task[Any]) -> None:
        """Reset state for the detail fetch task."""
        self._detail_loader_task = None
        if task.cancelled():
            return
        exc = task.exception()
        if exc:
            logger.debug("Detail loader encountered an error: %s", exc)

    async def _load_detail_async(self, run_id: str) -> None:
        """Retrieve run detail via background thread."""
        try:
            detail = await asyncio.to_thread(self.callbacks.fetch_detail, run_id)
        except Exception as exc:  # pragma: no cover - defensive logging for unexpected errors
            logger.exception("Failed to load run detail %s: %s", run_id, exc)
            detail = None
        finally:
            self._hide_loading()
        self._present_run_detail(detail)

    def _load_detail_sync(self, run_id: str) -> None:
        """Synchronous fallback for fetching run detail."""
        try:
            detail = self.callbacks.fetch_detail(run_id)
        except Exception as exc:  # pragma: no cover - defensive logging for unexpected errors
            logger.exception("Failed to load run detail %s: %s", run_id, exc)
            detail = None
        finally:
            self._hide_loading()
        self._present_run_detail(detail)

    def _present_run_detail(self, detail: Any | None) -> None:
        """Push the detail modal or surface an error."""
        if detail is None:
            self._update_status("Failed to load run detail.", append=True)
            return
        self.push_screen(RunDetailScreen(detail, on_export=self.queue_export_from_detail, ctx=self._ctx))
        self._update_status("Detail view: ↑/↓ scroll · PgUp/PgDn · q/Esc close · c copy ID · C copy JSON · e export")

    def queue_export_from_detail(self, detail: Any) -> None:
        """Start an export from the detail modal."""
        run_id = getattr(detail, "id", None)
        if not run_id:
            self._update_status("Cannot export run without an identifier.", append=True)
            return
        self._queue_export_job(str(run_id), detail)

    def _queue_export_job(self, run_id: str, detail: Any) -> None:
        """Schedule the export coroutine so it can suspend cleanly."""

        async def runner() -> None:
            await self._perform_export(run_id, detail)

        try:
            self.run_worker(runner(), name="export-run", exclusive=True)
        except Exception:
            # Store task to prevent premature garbage collection
            export_task = asyncio.create_task(runner())
            # Keep reference to prevent GC (task will complete on its own)
            self._active_export_tasks.add(export_task)
            export_task.add_done_callback(self._active_export_tasks.discard)

    async def _perform_export(self, run_id: str, detail: Any) -> None:
        """Execute the export callback with suspend mode."""
        try:
            with self.suspend():
                success = bool(self.callbacks.export_run(run_id, detail))
        except Exception as exc:  # pragma: no cover - defensive
            logger.exception("Export failed: %s", exc)
            self._update_status(f"Export failed: {exc}", append=True)
            return

        if success:
            self._update_status("Export complete (see slash console for path).", append=True)
        else:
            self._update_status("Export cancelled.", append=True)

    def _show_loading(
        self,
        message: str | None = None,
        *,
        table_spinner: bool = True,
        footer_message: bool = True,
    ) -> None:
        """Display the loading indicator with an optional status message."""
        show_loading_indicator(
            self,
            RUNS_LOADING_SELECTOR,
            message=message,
            set_status=self._update_status if footer_message else None,
        )
        self._set_table_loading(table_spinner)
        self._table_spinner_active = table_spinner

    def _hide_loading(self) -> None:
        """Hide the loading indicator."""
        hide_loading_indicator(self, RUNS_LOADING_SELECTOR)
        if self._table_spinner_active:
            self._set_table_loading(False)
            self._table_spinner_active = False

    def _set_table_loading(self, is_loading: bool) -> None:
        """Toggle the DataTable loading shimmer."""
        try:
            table = self.query_one(RUNS_TABLE_SELECTOR, DataTable)
            table.loading = is_loading
        except (AttributeError, RuntimeError) as e:
            logger.debug("Cannot toggle table loading state: %s", type(e).__name__)
