"""
Branding utilities for Cindergrace applications.

Provides common branding patterns:
- Logo loading from central location
- Theme CSS loading
- Configurable branding paths

Usage:
    from cgc_common import BaseConfig, BrandingMixin

    class Config(BaseConfig, BrandingMixin):
        APP_PREFIX = "SYSMON"

    # Get branding assets
    logo_path = Config.get_logo_path()
    css = Config.get_theme_css()

Environment Variables:
    CINDERGRACE_BRANDING_PATH - Override default branding assets location
"""

from pathlib import Path

from cgc_common.config import env_str


def get_default_branding_path() -> Path:
    """Get the default path to Cindergrace branding assets.

    Checks in order:
    1. CINDERGRACE_BRANDING_PATH environment variable
    2. ~/projekte/cindergrace_projects (development)
    3. /usr/share/cindergrace (system-wide installation)

    Returns:
        Path to branding directory
    """
    # Check environment variable first
    env_path = env_str("CINDERGRACE_BRANDING_PATH")
    if env_path:
        return Path(env_path)

    # Development path
    dev_path = Path.home() / "projekte" / "cindergrace_projects"
    if dev_path.exists():
        return dev_path

    # System path fallback
    return Path("/usr/share/cindergrace")


class BrandingMixin:
    """Mixin providing branding-related configuration patterns.

    Provides methods to load Cindergrace branding assets like
    logos and CSS themes from a central location.
    """

    # Default asset paths relative to branding root
    LOGO_SUBPATH: str = "logo/logo_v2_1024_transparent.png"
    LOGO_SMALL_SUBPATH: str = "logo/logo_v2_256_transparent.png"
    THEME_CSS_FILENAME: str = "gradio_theme.css"

    @classmethod
    def get_branding_path(cls) -> Path:
        """Get the path to branding assets directory.

        Returns:
            Path to branding directory
        """
        return get_default_branding_path()

    @classmethod
    def get_logo_path(cls, small: bool = False) -> Path:
        """Get path to Cindergrace logo.

        Args:
            small: If True, return path to smaller logo variant

        Returns:
            Path to logo file
        """
        subpath = cls.LOGO_SMALL_SUBPATH if small else cls.LOGO_SUBPATH
        return cls.get_branding_path() / subpath

    @classmethod
    def get_theme_css(cls) -> str:
        """Load Cindergrace Gradio theme CSS.

        Returns:
            CSS content as string, or empty string if not found
        """
        css_path = cls.get_branding_path() / cls.THEME_CSS_FILENAME
        if css_path.exists():
            return css_path.read_text(encoding="utf-8")
        return ""

    @classmethod
    def get_favicon_path(cls) -> Path | None:
        """Get path to favicon if available.

        Returns:
            Path to favicon or None if not found
        """
        favicon_path = cls.get_branding_path() / "favicon.ico"
        if favicon_path.exists():
            return favicon_path
        return None

    @classmethod
    def logo_exists(cls) -> bool:
        """Check if logo file exists.

        Returns:
            True if logo file exists
        """
        return cls.get_logo_path().exists()
