"""Rate limiter для контроля параллельных запросов."""
import asyncio
from typing import Optional


class RateLimiter:
    """Ограничивает количество одновременных запросов с помощью Semaphore."""

    def __init__(self, max_concurrent: int = 10):
        """
        Args:
            max_concurrent: Максимальное количество параллельных запросов
        """
        self.semaphore = asyncio.Semaphore(max_concurrent)
        self.max_concurrent = max_concurrent

    async def __aenter__(self):
        """Acquire semaphore."""
        await self.semaphore.acquire()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Release semaphore."""
        self.semaphore.release()

    async def execute(self, coro):
        """
        Выполняет корутину с rate limiting.

        Args:
            coro: Корутина для выполнения

        Returns:
            Результат выполнения корутины
        """
        async with self:
            return await coro
