from collections.abc import Awaitable, Callable
from datetime import timedelta
from time import perf_counter
import inspect
from async_lru import alru_cache

import httpx

from .models import HealthCheckResult


type HealthCheckCondition = Callable[[], bool | Awaitable[bool]]


class HealthCheck:
    def __init__(
        self,
        condition: HealthCheckCondition,
        service_name: str,
        tags: list[str] | None = None,
        comments: list[str] | None = None,
    ):
        self.condition = condition
        self.service_name = service_name
        self.tags = tags or []
        self.comments = comments or []

    async def run(self) -> HealthCheckResult:
        start = perf_counter()
        try:
            result = self.condition()
            if inspect.isawaitable(result):
                result = await result
            healthy = bool(result)
        except Exception:
            healthy = False
        elapsed = perf_counter() - start
        return HealthCheckResult(healthy=healthy, time_taken=timedelta(seconds=elapsed))


def create_url_health_check(
    url: str, timeout: float = 5.0, use_cache: bool = False, ttl: int = 60
) -> HealthCheckCondition:
    @alru_cache(maxsize=128, ttl=ttl)
    async def check_cached():
        async with httpx.AsyncClient() as client:
            response = await client.get(url, timeout=timeout)
            return response.status_code == 200

    async def check_no_cache():
        async with httpx.AsyncClient() as client:
            response = await client.get(url, timeout=timeout)
            return response.status_code == 200

    return check_cached if use_cache else check_no_cache
