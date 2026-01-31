"""TUI animated indicators for waiting states."""

from __future__ import annotations

from typing import Any

from rich.text import Text
from textual._context import NoActiveAppError
from textual.timer import Timer
from textual.widgets import Static

from glaip_sdk.cli.slash.tui.theme.catalog import _BUILTIN_THEMES

DEFAULT_MESSAGE = "Processing…"
DEFAULT_WIDTH = 20
DEFAULT_SPEED_MS = 40

BAR_GLYPH = " "
PULSE_GLYPH = "█"

VARIANT_STYLES: dict[str, str] = {
    # Default hex colors matching gl-dark theme (see theme/catalog.py)
    # These are used as fallbacks when the app theme is not active
    "accent": "#C77DFF",
    "primary": "#6EA8FE",
    "success": "#34D399",
    "warning": "#FBBF24",
    "error": "#F87171",
    "info": "#60A5FA",
    "subtle": "#9CA3AF",
}


class PulseIndicator(Static):
    """A Codex-style moving light/pulse indicator for waiting states.

    Mirrors the 'Knight Rider' / Cylon scanner animation pattern.
    Specified in specs/architecture/cli-textual-animated-indicators/spec.md
    """

    DEFAULT_CSS = """
    PulseIndicator {
        width: auto;
        height: 3;
        content-align: center middle;
        padding: 0 2;
        border: round #666666;
        color: $text;
        background: $surface;
    }
    """

    def __init__(
        self,
        message: str | None = None,
        *,
        width: int = DEFAULT_WIDTH,
        speed_ms: int = DEFAULT_SPEED_MS,
        variant: str = "accent",
        low_motion: bool = False,
        **kwargs: Any,
    ) -> None:
        """Initialize the PulseIndicator."""
        super().__init__(**kwargs)
        self._width = self._coerce_width(width)
        self._speed_ms = self._coerce_speed(speed_ms)
        self._variant = self._coerce_variant(variant)
        self._message = self._normalize_message(message)
        self._low_motion = bool(low_motion)
        self._position = 0
        self._direction = 1
        self._timer: Timer | None = None
        self._pending_render: Text | None = None
        self.can_focus = False
        self.accessible_label = self._message

    def on_mount(self) -> None:
        """Handle component mounting."""
        # Initial render happens here to ensure component is ready for updates
        self._safe_update(self._render_static() if self._low_motion else self._render_frame())
        if self._pending_render is not None:
            return
        if self._timer is None and not self._low_motion:
            self._timer = self.set_interval(self._speed_ms / 1000, self._tick)

    def start(self, message: str | None = None) -> None:
        """Start the pulse animation."""
        if message is not None:
            self.update_message(message)
        self._apply_pending_render()
        self._cancel_timer()
        if self._low_motion:
            self._position = 0
            self._safe_update(self._render_static())
            return
        self._timer = self.set_interval(self._speed_ms / 1000, self._tick)
        self._safe_update(self._render_frame())

    def stop(self, message: str | None = None) -> None:
        """Stop the pulse animation."""
        if message is not None:
            self.update_message(message)
        self._cancel_timer()
        self._position = 0
        self._direction = 1
        self._safe_update(self._render_static())

    def update_message(self, message: str) -> None:
        """Update the display message."""
        self._message = self._normalize_message(message)
        self.accessible_label = self._message
        self._safe_update(self._render_static() if self._low_motion else self._render_frame())

    def _tick(self) -> None:
        self._position += self._direction
        if self._position >= self._width - 1:
            self._position = self._width - 1
            self._direction = -1
        elif self._position <= 0:
            self._position = 0
            self._direction = 1
        self._safe_update(self._render_frame())

    def _render_frame(self) -> Text:
        bar = self._render_bar(self._position, active=True)
        bar.append(" ")
        bar.append(self._message, style=self._message_style)
        return bar

    def _render_static(self) -> Text:
        bar = self._render_bar(0, active=False)
        bar.append(" ")
        bar.append(self._message, style=self._message_style)
        return bar

    def _render_bar(self, position: int, *, active: bool) -> Text:
        bg = self._resolve_style("on #111111", "$surface", is_bg=True)
        bar = Text("[", style=f"grey37 {bg}")

        p = position
        v = self._active_style

        for index in range(self._width):
            if not active:
                glyph = "█"
                style = f"dim {v} {bg}"
            else:
                glyph, style = self._get_pulse_glyph_and_style(index, p, v, bg)

            bar.append(glyph, style=style)

        bar.append("]", style=f"grey37 {bg}")
        return bar

    def _get_pulse_glyph_and_style(self, index: int, p: int, v: str, bg: str) -> tuple[str, str]:
        """Determine glyph and style for a bar position during animation."""
        dist = abs(index - p)
        if dist == 0:
            return "█", f"bold white {bg}"
        if dist == 1:
            return "█", f"{v} {bg}"
        if dist == 2:
            return "▓", f"dim {v} {bg}"
        if dist == 3:
            return "▒", f"dim {v} {bg}"
        return " ", bg

    @property
    def _active_style(self) -> str:
        token = f"${self._variant}"
        fallback = VARIANT_STYLES.get(self._variant, VARIANT_STYLES["accent"])
        return self._resolve_style(fallback, token)

    @property
    def _message_style(self) -> str:
        token = "$text-muted" if self._variant == "subtle" else "$text"
        fallback = VARIANT_STYLES["subtle"] if self._variant == "subtle" else "white"
        return self._resolve_style(fallback, token)

    def _resolve_style(self, fallback: str, token: str | None = None, *, is_bg: bool = False) -> str:
        """Resolve a theme token to a Rich style string with fallback."""
        try:
            # Standard resolution sequence
            res = self._do_resolve(token, is_bg)
            if res:
                return res

            # Specific background resolution fallback
            if is_bg:
                res = self._do_resolve("$surface", True) or self._do_resolve("$background", True)
                if res:
                    return res
        except (NoActiveAppError, AttributeError):
            pass
        return fallback

    def _do_resolve(self, token: str | None, is_bg: bool) -> str | None:
        """Internal resolver that tries multiple sources."""
        if not token:
            return None

        # 1. Try resolving via component styles
        if token.startswith("$"):
            res = self._resolve_from_component(token, is_bg)
            if res:
                return res

        # 2. Try direct variable lookup (App.theme_variables or Theme.variables)
        res = self._resolve_from_theme_vars(token.lstrip("$"), is_bg)
        if res:
            return res

        # 3. Try our built-in theme catalog
        return self._resolve_from_catalog(token.lstrip("$"), is_bg)

    def _resolve_from_component(self, token: str, is_bg: bool) -> str | None:
        """Resolve style from Textual component registry."""
        try:
            style = self.app.get_component_rich_style(token)
            color = style.bgcolor if is_bg else style.color
            if color:
                return self._color_to_rich_style(color, is_bg)
        except Exception:
            pass
        return None

    def _resolve_from_theme_vars(self, var_name: str, is_bg: bool) -> str | None:
        """Resolve color from theme variables dictionary."""
        try:
            app = self.app
            # Check theme_variables first
            val = getattr(app, "theme_variables", {}).get(var_name)
            if val is None:
                # Fallback to current theme object's variables (Textual 0.52+)
                theme_obj = app.get_theme(app.theme)
                if theme_obj and hasattr(theme_obj, "variables"):
                    val = theme_obj.variables.get(var_name)

            if val:
                return self._color_to_rich_style(val, is_bg)
        except Exception:
            pass
        return None

    def _resolve_from_catalog(self, var_name: str, is_bg: bool) -> str | None:
        """Resolve color from our built-in theme catalog."""
        try:
            theme_name = getattr(self.app, "theme", "gl-dark")
            theme_tokens = _BUILTIN_THEMES.get(theme_name, _BUILTIN_THEMES["gl-dark"])
            val = getattr(theme_tokens, var_name.replace("-", "_"), None)
            if val:
                return self._color_to_rich_style(val, is_bg)
        except Exception:
            pass
        return None

    def _color_to_rich_style(self, color: Any, is_bg: bool) -> str | None:
        """Convert any color-like object to a Rich-compatible style string."""
        if not color:
            return None

        # 1. Textual Color objects
        if hasattr(color, "hex") and color.hex.startswith("#"):
            return f"on {color.hex}" if is_bg else color.hex

        # 2. Rich Color objects (with triplets)
        if hasattr(color, "triplet") and color.triplet:
            hex_val = color.triplet.hex
            return f"on {hex_val}" if is_bg else hex_val

        # 3. Strings or named colors
        return self._str_color_to_style(color, is_bg)

    def _str_color_to_style(self, color: Any, is_bg: bool) -> str | None:
        """Helper to convert string-based colors to style."""
        if color is None:
            return None
        c_str = str(color).strip()
        if not c_str:
            return None

        if c_str.startswith("#"):
            return f"on {c_str}" if is_bg else c_str

        # If it's a named color like 'white', Rich understands it directly
        # but we skip Textual's 'color(N)' internal format.
        if not c_str.startswith("color(") and not c_str.startswith("auto"):
            return f"on {c_str}" if is_bg else c_str

        return None

    def _safe_update(self, renderable: Text) -> None:
        try:
            self.update(renderable)
            self._pending_render = None
        except NoActiveAppError:
            self._pending_render = renderable

    def _apply_pending_render(self) -> None:
        if self._pending_render is None:
            return
        try:
            self.update(self._pending_render)
            self._pending_render = None
        except NoActiveAppError:
            return

    def _cancel_timer(self) -> None:
        if self._timer is None:
            return
        try:
            self._timer.stop()
        except Exception:
            pass
        self._timer = None

    @staticmethod
    def _normalize_message(message: str | None) -> str:
        if message is None:
            return DEFAULT_MESSAGE
        cleaned = str(message).strip()
        return cleaned if cleaned else DEFAULT_MESSAGE

    @staticmethod
    def _coerce_width(width: int) -> int:
        if not isinstance(width, int):
            return DEFAULT_WIDTH
        return width if width > 0 else DEFAULT_WIDTH

    @staticmethod
    def _coerce_speed(speed_ms: int) -> int:
        if not isinstance(speed_ms, int):
            return DEFAULT_SPEED_MS
        return speed_ms if speed_ms > 0 else DEFAULT_SPEED_MS

    @staticmethod
    def _coerce_variant(variant: str) -> str:
        if not isinstance(variant, str):
            return "accent"
        normalized = variant.strip().lower()
        return normalized if normalized in VARIANT_STYLES else "accent"
