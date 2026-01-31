"""AIP SDK Branding and Visual Identity.

Simple, friendly CLI branding for the GL AIP (GDP Labs AI Agent Package) SDK.

- Package name: GL AIP (GDP Labs AI Agent Package)
- Version: auto-detected (AIP_VERSION env or importlib.metadata), or passed in
- Colors: GDP Labs brand palette with NO_COLOR/AIP_NO_COLOR fallbacks

Author:
    Raymond Christopher (raymond.christopher@gdplabs.id)
"""

from __future__ import annotations

import os
import platform
import sys

from rich.console import Console
from rich.text import Text

from glaip_sdk._version import __version__ as SDK_VERSION
from glaip_sdk.rich_components import AIPPanel

try:
    # Python 3.8+ standard way to read installed package version
    from importlib.metadata import PackageNotFoundError
    from importlib.metadata import version as pkg_version
except Exception:  # pragma: no cover
    pkg_version = None
    PackageNotFoundError = Exception


# ---- GDP Labs Brand Color Palette -----------------------------------------
PRIMARY = "#004987"  # Primary brand blue (dark blue)
SECONDARY_DARK = "#003A5C"  # Darkest variant for emphasis
SECONDARY_MEDIUM = "#005CB8"  # Medium variant for UI elements
SECONDARY_LIGHT = "#40B4E5"  # Light variant for highlights

# Neutral companion palette (optimized for dark terminals)
SUCCESS = "#7FA089"  # Muted teal-green for success messaging
WARNING = "#C3A46F"  # Soft amber for warnings
ERROR = "#C97B6C"  # Tempered coral-red for errors
INFO = "#9CA3AF"  # Cool grey for informational accents
NEUTRAL = "#D1D5DB"  # Light grey for muted text and dividers

BORDER = PRIMARY  # Keep borders aligned with primary brand tone
TITLE_STYLE = f"bold {PRIMARY}"
LABEL = "bold"
SUCCESS_STYLE = f"bold {SUCCESS}"
WARNING_STYLE = f"bold {WARNING}"
ERROR_STYLE = f"bold {ERROR}"
INFO_STYLE = f"bold {INFO}"
ACCENT_STYLE = INFO  # For subdued inline highlights

# Hint styling (slash command helpers, tips, quick actions)
HINT_TITLE_STYLE = f"bold {SECONDARY_LIGHT}"
HINT_COMMAND_STYLE = f"bold {SECONDARY_LIGHT}"
HINT_DESCRIPTION_COLOR = NEUTRAL
HINT_PREFIX_STYLE = INFO_STYLE


class AIPBranding:
    """GL AIP branding utilities with ASCII banner and version display."""

    # GL AIP ASCII art - Modern block style with enhanced visibility
    AIP_LOGO = r"""
 ██████╗ ██╗         █████╗ ██╗██████╗
██╔════╝ ██║        ██╔══██╗██║██╔══██╗
██║  ███╗██║        ███████║██║██████╔╝
██║   ██║██║        ██╔══██║██║██╔═══╝
╚██████╔╝███████╗   ██║  ██║██║██║
 ╚═════╝ ╚══════╝   ╚═╝  ╚═╝╚═╝╚═╝
GDP Labs AI Agents Package
""".strip("\n")

    def __init__(
        self,
        version: str | None = None,
        package_name: str | None = None,
    ) -> None:
        """Initialize AIPBranding instance.

        Args:
            version: Explicit SDK version (overrides auto-detection).
            package_name: If set, attempt to read version from installed package.
        """
        self.version = version or self._auto_version(package_name)
        self.console = self._make_console()

    # ---- small helpers --------------------------------------------------------
    @staticmethod
    def _auto_version(package_name: str | None) -> str:
        """Auto-detect version from environment, package metadata, or fallback.

        Args:
            package_name: Optional package name to read version from installed metadata.

        Returns:
            Version string from AIP_VERSION env var, package metadata, or SDK_VERSION fallback.
        """
        # Priority: env → package metadata → fallback
        env_version = os.getenv("AIP_VERSION")
        if env_version:
            return env_version
        if package_name and pkg_version:
            try:
                return pkg_version(package_name)
            except PackageNotFoundError:
                pass
        return SDK_VERSION

    @staticmethod
    def _make_console(force_terminal: bool | None = None, *, soft_wrap: bool = True) -> Console:
        """Create a Rich Console instance respecting NO_COLOR environment variables.

        Args:
            force_terminal: Override terminal detection when True/False.
            soft_wrap: Whether to enable soft wrapping in the console.

        Returns:
            Console instance with color system configured based on environment.
        """
        # Respect NO_COLOR/AIP_NO_COLOR environment variables
        no_color_env = os.getenv("NO_COLOR") is not None or os.getenv("AIP_NO_COLOR") is not None
        if no_color_env:
            color_system = None
            no_color = True
        else:
            color_system = "auto"
            no_color = False
        return Console(
            color_system=color_system,
            no_color=no_color,
            soft_wrap=soft_wrap,
            force_terminal=force_terminal,
        )

    # ---- public API -----------------------------------------------------------
    def get_welcome_banner(self) -> str:
        """Get AIP banner with version info."""
        banner = f"[{PRIMARY}]{self.AIP_LOGO}[/{PRIMARY}]"
        line = f"Version: {self.version}"
        banner = f"{banner}\n{line}"
        return banner

    def get_version_info(self) -> dict:
        """Get comprehensive version information for the SDK.

        Returns:
            Dictionary containing version, Python version, platform, and architecture info
        """
        return {
            "version": self.version,
            "python_version": f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}",
            "platform": platform.platform(),
            "architecture": platform.architecture()[0],
        }

    def display_welcome_panel(
        self,
        title: str = "Welcome to AIP",
        *,
        console: Console | None = None,
    ) -> None:
        """Display a welcome panel with branding.

        Args:
            title: Custom title for the welcome panel
            console: Optional console instance to print to. If None, uses self.console
        """
        banner = self.get_welcome_banner()
        panel = AIPPanel(
            banner,
            title=f"[{TITLE_STYLE}]{title}[/{TITLE_STYLE}]",
            border_style=BORDER,
            padding=(1, 2),
        )
        target_console = console or self.console
        target_console.print(panel)

    def display_version_panel(self) -> None:
        """Display a panel with comprehensive version information."""
        v = self.get_version_info()
        version_text = (
            f"[{TITLE_STYLE}]AIP SDK Version Information[/{TITLE_STYLE}]\n\n"
            f"[{LABEL}]Version:[/] {v['version']}\n"
            f"[{LABEL}]Python:[/] {v['python_version']}\n"
            f"[{LABEL}]Platform:[/] {v['platform']}\n"
            f"[{LABEL}]Architecture:[/] {v['architecture']}"
        )
        panel = AIPPanel(
            version_text,
            title=f"[{TITLE_STYLE}]Version Details[/{TITLE_STYLE}]",
            border_style=BORDER,
            padding=(1, 2),
        )
        self.console.print(panel)

    def display_status_banner(self, status: str = "ready") -> None:
        """Display a status banner for the current state.

        Args:
            status: Current status to display
        """
        # Keep it simple (no emoji); easy to parse in logs/CI
        banner = f"[{LABEL}]AIP[/{LABEL}] - {status.title()}"
        self.console.print(banner)

    @classmethod
    def create_from_sdk(cls, sdk_version: str | None = None, package_name: str | None = None) -> AIPBranding:
        """Create AIPBranding instance from SDK package information.

        Args:
            sdk_version: Explicit SDK version override
            package_name: Package name to read version from

        Returns:
            AIPBranding instance
        """
        return cls(version=sdk_version, package_name=package_name)


