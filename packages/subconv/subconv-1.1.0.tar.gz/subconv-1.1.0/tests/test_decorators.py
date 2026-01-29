import asyncio
from unittest.mock import patch

import pytest

from subconv._decorators import with_semaphore, with_timer


class TestWithTimer:
    def test_sync_function_returns_result(self):
        @with_timer
        def add(a, b):
            return a + b

        result = add(2, 3)

        assert result == 5

    def test_sync_function_logs_time(self):
        @with_timer
        def dummy():
            return "done"

        with patch("subconv._decorators.logger") as mock_logger:
            dummy()

            mock_logger.info.assert_called_once()
            log_message = mock_logger.info.call_args[0][0]
            assert "dummy" in log_message
            assert "took" in log_message

    @pytest.mark.asyncio
    async def test_async_function_returns_result(self):
        @with_timer
        async def async_add(a, b):
            return a + b

        result = await async_add(2, 3)

        assert result == 5

    @pytest.mark.asyncio
    async def test_async_function_logs_time(self):
        @with_timer
        async def async_dummy():
            return "done"

        with patch("subconv._decorators.logger") as mock_logger:
            await async_dummy()

            mock_logger.info.assert_called_once()
            log_message = mock_logger.info.call_args[0][0]
            assert "async_dummy" in log_message
            assert "took" in log_message

    def test_preserves_function_name(self):
        @with_timer
        def my_function():
            pass

        assert my_function.__name__ == "my_function"

    @pytest.mark.asyncio
    async def test_async_preserves_function_name(self):
        @with_timer
        async def my_async_function():
            pass

        assert my_async_function.__name__ == "my_async_function"

    def test_handles_exception(self):
        @with_timer
        def failing_function():
            raise ValueError("error")

        with patch("subconv._decorators.logger"):
            with pytest.raises(ValueError, match="error"):
                failing_function()

    @pytest.mark.asyncio
    async def test_async_handles_exception(self):
        @with_timer
        async def async_failing():
            raise ValueError("async error")

        with patch("subconv._decorators.logger"):
            with pytest.raises(ValueError, match="async error"):
                await async_failing()


class TestWithSemaphore:
    @pytest.mark.asyncio
    async def test_limits_concurrency(self):
        semaphore = asyncio.Semaphore(2)
        active_count = 0
        max_concurrent = 0

        @with_semaphore(semaphore)
        async def limited_task():
            nonlocal active_count, max_concurrent
            active_count += 1
            max_concurrent = max(max_concurrent, active_count)
            await asyncio.sleep(0.1)
            active_count -= 1
            return "done"

        tasks = [limited_task() for _ in range(5)]
        results = await asyncio.gather(*tasks)

        assert all(r == "done" for r in results)
        assert max_concurrent <= 2

    @pytest.mark.asyncio
    async def test_returns_result(self):
        semaphore = asyncio.Semaphore(1)

        @with_semaphore(semaphore)
        async def compute(x):
            return x * 2

        result = await compute(5)

        assert result == 10

    @pytest.mark.asyncio
    async def test_preserves_function_name(self):
        semaphore = asyncio.Semaphore(1)

        @with_semaphore(semaphore)
        async def my_limited_function():
            pass

        assert my_limited_function.__name__ == "my_limited_function"

    @pytest.mark.asyncio
    async def test_releases_semaphore_on_exception(self):
        semaphore = asyncio.Semaphore(1)

        @with_semaphore(semaphore)
        async def failing_task():
            raise ValueError("failed")

        with pytest.raises(ValueError):
            await failing_task()

        assert semaphore._value == 1

    @pytest.mark.asyncio
    async def test_passes_args_and_kwargs(self):
        semaphore = asyncio.Semaphore(1)

        @with_semaphore(semaphore)
        async def task_with_args(a, b, c=None):
            return (a, b, c)

        result = await task_with_args(1, 2, c=3)

        assert result == (1, 2, 3)
