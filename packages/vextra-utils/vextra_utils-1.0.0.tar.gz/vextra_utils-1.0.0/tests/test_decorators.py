import asyncio
import time
from threading import Thread
from unittest.mock import patch

import pytest

from vextra_utils import synchronized, with_semaphore, with_timer


class TestWithTimer:
    def test_sync_function_returns_correct_value(self) -> None:
        @with_timer
        def add(a: int, b: int) -> int:
            return a + b

        assert add(2, 3) == 5

    def test_sync_function_logs_execution_time(self) -> None:
        with patch("vextra_utils.decorators._logger") as mock_logger:

            @with_timer
            def slow_func() -> str:
                time.sleep(0.1)
                return "done"

            result = slow_func()

            assert result == "done"
            mock_logger.info.assert_called_once()
            log_message = mock_logger.info.call_args[0][0]
            assert "slow_func took" in log_message
            assert "s" in log_message

    def test_sync_function_preserves_name(self) -> None:
        @with_timer
        def my_function() -> None:
            pass

        assert my_function.__name__ == "my_function"

    @pytest.mark.asyncio
    async def test_async_function_returns_correct_value(self) -> None:
        @with_timer
        async def async_add(a: int, b: int) -> int:
            await asyncio.sleep(0.01)
            return a + b

        result = await async_add(2, 3)
        assert result == 5

    @pytest.mark.asyncio
    async def test_async_function_logs_execution_time(self) -> None:
        with patch("vextra_utils.decorators._logger") as mock_logger:

            @with_timer
            async def async_slow_func() -> str:
                await asyncio.sleep(0.1)
                return "done"

            result = await async_slow_func()

            assert result == "done"
            mock_logger.info.assert_called_once()
            log_message = mock_logger.info.call_args[0][0]
            assert "async_slow_func took" in log_message

    @pytest.mark.asyncio
    async def test_async_function_preserves_name(self) -> None:
        @with_timer
        async def my_async_function() -> None:
            pass

        assert my_async_function.__name__ == "my_async_function"

    def test_sync_function_with_exception(self) -> None:
        with patch("vextra_utils.decorators._logger") as mock_logger:

            @with_timer
            def failing_func() -> None:
                raise ValueError("test error")

            with pytest.raises(ValueError, match="test error"):
                failing_func()

            mock_logger.info.assert_called_once()

    @pytest.mark.asyncio
    async def test_async_function_with_exception(self) -> None:
        with patch("vextra_utils.decorators._logger") as mock_logger:

            @with_timer
            async def async_failing_func() -> None:
                raise ValueError("async test error")

            with pytest.raises(ValueError, match="async test error"):
                await async_failing_func()

            mock_logger.info.assert_called_once()


class TestWithSemaphore:
    @pytest.mark.asyncio
    async def test_limits_concurrent_execution(self) -> None:
        semaphore = asyncio.Semaphore(2)
        active_count = 0
        max_concurrent = 0

        @with_semaphore(semaphore)
        async def limited_task() -> None:
            nonlocal active_count, max_concurrent
            active_count += 1
            max_concurrent = max(max_concurrent, active_count)
            await asyncio.sleep(0.1)
            active_count -= 1

        await asyncio.gather(*[limited_task() for _ in range(5)])

        assert max_concurrent == 2

    @pytest.mark.asyncio
    async def test_returns_correct_value(self) -> None:
        semaphore = asyncio.Semaphore(3)

        @with_semaphore(semaphore)
        async def fetch(value: int) -> int:
            await asyncio.sleep(0.01)
            return value * 2

        result = await fetch(5)
        assert result == 10

    @pytest.mark.asyncio
    async def test_preserves_function_name(self) -> None:
        semaphore = asyncio.Semaphore(1)

        @with_semaphore(semaphore)
        async def my_limited_func() -> None:
            pass

        assert my_limited_func.__name__ == "my_limited_func"

    @pytest.mark.asyncio
    async def test_propagates_exception(self) -> None:
        semaphore = asyncio.Semaphore(1)

        @with_semaphore(semaphore)
        async def failing_task() -> None:
            raise RuntimeError("task failed")

        with pytest.raises(RuntimeError, match="task failed"):
            await failing_task()

    @pytest.mark.asyncio
    async def test_releases_semaphore_on_exception(self) -> None:
        semaphore = asyncio.Semaphore(1)

        @with_semaphore(semaphore)
        async def failing_task() -> None:
            raise RuntimeError("task failed")

        with pytest.raises(RuntimeError):
            await failing_task()

        assert semaphore._value == 1


class TestSynchronized:
    def test_returns_correct_value(self) -> None:
        @synchronized()
        def add(a: int, b: int) -> int:
            return a + b

        assert add(2, 3) == 5

    def test_preserves_function_name(self) -> None:
        @synchronized()
        def my_sync_func() -> None:
            pass

        assert my_sync_func.__name__ == "my_sync_func"

    def test_thread_safety_without_shared_lock(self) -> None:
        counter = {"value": 0}

        @synchronized()
        def increment() -> None:
            current = counter["value"]
            time.sleep(0.0001)
            counter["value"] = current + 1

        threads = [Thread(target=increment) for _ in range(10)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert counter["value"] == 10

    def test_thread_safety_with_shared_lock(self) -> None:
        from threading import Lock

        shared_lock = Lock()
        counter = {"value": 0}

        @synchronized(shared_lock)
        def increment() -> None:
            current = counter["value"]
            time.sleep(0.0001)
            counter["value"] = current + 1

        @synchronized(shared_lock)
        def decrement() -> None:
            current = counter["value"]
            time.sleep(0.0001)
            counter["value"] = current - 1

        threads = []
        for _ in range(5):
            threads.append(Thread(target=increment))
            threads.append(Thread(target=decrement))

        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert counter["value"] == 0

    def test_propagates_exception(self) -> None:
        @synchronized()
        def failing_func() -> None:
            raise ValueError("sync error")

        with pytest.raises(ValueError, match="sync error"):
            failing_func()

    def test_uses_reentrant_lock_by_default(self) -> None:
        call_count = 0

        @synchronized()
        def outer() -> int:
            nonlocal call_count
            call_count += 1
            return inner()

        @synchronized()
        def inner() -> int:
            nonlocal call_count
            call_count += 1
            return 42

        result = outer()
        assert result == 42
        assert call_count == 2
