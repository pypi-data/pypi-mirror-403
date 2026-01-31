"""
CGC Common - Shared utilities for CGC Studio applications.

Provides common patterns for:
- Configuration management with environment variables
- Security settings (localhost binding, feature flags)
- Branding (logos, themes, CSS)
- Internationalization (i18n) utilities
- State persistence (JSON, XDG)
- CLI argument parsing
- Retry utilities
- Logging setup
- Gradio UI theming
- Path sanitization
- Git repository backups
"""

from .config import BaseConfig, env_bool, env_int, env_str
from .security import SecurityMixin
from .branding import BrandingMixin, get_default_branding_path
from .i18n import I18nManager, load_translations
from .state import JSONStore, XDGStateStore, merge_defaults
from .cli import ServerArgs, add_server_args, resolve_host
from .utils.retry import retry_on_failure
from .utils.paths import (
    PathTraversalError,
    is_safe_path,
    normalize_path,
    resolve_safe_path,
    safe_join,
    sanitize_filename,
)
from .utils.datetime import generate_id, utcnow
from .logging_setup import (
    ColoredFormatter,
    get_logger,
    set_level,
    setup_logging,
)
from .ui.gradio import (
    CSSVariables,
    GradioTheme,
    LOGO_SVG,
    build_header,
    default_css_variables,
)
from .secrets import (
    SecretStore,
    SecretStoreWarning,
    get_secret,
    set_secret,
)
from .backup import (
    BackupInfo,
    create_git_mirror_backup,
    delete_old_backups,
    get_latest_backup,
    list_backups,
    restore_from_backup,
)

# OpenRouter is optional (requires httpx)
try:
    from .openrouter import (
        OpenRouterClient,
        OpenRouterResponse,
        OPENROUTER_MODELS,
        DEFAULT_MODEL as OPENROUTER_DEFAULT_MODEL,
    )
    _OPENROUTER_AVAILABLE = True
except ImportError:
    OpenRouterClient = None  # type: ignore
    OpenRouterResponse = None  # type: ignore
    OPENROUTER_MODELS = {}
    OPENROUTER_DEFAULT_MODEL = ""
    _OPENROUTER_AVAILABLE = False

__version__ = "0.6.0"

__all__ = [
    # Config
    "BaseConfig",
    "env_bool",
    "env_int",
    "env_str",
    # Security
    "SecurityMixin",
    # Branding
    "BrandingMixin",
    "get_default_branding_path",
    # i18n
    "I18nManager",
    "load_translations",
    # State
    "JSONStore",
    "XDGStateStore",
    "merge_defaults",
    # CLI
    "ServerArgs",
    "add_server_args",
    "resolve_host",
    # Utils - Retry
    "retry_on_failure",
    # Utils - Paths
    "PathTraversalError",
    "is_safe_path",
    "normalize_path",
    "resolve_safe_path",
    "safe_join",
    "sanitize_filename",
    # Utils - DateTime
    "generate_id",
    "utcnow",
    # Logging
    "ColoredFormatter",
    "get_logger",
    "set_level",
    "setup_logging",
    # UI / Gradio
    "CSSVariables",
    "GradioTheme",
    "LOGO_SVG",
    "build_header",
    "default_css_variables",
    # Secrets
    "SecretStore",
    "SecretStoreWarning",
    "get_secret",
    "set_secret",
    # Backup
    "BackupInfo",
    "create_git_mirror_backup",
    "delete_old_backups",
    "get_latest_backup",
    "list_backups",
    "restore_from_backup",
    # OpenRouter
    "OpenRouterClient",
    "OpenRouterResponse",
    "OPENROUTER_MODELS",
    "OPENROUTER_DEFAULT_MODEL",
]
