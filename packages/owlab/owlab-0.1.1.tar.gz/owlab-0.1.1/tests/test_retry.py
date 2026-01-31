"""Tests for retry utilities."""

from unittest.mock import Mock

import pytest

from owlab.utils.retry import retry
from owlab.utils.retry import retry_on_http_error
from owlab.utils.retry import RetryError


class TestRetry:
    """Tests for retry decorators."""

    def test_retry_success(self):
        """Test retry decorator with successful call."""
        call_count = 0

        @retry(max_attempts=3)
        def successful_func():
            nonlocal call_count
            call_count += 1
            return "success"

        result = successful_func()
        assert result == "success"
        assert call_count == 1

    def test_retry_failure_then_success(self):
        """Test retry decorator with failure then success."""
        call_count = 0

        @retry(max_attempts=3, delay=0.1)
        def flaky_func():
            nonlocal call_count
            call_count += 1
            if call_count < 2:
                raise ValueError("Temporary failure")
            return "success"

        result = flaky_func()
        assert result == "success"
        assert call_count == 2

    def test_retry_all_failures(self):
        """Test retry decorator with all failures."""
        call_count = 0

        @retry(max_attempts=3, delay=0.1)
        def failing_func():
            nonlocal call_count
            call_count += 1
            raise ValueError("Always fails")

        with pytest.raises(RetryError):
            failing_func()
        assert call_count == 3

    def test_retry_specific_exception(self):
        """Test retry decorator with specific exception."""
        call_count = 0

        @retry(max_attempts=3, exceptions=ValueError)
        def func_with_wrong_exception():
            nonlocal call_count
            call_count += 1
            raise TypeError("Wrong exception")

        with pytest.raises(TypeError):
            func_with_wrong_exception()
        assert call_count == 1

    def test_retry_on_http_error_success(self):
        """Test retry_on_http_error with successful HTTP call."""
        mock_response = Mock()
        mock_response.status_code = 200

        @retry_on_http_error(max_attempts=3)
        def successful_http_func():
            return mock_response

        result = successful_http_func()
        assert result.status_code == 200

    def test_retry_on_http_error_retryable_status(self):
        """Test retry_on_http_error with retryable status code."""
        call_count = 0

        @retry_on_http_error(max_attempts=3, delay=0.1, status_codes=(429,))
        def flaky_http_func():
            nonlocal call_count
            call_count += 1
            mock_response = Mock()
            if call_count < 2:
                mock_response.status_code = 429
            else:
                mock_response.status_code = 200
            return mock_response

        result = flaky_http_func()
        assert result.status_code == 200
        assert call_count == 2

    def test_retry_on_http_error_all_failures(self):
        """Test retry_on_http_error with all failures."""
        call_count = 0

        @retry_on_http_error(max_attempts=2, delay=0.1, status_codes=(500,))
        def failing_http_func():
            nonlocal call_count
            call_count += 1
            mock_response = Mock()
            mock_response.status_code = 500
            return mock_response

        result = failing_http_func()
        # Should return the last response even if it failed
        assert result.status_code == 500
        assert call_count == 2
