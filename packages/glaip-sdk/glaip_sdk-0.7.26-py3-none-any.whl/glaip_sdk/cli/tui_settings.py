"""Typed loader/saver for TUI preferences stored in config.yaml.

This module implements the TUI preferences store as defined in
`specs/architecture/tui-preferences-store/spec.md`.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Literal, cast

from glaip_sdk.cli.account_store import AccountStore, get_account_store

ThemeModeValue = Literal["auto", "light", "dark"]

_DEFAULT_THEME_MODE: ThemeModeValue = "auto"
_DEFAULT_LEADER = "ctrl+x"
_DEFAULT_MOUSE_CAPTURE = False


@dataclass(frozen=True)
class TUISettings:
    """Resolved TUI preferences from config.yaml."""

    theme_mode: ThemeModeValue = _DEFAULT_THEME_MODE
    theme_name: str | None = None
    leader: str = _DEFAULT_LEADER
    keybind_overrides: dict[str, str] = field(default_factory=dict)
    mouse_capture: bool = _DEFAULT_MOUSE_CAPTURE


def load_tui_settings(*, store: AccountStore | None = None) -> TUISettings:
    """Load TUI preferences from the CLI config file."""
    store = store or get_account_store()
    config = store.load_config()

    tui = _as_dict(config.get("tui"))
    theme = _as_dict(tui.get("theme"))
    mode = _coerce_theme_mode(theme.get("mode"))
    name = _normalize_theme_name(theme.get("name"))

    keybinds = _as_dict(tui.get("keybinds"))
    leader = keybinds.get("leader")
    if not isinstance(leader, str) or not leader.strip():
        leader = _DEFAULT_LEADER

    overrides = _coerce_keybind_overrides(keybinds.get("overrides"))

    mouse_capture = tui.get("mouse_capture")
    if not isinstance(mouse_capture, bool):
        mouse_capture = _DEFAULT_MOUSE_CAPTURE

    return TUISettings(
        theme_mode=mode,
        theme_name=name,
        leader=leader,
        keybind_overrides=overrides,
        mouse_capture=mouse_capture,
    )


def update_tui_settings(patch: dict[str, Any], *, store: AccountStore | None = None) -> None:
    """Update TUI preferences, preserving unrelated config keys."""
    store = store or get_account_store()
    config = store.load_config()

    existing = _as_dict(config.get("tui"))
    config["tui"] = _merge_dict(existing, patch)

    store.save_config_updates(config)


def persist_tui_theme(*, mode: ThemeModeValue, name: str | None, store: AccountStore | None = None) -> None:
    """Persist theme preferences in the tui.theme namespace."""
    update_tui_settings(
        {"theme": {"mode": _coerce_theme_mode(mode), "name": _serialize_theme_name(name)}},
        store=store,
    )


def _as_dict(value: Any) -> dict[str, Any]:
    if isinstance(value, dict):
        return dict(value)
    return {}


def _coerce_theme_mode(value: Any) -> ThemeModeValue:
    if isinstance(value, str):
        lowered = value.strip().lower()
        if lowered in {"auto", "light", "dark"}:
            return cast(ThemeModeValue, lowered)
    return _DEFAULT_THEME_MODE


def _normalize_theme_name(value: Any) -> str | None:
    if not isinstance(value, str):
        return None
    cleaned = value.strip()
    if not cleaned or cleaned.lower() == "default":
        return None
    return cleaned


def _serialize_theme_name(name: str | None) -> str:
    if isinstance(name, str):
        cleaned = name.strip()
        if cleaned:
            return cleaned
    return "default"


def _coerce_keybind_overrides(value: Any) -> dict[str, str]:
    if not isinstance(value, dict):
        return {}
    return {key: val for key, val in value.items() if isinstance(key, str) and isinstance(val, str)}


def _merge_dict(base: dict[str, Any], patch: dict[str, Any]) -> dict[str, Any]:
    merged = dict(base)
    for key, value in patch.items():
        if isinstance(value, dict) and isinstance(merged.get(key), dict):
            merged[key] = _merge_dict(cast(dict[str, Any], merged[key]), value)
        else:
            merged[key] = value
    return merged
