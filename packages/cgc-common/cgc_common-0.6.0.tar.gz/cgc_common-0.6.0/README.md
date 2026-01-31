# Cindergrace Common

**Status:** Final


> **Internal Use Only** - This repository is public solely for integration with free-tier code analysis tools (Codacy). It is not intended for external use, contribution, or distribution. No support is provided.

Shared utilities for Cindergrace applications.

## Installation

```bash
pip install cindergrace-common
```

With optional dependencies:
```bash
pip install cindergrace-common[gradio]   # Gradio theme support
pip install cindergrace-common[secrets]  # OS Keyring support
pip install cindergrace-common[dev]      # Development tools
```

## Features

- **Configuration**: Type-safe environment variable helpers
- **Security**: Localhost-by-default server binding, feature flags
- **Branding**: Centralized logo and CSS loading
- **i18n**: YAML-based translations
- **State**: XDG-compliant JSON persistence
- **Logging**: Unified logging setup with colored output
- **Paths**: Path traversal protection utilities
- **Secrets**: OS Keyring integration for API keys (v0.3.0)
- **Gradio**: Consistent theming for Gradio apps

## Quick Start

```python
from cindergrace_common import (
    BaseConfig, SecurityMixin, BrandingMixin,
    env_int, env_bool, setup_logging
)

logger = setup_logging("myapp")

class Config(BaseConfig, SecurityMixin, BrandingMixin):
    APP_PREFIX = "MYAPP"
    PORT = env_int("MYAPP_PORT", 7865)

# Server binds to localhost by default
# Set MYAPP_ALLOW_REMOTE=1 for network access
server_name = Config.get_server_bind()
```

### Secure API Key Storage (v0.3.0)

```python
from cindergrace_common import SecretStore

secrets = SecretStore("myapp")
secrets.set("API_TOKEN", "secret123")  # Stores in OS Keyring
token = secrets.get("API_TOKEN")       # Retrieves from Keyring
```

## Environment Variables

| Variable | Description |
|----------|-------------|
| `{PREFIX}_PORT` | Server port |
| `{PREFIX}_ALLOW_REMOTE` | Set to `1` for network access |
| `{PREFIX}_ENABLE_{FEATURE}` | Enable specific features |
| `CINDERGRACE_BRANDING_PATH` | Path to branding assets |
| `{SERVICE}__{KEY}` | Fallback for secrets when keyring unavailable |

## License

MIT


