"""Tests for OpenRouter client."""

import json
from unittest.mock import MagicMock, patch

import pytest

from cgc_common.openrouter import (
    OpenRouterClient,
    OpenRouterResponse,
    OPENROUTER_MODELS,
    DEFAULT_MODEL,
)


class TestOpenRouterResponse:
    """Tests for OpenRouterResponse dataclass."""

    def test_success_response(self):
        """Test successful response."""
        resp = OpenRouterResponse(success=True, content="Hello!")
        assert resp.success is True
        assert resp.content == "Hello!"
        assert resp.error is None

    def test_error_response(self):
        """Test error response."""
        resp = OpenRouterResponse(success=False, content="", error="API error")
        assert resp.success is False
        assert resp.content == ""
        assert resp.error == "API error"

    def test_with_usage(self):
        """Test response with usage info."""
        usage = {"prompt_tokens": 10, "completion_tokens": 20}
        resp = OpenRouterResponse(
            success=True, content="Test", model="llama", usage=usage
        )
        assert resp.usage == usage
        assert resp.model == "llama"


class TestOpenRouterClient:
    """Tests for OpenRouterClient."""

    def test_init_with_credentials(self):
        """Test initialization with explicit credentials."""
        client = OpenRouterClient(api_key="sk-test", model="test-model")
        assert client.api_key == "sk-test"
        assert client.model == "test-model"
        assert client.is_configured() is True

    def test_init_without_credentials(self):
        """Test initialization without credentials."""
        client = OpenRouterClient()
        assert client.api_key is None
        assert client.model == DEFAULT_MODEL
        assert client.is_configured() is False

    def test_default_model(self):
        """Test default model is set."""
        client = OpenRouterClient(api_key="sk-test")
        assert client.model == DEFAULT_MODEL

    def test_set_api_key(self):
        """Test setting API key."""
        client = OpenRouterClient()
        client.set_api_key("sk-new")
        assert client.api_key == "sk-new"

    def test_set_model(self):
        """Test setting model."""
        client = OpenRouterClient()
        client.set_model("new-model")
        assert client.model == "new-model"

    def test_is_configured_no_key(self):
        """Test is_configured without API key."""
        client = OpenRouterClient(model="test")
        assert client.is_configured() is False

    def test_is_configured_with_key(self):
        """Test is_configured with API key."""
        client = OpenRouterClient(api_key="sk-test")
        assert client.is_configured() is True

    def test_get_available_models(self):
        """Test getting available models."""
        models = OpenRouterClient.get_available_models()
        assert isinstance(models, dict)
        assert len(models) > 0
        assert "llama-3.1-8b" in models