class LogoAnimator:
    """Animated logo with pulse effect for CLI startup.

    Provides a "Knight Rider" style light pulse animation that sweeps across
    the GL AIP logo during initialization tasks. Respects NO_COLOR and non-TTY
    environments with graceful degradation.
    """

    # Animation colors from GDP Labs brand palette
    BASE_BLUE = SECONDARY_MEDIUM  # "#005CB8" - Medium Blue
    HIGHLIGHT = SECONDARY_LIGHT  # "#40B4E5" - Light Blue
    WHITE = "#FFFFFF"  # Bright white center

    def __init__(self, console: Console | None = None) -> None:
        """Initialize LogoAnimator.

        Args:
            console: Optional console instance. If None, creates a default console.
        """
        self.console = console or AIPBranding._make_console()
        self.logo = AIPBranding.AIP_LOGO
        self.lines = self.logo.split("\n")
        self.max_width = max(len(line) for line in self.lines) if self.lines else 0

    def generate_frame(self, step: int, status_text: str = "") -> Text:
        """Generate a single animation frame with logo pulse and status.

        Args:
            step: Current animation step (position of the pulse).
            status_text: Optional status text to display below the logo.

        Returns:
            Text object with styled logo and status.
        """
        text = Text()

        for line in self.lines:
            for x, char in enumerate(line):
                distance = abs(x - step)

                if distance == 0:
                    style = f"bold {self.WHITE}"  # Bright white center
                elif distance <= 3:
                    style = f"bold {self.HIGHLIGHT}"  # Light blue glow
                else:
                    style = self.BASE_BLUE  # Base blue

                text.append(char, style=style)
            text.append("\n")

        # Add status area below the logo
        if status_text:
            text.append(f"\n{status_text}\n")

        return text

    def should_animate(self) -> bool:
        """Check if animation should be used.

        Returns:
            True if animation should be used (interactive TTY with colors),
            False otherwise (NO_COLOR set or non-TTY).
        """
        # Check for NO_COLOR environment variables
        no_color = os.getenv("NO_COLOR") is not None or os.getenv("AIP_NO_COLOR") is not None
        if no_color:
            return False

        # Check if console is a TTY
        if not self.console.is_terminal:
            return False

        # Check if console explicitly disables colors
        if self.console.no_color:
            return False

        # If we get here, we have a TTY without NO_COLOR set
        # Rich will handle color detection, so we can animate
        return True

    def display_static_logo(self, status_text: str = "") -> None:
        """Display static logo without animation (for non-TTY or NO_COLOR).

        Args:
            status_text: Optional status text to display below the logo.
        """
        self.console.print(self.static_frame(status_text))

    def static_frame(self, status_text: str = "") -> Text:
        """Return a static logo frame for use in non-animated renders.

        Args:
            status_text: Optional status text to display below the logo.
        """
        logo_text = Text(self.logo, style=self.BASE_BLUE)
        if status_text:
            logo_text.append("\n")
            logo_text.append(status_text)
        return logo_text
