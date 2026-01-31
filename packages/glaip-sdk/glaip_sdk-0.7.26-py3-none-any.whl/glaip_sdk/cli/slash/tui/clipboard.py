"""Clipboard adapter for TUI copy actions."""

from __future__ import annotations

import base64
import os
import platform
import shutil
import subprocess
import sys
from dataclasses import dataclass
from enum import Enum
from typing import Any
from collections.abc import Callable

from glaip_sdk.cli.slash.tui.terminal import TerminalCapabilities, detect_osc52_support


class ClipboardMethod(str, Enum):
    """Supported clipboard backends."""

    OSC52 = "osc52"
    PBCOPY = "pbcopy"
    XCLIP = "xclip"
    XSEL = "xsel"
    WL_COPY = "wl-copy"
    CLIP = "clip"
    NONE = "none"


@dataclass(frozen=True, slots=True)
class ClipboardResult:
    """Result of a clipboard operation."""

    success: bool
    method: ClipboardMethod
    message: str


@dataclass(frozen=True, slots=True)
class ClipboardReadResult:
    """Result of a clipboard read operation."""

    success: bool
    method: ClipboardMethod
    message: str
    text: str


_SUBPROCESS_COMMANDS: dict[ClipboardMethod, list[str]] = {
    ClipboardMethod.PBCOPY: ["pbcopy"],
    ClipboardMethod.XCLIP: ["xclip", "-selection", "clipboard"],
    ClipboardMethod.XSEL: ["xsel", "--clipboard", "--input"],
    ClipboardMethod.WL_COPY: ["wl-copy"],
    ClipboardMethod.CLIP: ["clip"],
}
_SUBPROCESS_READ_COMMANDS: dict[ClipboardMethod, list[str]] = {
    ClipboardMethod.PBCOPY: ["pbpaste"],
    ClipboardMethod.XCLIP: ["xclip", "-selection", "clipboard", "-o"],
    ClipboardMethod.XSEL: ["xsel", "--clipboard", "--output"],
    ClipboardMethod.WL_COPY: ["wl-paste", "--no-newline"],
}

_ENV_CLIPBOARD_METHOD = "AIP_TUI_CLIPBOARD_METHOD"
_ENV_CLIPBOARD_FORCE = "AIP_TUI_CLIPBOARD_FORCE"
_ENV_METHOD_MAP = {
    "osc52": ClipboardMethod.OSC52,
    "pbcopy": ClipboardMethod.PBCOPY,
    "xclip": ClipboardMethod.XCLIP,
    "xsel": ClipboardMethod.XSEL,
    "wl-copy": ClipboardMethod.WL_COPY,
    "wl_copy": ClipboardMethod.WL_COPY,
    "clip": ClipboardMethod.CLIP,
    "none": ClipboardMethod.NONE,
}

_SUBPROCESS_TIMEOUT = 2.0


def _resolve_env_method() -> ClipboardMethod | None:
    raw = os.getenv(_ENV_CLIPBOARD_METHOD)
    if not raw:
        return None
    value = raw.strip().lower()
    if value in ("auto", "default"):
        return None
    return _ENV_METHOD_MAP.get(value)


def _is_env_force_enabled() -> bool:
    raw = os.getenv(_ENV_CLIPBOARD_FORCE)
    if not raw:
        return False
    return raw.strip().lower() in {"1", "true", "yes", "on"}


def _resolve_windows_read_command() -> list[str] | None:
    for shell in ("powershell", "pwsh"):
        if shutil.which(shell):
            return [shell, "-NoProfile", "-Command", "Get-Clipboard -Raw"]
    return None


