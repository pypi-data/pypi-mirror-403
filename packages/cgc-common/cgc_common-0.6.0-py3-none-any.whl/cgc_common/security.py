"""
Security utilities for Cindergrace applications.

Provides common security patterns:
- Localhost-by-default server binding
- Feature flags for sensitive operations
- Configurable access control

Usage:
    from cgc_common import BaseConfig, SecurityMixin

    class Config(BaseConfig, SecurityMixin):
        APP_PREFIX = "SYSMON"

    # In your app:
    server_name = Config.get_server_bind()  # "127.0.0.1" or "0.0.0.0"

Environment Variables:
    {PREFIX}_ALLOW_REMOTE=1  - Allow remote access (binds to 0.0.0.0)
    {PREFIX}_ENABLE_{FEATURE}=1 - Enable specific features
"""

from cgc_common.config import env_bool


class SecurityMixin:
    """Mixin providing security-related configuration patterns.

    Requires APP_PREFIX to be defined in the class.

    Security Philosophy:
    - Secure by default (localhost only)
    - Explicit opt-in for remote access
    - Feature flags for dangerous operations
    """

    APP_PREFIX: str  # Must be defined by the class using this mixin

    # Default settings
    DEFAULT_ALLOW_REMOTE: bool = False
    LOCALHOST: str = "127.0.0.1"
    ALL_INTERFACES: str = "0.0.0.0"  # nosec B104 - intentional, requires explicit ALLOW_REMOTE=1

    @classmethod
    def _security_key(cls, key: str) -> str:
        """Get full environment variable name for security setting."""
        return f"{cls.APP_PREFIX}_{key}"

    @classmethod
    def allow_remote(cls) -> bool:
        """Check if remote access is allowed.

        Returns:
            True if {PREFIX}_ALLOW_REMOTE=1, False otherwise
        """
        return env_bool(cls._security_key("ALLOW_REMOTE"), cls.DEFAULT_ALLOW_REMOTE)

    @classmethod
    def get_server_bind(cls) -> str:
        """Get the server bind address based on security settings.

        Returns:
            "0.0.0.0" if remote access allowed, "127.0.0.1" otherwise
        """
        return cls.ALL_INTERFACES if cls.allow_remote() else cls.LOCALHOST

    @classmethod
    def is_feature_enabled(cls, feature: str) -> bool:
        """Check if a specific feature is enabled.

        Features are disabled by default and must be explicitly enabled
        via environment variable {PREFIX}_ENABLE_{FEATURE}=1.

        Args:
            feature: Feature name (e.g., "KILL", "PACKAGES")

        Returns:
            True if feature is enabled, False otherwise

        Example:
            # Check if kill feature is enabled
            if Config.is_feature_enabled("KILL"):
                show_kill_button()
        """
        key = cls._security_key(f"ENABLE_{feature.upper()}")
        return env_bool(key, False)

    @classmethod
    def get_security_docs(cls) -> dict[str, str]:
        """Get documentation for security environment variables.

        Returns:
            Dict mapping env var names to descriptions
        """
        prefix = cls.APP_PREFIX
        return {
            f"{prefix}_ALLOW_REMOTE": "Set to 1 to allow remote access (binds to 0.0.0.0)",
            f"{prefix}_ENABLE_*": "Set to 1 to enable specific features (e.g., ENABLE_KILL)",
        }