class TestOpenRouterClientComplete:
    """Tests for complete() method."""

    def test_complete_no_api_key(self):
        """Test complete without API key."""
        client = OpenRouterClient()
        result = client.complete("Hello")
        assert result.success is False
        assert "No API key" in result.error

    @patch("cgc_common.openrouter.httpx")
    def test_complete_success(self, mock_httpx):
        """Test successful completion."""
        # Mock response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "choices": [{"message": {"content": "Hello back!"}}],
            "usage": {"prompt_tokens": 5, "completion_tokens": 3},
        }

        mock_client = MagicMock()
        mock_client.__enter__ = MagicMock(return_value=mock_client)
        mock_client.__exit__ = MagicMock(return_value=False)
        mock_client.post.return_value = mock_response
        mock_httpx.Client.return_value = mock_client

        client = OpenRouterClient(api_key="sk-test", model="test-model")
        result = client.complete("Hello")

        assert result.success is True
        assert result.content == "Hello back!"
        assert result.model == "test-model"

    @patch("cgc_common.openrouter.httpx")
    def test_complete_with_system_prompt(self, mock_httpx):
        """Test completion with system prompt."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "choices": [{"message": {"content": "Response"}}]
        }

        mock_client = MagicMock()
        mock_client.__enter__ = MagicMock(return_value=mock_client)
        mock_client.__exit__ = MagicMock(return_value=False)
        mock_client.post.return_value = mock_response
        mock_httpx.Client.return_value = mock_client

        client = OpenRouterClient(api_key="sk-test")
        result = client.complete("Hello", system_prompt="Be helpful")

        assert result.success is True
        # Verify system prompt was included
        call_args = mock_client.post.call_args
        messages = call_args[1]["json"]["messages"]
        assert len(messages) == 2
        assert messages[0]["role"] == "system"
        assert messages[0]["content"] == "Be helpful"

    @patch("cgc_common.openrouter.httpx")
    def test_complete_401_error(self, mock_httpx):
        """Test 401 unauthorized error."""
        mock_response = MagicMock()
        mock_response.status_code = 401

        mock_client = MagicMock()
        mock_client.__enter__ = MagicMock(return_value=mock_client)
        mock_client.__exit__ = MagicMock(return_value=False)
        mock_client.post.return_value = mock_response
        mock_httpx.Client.return_value = mock_client

        client = OpenRouterClient(api_key="bad-key")
        result = client.complete("Hello")

        assert result.success is False
        assert "invalid" in result.error.lower()

    @patch("cgc_common.openrouter.httpx")
    def test_complete_404_error(self, mock_httpx):
        """Test 404 model not found error."""
        mock_response = MagicMock()
        mock_response.status_code = 404

        mock_client = MagicMock()
        mock_client.__enter__ = MagicMock(return_value=mock_client)
        mock_client.__exit__ = MagicMock(return_value=False)
        mock_client.post.return_value = mock_response
        mock_httpx.Client.return_value = mock_client

        client = OpenRouterClient(api_key="sk-test", model="unknown-model")
        result = client.complete("Hello")

        assert result.success is False
        assert "not found" in result.error.lower()
        assert "unknown-model" in result.error

    @patch("cgc_common.openrouter.httpx")
    def test_complete_429_rate_limit(self, mock_httpx):
        """Test 429 rate limit error."""
        mock_response = MagicMock()
        mock_response.status_code = 429

        mock_client = MagicMock()
        mock_client.__enter__ = MagicMock(return_value=mock_client)
        mock_client.__exit__ = MagicMock(return_value=False)
        mock_client.post.return_value = mock_response
        mock_httpx.Client.return_value = mock_client

        client = OpenRouterClient(api_key="sk-test")
        result = client.complete("Hello")

        assert result.success is False
        assert "rate limit" in result.error.lower()

    @patch("cgc_common.openrouter.httpx")
    def test_complete_connection_error(self, mock_httpx):
        """Test connection error handling."""
        mock_httpx.Client.side_effect = Exception("Network error")

        client = OpenRouterClient(api_key="sk-test")
        result = client.complete("Hello")

        assert result.success is False
        assert "error" in result.error.lower()


class TestOpenRouterClientExtractJson:
    """Tests for extract_json() method."""

    @patch("cgc_common.openrouter.httpx")
    def test_extract_json_success(self, mock_httpx):
        """Test successful JSON extraction."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "choices": [{"message": {"content": '{"name": "Test", "value": 42}'}}]
        }

        mock_client = MagicMock()
        mock_client.__enter__ = MagicMock(return_value=mock_client)
        mock_client.__exit__ = MagicMock(return_value=False)
        mock_client.post.return_value = mock_response
        mock_httpx.Client.return_value = mock_client

        client = OpenRouterClient(api_key="sk-test")
        result = client.extract_json("Return JSON")

        assert result == {"name": "Test", "value": 42}

    @patch("cgc_common.openrouter.httpx")
    def test_extract_json_markdown_block(self, mock_httpx):
        """Test JSON extraction from markdown code block."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "choices": [
                {"message": {"content": '```json\n{"key": "value"}\n```'}}
            ]
        }

        mock_client = MagicMock()
        mock_client.__enter__ = MagicMock(return_value=mock_client)
        mock_client.__exit__ = MagicMock(return_value=False)
        mock_client.post.return_value = mock_response
        mock_httpx.Client.return_value = mock_client

        client = OpenRouterClient(api_key="sk-test")
        result = client.extract_json("Return JSON")

        assert result == {"key": "value"}

    @patch("cgc_common.openrouter.httpx")
    def test_extract_json_invalid(self, mock_httpx):
        """Test invalid JSON handling."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "choices": [{"message": {"content": "This is not JSON"}}]
        }

        mock_client = MagicMock()
        mock_client.__enter__ = MagicMock(return_value=mock_client)
        mock_client.__exit__ = MagicMock(return_value=False)
        mock_client.post.return_value = mock_response
        mock_httpx.Client.return_value = mock_client

        client = OpenRouterClient(api_key="sk-test")
        result = client.extract_json("Return JSON")

        assert result is None

    def test_extract_json_no_api_key(self):
        """Test extract_json without API key."""
        client = OpenRouterClient()
        result = client.extract_json("Return JSON")
        assert result is None