class ClipboardAdapter:
    """Cross-platform clipboard access with OSC 52 fallback."""

    def __init__(
        self,
        *,
        terminal: TerminalCapabilities | None = None,
        method: ClipboardMethod | None = None,
    ) -> None:
        """Initialize the adapter."""
        self._terminal = terminal
        self._force_method = False
        self._fallback_methods_cache: list[ClipboardMethod] | None = None
        if method is not None:
            self._method = method
        else:
            env_method = _resolve_env_method()
            if env_method is not None:
                self._method = env_method
                self._force_method = _is_env_force_enabled()
            else:
                self._method = self._detect_method()

    @property
    def method(self) -> ClipboardMethod:
        """Return the detected clipboard backend."""
        return self._method

    def copy(self, text: str, *, writer: Callable[[str], Any] | None = None) -> ClipboardResult:
        """Copy text to clipboard using the best available method.

        Args:
            text: Text to copy.
            writer: Optional function to write OSC 52 sequence (e.g., self.app.console.write).
                   Defaults to sys.stdout.write if not provided.
        """
        if self._method == ClipboardMethod.OSC52:
            return self._copy_osc52(text, writer=writer)

        command = _SUBPROCESS_COMMANDS.get(self._method)
        if command is None:
            if self._force_method:
                return ClipboardResult(False, self._method, "Forced clipboard method unavailable.")
            return self._copy_osc52(text, writer=writer)

        result = self._copy_subprocess(command, text)
        if not result.success:
            if self._force_method or "timed out" in result.message:
                return result
            return self._copy_osc52(text, writer=writer)

        return result

    def read(self) -> ClipboardReadResult:
        """Read text from the clipboard using the best available method."""
        result = self._read_with_method(self._method)
        if result.success or self._force_method:
            return result

        if self._fallback_methods_cache is None:
            self._fallback_methods_cache = self._fallback_read_methods()

        for method in self._fallback_methods_cache:
            if method is self._method:
                continue
            fallback = self._read_with_method(method)
            if fallback.success:
                return fallback

        return result

    def _detect_method(self) -> ClipboardMethod:
        system = platform.system()
        method = ClipboardMethod.NONE
        if system == "Darwin":
            method = self._detect_darwin_method()
        elif system == "Linux":
            method = self._detect_linux_method()
        elif system == "Windows":
            method = self._detect_windows_method()

        if method is not ClipboardMethod.NONE:
            return method

        if self._terminal.osc52 if self._terminal else detect_osc52_support():
            return ClipboardMethod.OSC52

        return ClipboardMethod.NONE

    def _detect_darwin_method(self) -> ClipboardMethod:
        return ClipboardMethod.PBCOPY if shutil.which("pbcopy") else ClipboardMethod.NONE

    def _detect_linux_method(self) -> ClipboardMethod:
        if not os.getenv("DISPLAY") and not os.getenv("WAYLAND_DISPLAY"):
            return ClipboardMethod.NONE

        # Order of preference: Wayland then X11 tools
        for method in (ClipboardMethod.WL_COPY, ClipboardMethod.XCLIP, ClipboardMethod.XSEL):
            cmd = _SUBPROCESS_COMMANDS.get(method)
            if cmd and shutil.which(cmd[0]):
                return method
        return ClipboardMethod.NONE

    def _detect_windows_method(self) -> ClipboardMethod:
        return ClipboardMethod.CLIP if shutil.which("clip") else ClipboardMethod.NONE

    def _copy_osc52(self, text: str, *, writer: Callable[[str], Any] | None = None) -> ClipboardResult:
        encoded = base64.b64encode(text.encode("utf-8")).decode("ascii")
        sequence = f"\x1b]52;c;{encoded}\x07"
        try:
            if writer:
                writer(sequence)
            else:
                sys.stdout.write(sequence)
                sys.stdout.flush()
        except Exception as exc:
            return ClipboardResult(False, ClipboardMethod.OSC52, str(exc))

        return ClipboardResult(True, ClipboardMethod.OSC52, "Copied to clipboard")

    def _copy_subprocess(self, cmd: list[str], text: str) -> ClipboardResult:
        try:
            completed = subprocess.run(
                cmd,
                input=text.encode("utf-8"),
                check=False,
                timeout=_SUBPROCESS_TIMEOUT,
            )
        except subprocess.TimeoutExpired:
            return ClipboardResult(False, self._method, f"Clipboard command timed out after {_SUBPROCESS_TIMEOUT}s")
        except OSError as exc:
            return ClipboardResult(False, self._method, str(exc))

        if completed.returncode == 0:
            return ClipboardResult(True, self._method, "Copied to clipboard")

        return ClipboardResult(False, self._method, f"Command failed: {completed.returncode}")

    def _read_with_method(self, method: ClipboardMethod) -> ClipboardReadResult:
        if method is ClipboardMethod.OSC52:
            # OSC 52 read requires an asynchronous terminal response (DSR) which is
            # significantly more complex to implement than synchronous subprocess reads.
            # Currently out of scope.
            return ClipboardReadResult(False, method, "OSC 52 clipboard read is unsupported.", "")
        if method is ClipboardMethod.NONE:
            return ClipboardReadResult(False, method, "Clipboard backend unavailable.", "")

        if method is ClipboardMethod.CLIP:
            command = _resolve_windows_read_command()
            if command is None:
                return ClipboardReadResult(False, method, "PowerShell clipboard read unavailable.", "")
            return self._read_subprocess(command, method)

        command = _SUBPROCESS_READ_COMMANDS.get(method)
        if command is None:
            return ClipboardReadResult(False, method, "Clipboard read method unavailable.", "")

        return self._read_subprocess(command, method)

    def _read_subprocess(self, cmd: list[str], method: ClipboardMethod) -> ClipboardReadResult:
        try:
            completed = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                encoding="utf-8",
                check=False,
                timeout=_SUBPROCESS_TIMEOUT,
            )
        except subprocess.TimeoutExpired:
            return ClipboardReadResult(False, method, f"Clipboard command timed out after {_SUBPROCESS_TIMEOUT}s", "")
        except OSError as exc:
            return ClipboardReadResult(False, method, str(exc), "")

        if completed.returncode == 0:
            return ClipboardReadResult(True, method, "Read from clipboard", completed.stdout)

        return ClipboardReadResult(False, method, f"Command failed: {completed.returncode}", "")

    def _fallback_read_methods(self) -> list[ClipboardMethod]:
        system = platform.system()
        if system == "Darwin":
            return self._fallback_darwin()
        if system == "Linux":
            return self._fallback_linux()
        if system == "Windows":
            return self._fallback_windows()
        return []

    def _fallback_darwin(self) -> list[ClipboardMethod]:
        cmd = _SUBPROCESS_READ_COMMANDS.get(ClipboardMethod.PBCOPY)
        if cmd and shutil.which(cmd[0]):
            return [ClipboardMethod.PBCOPY]
        return []

    def _fallback_linux(self) -> list[ClipboardMethod]:
        methods: list[ClipboardMethod] = []
        for method in (ClipboardMethod.WL_COPY, ClipboardMethod.XCLIP, ClipboardMethod.XSEL):
            cmd = _SUBPROCESS_READ_COMMANDS.get(method)
            if not cmd:
                continue
            if method == ClipboardMethod.WL_COPY and not os.getenv("WAYLAND_DISPLAY"):
                continue
            if method in (ClipboardMethod.XCLIP, ClipboardMethod.XSEL) and not os.getenv("DISPLAY"):
                continue
            if shutil.which(cmd[0]):
                methods.append(method)
        return methods

    def _fallback_windows(self) -> list[ClipboardMethod]:
        if _resolve_windows_read_command():
            return [ClipboardMethod.CLIP]
        return []
