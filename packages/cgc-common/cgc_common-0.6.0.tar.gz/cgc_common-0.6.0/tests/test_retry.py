"""Tests for retry module."""

import pytest
from unittest.mock import MagicMock
from cgc_common.utils.retry import retry_on_failure


class TestRetryOnFailure:
    def test_success_first_try(self):
        call_count = 0

        @retry_on_failure(max_attempts=3)
        def succeeds():
            nonlocal call_count
            call_count += 1
            return "success"

        result = succeeds()
        assert result == "success"
        assert call_count == 1

    def test_success_after_retries(self):
        call_count = 0

        @retry_on_failure(max_attempts=3)
        def fails_twice():
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise ValueError("fail")
            return "success"

        result = fails_twice()
        assert result == "success"
        assert call_count == 3

    def test_all_attempts_fail(self):
        call_count = 0

        @retry_on_failure(max_attempts=3)
        def always_fails():
            nonlocal call_count
            call_count += 1
            raise ValueError("always fails")

        with pytest.raises(ValueError, match="always fails"):
            always_fails()
        assert call_count == 3

    def test_specific_exceptions(self):
        call_count = 0

        @retry_on_failure(max_attempts=3, exceptions=(ValueError,))
        def raises_type_error():
            nonlocal call_count
            call_count += 1
            raise TypeError("not caught")

        with pytest.raises(TypeError):
            raises_type_error()
        assert call_count == 1  # No retry for uncaught exception

    def test_with_logger(self):
        call_count = 0
        logger = MagicMock()

        @retry_on_failure(max_attempts=3, logger=logger)
        def fails_twice_with_logging():
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise ValueError("retry me")
            return "done"

        result = fails_twice_with_logging()
        assert result == "done"
        assert logger.warning.call_count == 2

    def test_preserves_function_metadata(self):
        @retry_on_failure(max_attempts=2)
        def my_function():
            """My docstring."""
            pass

        assert my_function.__name__ == "my_function"
        assert my_function.__doc__ == "My docstring."

    def test_with_arguments(self):
        @retry_on_failure(max_attempts=2)
        def add(a, b):
            return a + b

        assert add(2, 3) == 5
        assert add(a=1, b=2) == 3