class TestOpenRouterClientCheckConnection:
    """Tests for check_connection() method."""

    def test_check_connection_no_key(self):
        """Test connection check without API key."""
        client = OpenRouterClient()
        result = client.check_connection()
        assert "⚠️" in result
        assert "No API key" in result

    @patch("cgc_common.openrouter.httpx")
    def test_check_connection_success(self, mock_httpx):
        """Test successful connection check."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "choices": [{"message": {"content": "Hi"}}]
        }

        mock_client = MagicMock()
        mock_client.__enter__ = MagicMock(return_value=mock_client)
        mock_client.__exit__ = MagicMock(return_value=False)
        mock_client.post.return_value = mock_response
        mock_httpx.Client.return_value = mock_client

        client = OpenRouterClient(api_key="sk-test", model="test-model")
        result = client.check_connection()

        assert "✅" in result
        assert "test-model" in result

    @patch("cgc_common.openrouter.httpx")
    def test_check_connection_failure(self, mock_httpx):
        """Test failed connection check."""
        mock_response = MagicMock()
        mock_response.status_code = 401

        mock_client = MagicMock()
        mock_client.__enter__ = MagicMock(return_value=mock_client)
        mock_client.__exit__ = MagicMock(return_value=False)
        mock_client.post.return_value = mock_response
        mock_httpx.Client.return_value = mock_client

        client = OpenRouterClient(api_key="bad-key")
        result = client.check_connection()

        assert "❌" in result


class TestOpenRouterClientFromSecrets:
    """Tests for from_secrets() class method."""

    @patch("cgc_common.secrets.SecretStore")
    def test_from_secrets(self, mock_store_class):
        """Test creating client from SecretStore."""
        mock_store = MagicMock()
        mock_store.get.side_effect = lambda key: {
            "openrouter_api_key": "sk-stored",
            "openrouter_model": "stored-model",
        }.get(key)
        mock_store_class.return_value = mock_store

        client = OpenRouterClient.from_secrets("myapp")

        assert client.api_key == "sk-stored"
        assert client.model == "stored-model"
        mock_store_class.assert_called_once_with("myapp")

    @patch("cgc_common.secrets.SecretStore")
    def test_from_secrets_default_model(self, mock_store_class):
        """Test from_secrets with default model."""
        mock_store = MagicMock()
        mock_store.get.side_effect = lambda key: {
            "openrouter_api_key": "sk-stored",
            "openrouter_model": None,
        }.get(key)
        mock_store_class.return_value = mock_store

        client = OpenRouterClient.from_secrets("myapp")

        assert client.api_key == "sk-stored"
        assert client.model == DEFAULT_MODEL


class TestOpenRouterModels:
    """Tests for model constants."""

    def test_models_dict_not_empty(self):
        """Test OPENROUTER_MODELS is not empty."""
        assert len(OPENROUTER_MODELS) > 0

    def test_default_model_set(self):
        """Test DEFAULT_MODEL is set."""
        assert DEFAULT_MODEL
        assert "llama" in DEFAULT_MODEL.lower()

    def test_model_format(self):
        """Test model identifiers have correct format."""
        for shortcut, full_id in OPENROUTER_MODELS.items():
            # Full ID should contain provider/model pattern
            assert "/" in full_id, f"Model {shortcut} missing provider prefix"
