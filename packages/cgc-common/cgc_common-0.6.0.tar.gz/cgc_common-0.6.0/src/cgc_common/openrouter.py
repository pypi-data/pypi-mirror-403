"""OpenRouter API Client.

Reusable client for AI generation via OpenRouter.
Stores API key securely via SecretStore (keyring).

Usage:
    from cgc_common import OpenRouterClient

    # With explicit credentials
    client = OpenRouterClient(api_key="sk-...", model="meta-llama/llama-3-8b")

    # Or using SecretStore (recommended)
    client = OpenRouterClient.from_secrets("myapp")
    # Reads from keyring: myapp/openrouter_api_key, myapp/openrouter_model

    # Generate completion
    response = client.complete("Explain this code...")
    if response.success:
        print(response.content)

    # Extract JSON
    data = client.extract_json("Return as JSON: {name, age}")
"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass
from typing import TYPE_CHECKING

try:
    import httpx
except ImportError:
    httpx = None  # type: ignore

if TYPE_CHECKING:
    from cgc_common.secrets import SecretStore

logger = logging.getLogger(__name__)

OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"

# Common models for reference
OPENROUTER_MODELS = {
    "llama-3.3-70b": "meta-llama/llama-3.3-70b-instruct",
    "llama-3.1-8b": "meta-llama/llama-3.1-8b-instruct",
    "gemma-2-9b": "google/gemma-2-9b-it",
    "qwen-2.5-72b": "qwen/qwen-2.5-72b-instruct",
    "mistral-7b": "mistralai/mistral-7b-instruct",
    "claude-3-haiku": "anthropic/claude-3-haiku",
    "gpt-4o-mini": "openai/gpt-4o-mini",
}

DEFAULT_MODEL = "meta-llama/llama-3.1-8b-instruct"


@dataclass
class OpenRouterResponse:
    """Response from OpenRouter API."""

    success: bool
    content: str
    error: str | None = None
    model: str | None = None
    usage: dict | None = None


class OpenRouterClient:
    """Client for OpenRouter API calls.

    Can be initialized with explicit credentials or loaded from SecretStore.

    Args:
        api_key: OpenRouter API key (starts with sk-or-)
        model: Model identifier (e.g., "meta-llama/llama-3.1-8b-instruct")
        app_name: Optional app name for SecretStore fallback
    """

    # SecretStore keys
    KEY_API_KEY = "openrouter_api_key"
    KEY_MODEL = "openrouter_model"

    def __init__(
        self,
        api_key: str | None = None,
        model: str | None = None,
        app_name: str | None = None,
    ):
        self._api_key = api_key
        self._model = model or DEFAULT_MODEL
        self._app_name = app_name
        self._secrets: SecretStore | None = None

    @classmethod
    def from_secrets(cls, app_name: str) -> "OpenRouterClient":
        """Create client using credentials from SecretStore.

        Args:
            app_name: Application name for SecretStore (e.g., "cindergrace_devhub")

        Returns:
            OpenRouterClient configured with stored credentials
        """
        from cgc_common.secrets import SecretStore

        secrets = SecretStore(app_name)
        api_key = secrets.get(cls.KEY_API_KEY)
        model = secrets.get(cls.KEY_MODEL) or DEFAULT_MODEL

        client = cls(api_key=api_key, model=model, app_name=app_name)
        client._secrets = secrets
        return client

    @property
    def api_key(self) -> str | None:
        """Get API key (from init or SecretStore)."""
        if self._api_key:
            return self._api_key
        if self._secrets:
            return self._secrets.get(self.KEY_API_KEY)
        return None

    @property
    def model(self) -> str:
        """Get model (from init or SecretStore)."""
        if self._model:
            return self._model
        if self._secrets:
            return self._secrets.get(self.KEY_MODEL) or DEFAULT_MODEL
        return DEFAULT_MODEL

    def set_api_key(self, api_key: str) -> None:
        """Set API key (and save to SecretStore if available)."""
        self._api_key = api_key
        if self._secrets:
            self._secrets.set(self.KEY_API_KEY, api_key)

    def set_model(self, model: str) -> None:
        """Set model (and save to SecretStore if available)."""
        self._model = model
        if self._secrets:
            self._secrets.set(self.KEY_MODEL, model)

    def is_configured(self) -> bool:
        """Check if OpenRouter is configured with valid credentials."""
        return bool(self.api_key and self.model)

    def complete(
        self,
        prompt: str,
        system_prompt: str | None = None,
        max_tokens: int = 500,
        temperature: float = 0.7,
        timeout: float = 30.0,
    ) -> OpenRouterResponse:
        """Generate completion using OpenRouter API.

        Args:
            prompt: The user prompt to send
            system_prompt: Optional system prompt for context
            max_tokens: Maximum tokens in response
            temperature: Sampling temperature (0.0-2.0)
            timeout: Request timeout in seconds

        Returns:
            OpenRouterResponse with success status and content/error
        """
        api_key = self.api_key
        model = self.model

        if not api_key:
            return OpenRouterResponse(
                success=False,
                content="",
                error="No API key configured",
            )

        # Build messages
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        if httpx is None:
            return OpenRouterResponse(
                success=False,
                content="",
                error="httpx not installed. Run: pip install httpx",
            )

        try:
            with httpx.Client(
                base_url=OPENROUTER_BASE_URL,
                headers={
                    "Authorization": f"Bearer {api_key.strip()}",
                    "Content-Type": "application/json",
                    "HTTP-Referer": "https://cindergrace.studio",
                    "X-Title": self._app_name or "Cindergrace App",
                },
                timeout=timeout,
            ) as client:
                response = client.post(
                    "/chat/completions",
                    json={
                        "model": model,
                        "messages": messages,
                        "max_tokens": max_tokens,
                        "temperature": temperature,
                    },
                )

                if response.status_code == 200:
                    data = response.json()
                    content = data["choices"][0]["message"]["content"].strip()
                    usage = data.get("usage")
                    return OpenRouterResponse(
                        success=True,
                        content=content,
                        model=model,
                        usage=usage,
                    )
                elif response.status_code == 401:
                    return OpenRouterResponse(
                        success=False,
                        content="",
                        error="API key invalid",
                    )
                elif response.status_code == 404:
                    return OpenRouterResponse(
                        success=False,
                        content="",
                        error=f"Model not found: {model}",
                    )
                elif response.status_code == 429:
                    return OpenRouterResponse(
                        success=False,
                        content="",
                        error="Rate limit exceeded",
                    )
                else:
                    error_text = response.text[:200] if response.text else "Unknown"
                    return OpenRouterResponse(
                        success=False,
                        content="",
                        error=f"API error {response.status_code}: {error_text}",
                    )

        except Exception as e:
            logger.warning(f"OpenRouter error: {e}")
            return OpenRouterResponse(
                success=False,
                content="",
                error=f"Connection error: {e}",
            )

    def check_connection(self) -> str:
        """Test OpenRouter connection with a minimal request.

        Returns:
            Status message with emoji indicator
        """
        if not self.api_key:
            return "⚠️ No API key configured"

        result = self.complete("Hi", max_tokens=5, timeout=15.0)

        if result.success:
            return f"✅ Connected to {self.model}"
        else:
            return f"❌ {result.error}"

    def extract_json(
        self,
        prompt: str,
        system_prompt: str | None = None,
        max_tokens: int = 500,
    ) -> dict | None:
        """Generate a completion and parse it as JSON.

        Handles markdown code blocks in response.

        Args:
            prompt: The prompt (should request JSON output)
            system_prompt: Optional system prompt
            max_tokens: Maximum tokens in response

        Returns:
            Parsed dict or None on error
        """
        # Add JSON hint to system prompt
        json_system = "Always respond with valid JSON only. No explanations."
        if system_prompt:
            json_system = f"{system_prompt}\n\n{json_system}"

        result = self.complete(
            prompt,
            system_prompt=json_system,
            max_tokens=max_tokens,
            temperature=0.3,  # Lower temperature for structured output
        )

        if not result.success:
            logger.warning(f"OpenRouter JSON request failed: {result.error}")
            return None

        content = result.content

        # Handle markdown code blocks
        if "```" in content:
            parts = content.split("```")
            if len(parts) >= 2:
                content = parts[1]
                # Remove language identifier
                if content.startswith("json"):
                    content = content[4:]
                elif content.startswith("JSON"):
                    content = content[4:]
                content = content.strip()

        try:
            return json.loads(content)
        except json.JSONDecodeError as e:
            logger.warning(f"Failed to parse JSON from OpenRouter: {e}")
            logger.debug(f"Raw content: {content[:200]}")
            return None

    @staticmethod
    def get_available_models() -> dict[str, str]:
        """Get dict of common model shortcuts and their full identifiers."""
        return OPENROUTER_MODELS.copy()
