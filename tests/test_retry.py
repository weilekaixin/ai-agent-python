"""
Unit tests for with_retry and async_with_retry decorators.
No I/O, no external dependencies.
"""
from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from ai_agent.core.retry import async_with_retry, with_retry


# ---------------------------------------------------------------------------
# Synchronous retry
# ---------------------------------------------------------------------------

class TestWithRetry:
    def test_success_on_first_attempt(self):
        fn = MagicMock(return_value="ok")
        assert with_retry(max_attempts=3)(fn)() == "ok"
        fn.assert_called_once()

    def test_retries_then_succeeds(self):
        fn = MagicMock(side_effect=[ValueError("fail"), ValueError("fail"), "ok"])
        result = with_retry(max_attempts=3, base_delay=0)(fn)()
        assert result == "ok"
        assert fn.call_count == 3

    def test_raises_after_max_attempts(self):
        fn = MagicMock(side_effect=ValueError("always fails"))
        with pytest.raises(ValueError, match="always fails"):
            with_retry(max_attempts=2, base_delay=0)(fn)()
        assert fn.call_count == 2

    def test_no_retry_for_untracked_exception(self):
        fn = MagicMock(side_effect=RuntimeError("fatal"))
        with pytest.raises(RuntimeError):
            with_retry(max_attempts=3, base_delay=0, exceptions=(ValueError,))(fn)()
        fn.assert_called_once()  # no retry because RuntimeError not in exceptions tuple

    def test_preserves_function_metadata(self):
        def my_func():
            """docstring"""

        wrapped = with_retry()(my_func)
        assert wrapped.__name__ == "my_func"
        assert wrapped.__doc__ == """docstring"""


# ---------------------------------------------------------------------------
# Async retry
# ---------------------------------------------------------------------------

class TestAsyncWithRetry:
    async def test_success_on_first_attempt(self):
        async def fn():
            return "ok"

        assert await async_with_retry(max_attempts=3)(fn)() == "ok"

    async def test_retries_then_succeeds(self):
        call_count = 0

        async def fn():
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise ConnectionError("transient")
            return "done"

        result = await async_with_retry(max_attempts=3, base_delay=0)(fn)()
        assert result == "done"
        assert call_count == 3

    async def test_raises_after_max_attempts(self):
        async def fn():
            raise TimeoutError("timeout")

        with pytest.raises(TimeoutError):
            await async_with_retry(max_attempts=2, base_delay=0)(fn)()

    async def test_preserves_function_metadata(self):
        async def my_async_func():
            pass

        assert async_with_retry()(my_async_func).__name__ == "my_async_func"
