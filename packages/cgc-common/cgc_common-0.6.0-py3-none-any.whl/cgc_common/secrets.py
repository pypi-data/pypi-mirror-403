"""Secure secret storage with OS keyring and environment variable fallback.

Provides a unified interface for storing and retrieving sensitive data like
API keys, tokens, and credentials using the most secure available method.

Priority order:
1. OS Keyring (Windows Credential Manager, macOS Keychain, Linux Secret Service)
2. Environment variables (with warning)
3. None (secret not found)
"""

import logging
import os
import warnings

# Try to import keyring, but don't fail if not available
try:
    import keyring
    from keyring.errors import KeyringError, NoKeyringError

    KEYRING_AVAILABLE = True
except ImportError:
    KEYRING_AVAILABLE = False
    KeyringError = Exception  # type: ignore
    NoKeyringError = Exception  # type: ignore

logger = logging.getLogger(__name__)


class SecretStoreWarning(UserWarning):
    """Warning for insecure secret storage fallback."""

    pass


class SecretStore:
    """Secure storage for API keys and sensitive credentials.

    Uses OS keyring when available, falls back to environment variables.
    Provides a consistent interface regardless of backend.

    Usage:
        secrets = SecretStore("myapp")

        # Store a secret (tries keyring first)
        secrets.set("API_TOKEN", "secret123")

        # Retrieve a secret
        token = secrets.get("API_TOKEN")

        # Delete a secret
        secrets.delete("API_TOKEN")

        # Check if using secure storage
        if secrets.is_keyring_available():
            print("Using OS keyring")
        else:
            print("Falling back to env vars")

    Environment Variable Format:
        When keyring is unavailable, secrets are read from environment
        variables named: {SERVICE_NAME}__{KEY}
        Example: MYAPP__API_TOKEN

    Attributes:
        service_name: Application identifier used as keyring service name
        env_prefix: Prefix for environment variable fallback
    """

    def __init__(
        self,
        service_name: str,
        env_prefix: str | None = None,
        warn_on_fallback: bool = True,
    ):
        """Initialize SecretStore.

        Args:
            service_name: Unique identifier for the application (used as keyring service)
            env_prefix: Prefix for env var fallback (default: service_name.upper())
            warn_on_fallback: Emit warning when falling back to env vars
        """
        self.service_name = service_name
        self.env_prefix = (env_prefix or service_name).upper().replace("-", "_")
        self._warn_on_fallback = warn_on_fallback
        self._keyring_tested = False
        self._keyring_works = False

    def _test_keyring(self) -> bool:
        """Test if keyring is actually functional (not just importable)."""
        if self._keyring_tested:
            return self._keyring_works

        self._keyring_tested = True

        if not KEYRING_AVAILABLE:
            self._keyring_works = False
            return False

        try:
            # Try a test operation to see if keyring backend works
            test_key = f"__cindergrace_test_{os.getpid()}__"
            keyring.set_password(self.service_name, test_key, "test")
            keyring.delete_password(self.service_name, test_key)
            self._keyring_works = True
        except (KeyringError, NoKeyringError, RuntimeError) as e:
            logger.debug(f"Keyring not functional: {e}")
            self._keyring_works = False
        except Exception as e:
            # Catch any unexpected errors from keyring backends
            logger.debug(f"Keyring test failed: {e}")
            self._keyring_works = False

        return self._keyring_works

    def is_keyring_available(self) -> bool:
        """Check if OS keyring is available and functional.

        Returns:
            True if keyring can be used, False if falling back to env vars
        """
        return self._test_keyring()

    def _env_var_name(self, key: str) -> str:
        """Generate environment variable name for a key."""
        safe_key = key.upper().replace("-", "_").replace(" ", "_")
        return f"{self.env_prefix}__{safe_key}"

    def _warn_fallback(self, key: str, operation: str) -> None:
        """Emit warning about using env var fallback."""
        if self._warn_on_fallback:
            env_var = self._env_var_name(key)
            warnings.warn(
                f"Keyring unavailable, {operation} '{key}' via environment variable {env_var}. "
                f"Install 'keyring' package for secure storage.",
                SecretStoreWarning,
                stacklevel=4,
            )

    def get(self, key: str, default: str | None = None) -> str | None:
        """Retrieve a secret.

        Tries keyring first, falls back to environment variable.

        Args:
            key: Secret identifier
            default: Value to return if secret not found

        Returns:
            The secret value, or default if not found
        """
        # Try keyring first
        if self._test_keyring():
            try:
                value = keyring.get_password(self.service_name, key)
                if value is not None:
                    return value
            except (KeyringError, NoKeyringError):
                pass

        # Fall back to environment variable
        env_var = self._env_var_name(key)
        value = os.environ.get(env_var)

        if value is not None:
            if not self._keyring_works:
                self._warn_fallback(key, "reading")
            return value

        return default

    def set(self, key: str, value: str) -> bool:
        """Store a secret.

        Tries keyring first, falls back to setting environment variable
        for current process only (not persistent without keyring).

        Args:
            key: Secret identifier
            value: Secret value to store

        Returns:
            True if stored in keyring (persistent), False if only in env var
        """
        # Try keyring first
        if self._test_keyring():
            try:
                keyring.set_password(self.service_name, key, value)
                logger.debug(f"Stored '{key}' in OS keyring")
                return True
            except (KeyringError, NoKeyringError) as e:
                logger.warning(f"Failed to store in keyring: {e}")

        # Fall back to environment variable (current process only)
        env_var = self._env_var_name(key)
        os.environ[env_var] = value
        self._warn_fallback(key, "storing")
        logger.debug(f"Stored '{key}' in environment variable {env_var}")
        return False

    def delete(self, key: str) -> bool:
        """Delete a secret.

        Removes from both keyring and environment variable.

        Args:
            key: Secret identifier

        Returns:
            True if secret was found and deleted, False if not found
        """
        deleted = False

        # Try keyring
        if self._test_keyring():
            try:
                keyring.delete_password(self.service_name, key)
                deleted = True
                logger.debug(f"Deleted '{key}' from OS keyring")
            except (KeyringError, NoKeyringError):
                pass

        # Also remove from environment
        env_var = self._env_var_name(key)
        if env_var in os.environ:
            del os.environ[env_var]
            deleted = True
            logger.debug(f"Deleted '{key}' from environment")

        return deleted

    def exists(self, key: str) -> bool:
        """Check if a secret exists.

        Args:
            key: Secret identifier

        Returns:
            True if secret exists in keyring or environment
        """
        return self.get(key) is not None

    def get_storage_info(self) -> dict[str, str | bool]:
        """Get information about current storage backend.

        Returns:
            Dict with storage backend details
        """
        info: dict[str, str | bool] = {
            "keyring_available": KEYRING_AVAILABLE,
            "keyring_functional": self._test_keyring(),
            "service_name": self.service_name,
            "env_prefix": self.env_prefix,
        }

        if KEYRING_AVAILABLE and self._keyring_works:
            try:
                info["keyring_backend"] = keyring.get_keyring().__class__.__name__
            except Exception:
                info["keyring_backend"] = "unknown"
        else:
            info["keyring_backend"] = "none (using env vars)"

        return info


def get_secret(
    service: str,
    key: str,
    default: str | None = None,
) -> str | None:
    """Convenience function to get a secret.

    Args:
        service: Application/service name
        key: Secret identifier
        default: Default value if not found

    Returns:
        Secret value or default
    """
    store = SecretStore(service, warn_on_fallback=False)
    return store.get(key, default)


def set_secret(service: str, key: str, value: str) -> bool:
    """Convenience function to set a secret.

    Args:
        service: Application/service name
        key: Secret identifier
        value: Secret value

    Returns:
        True if stored in keyring, False if env var fallback
    """
    store = SecretStore(service, warn_on_fallback=False)
    return store.set(key, value)
