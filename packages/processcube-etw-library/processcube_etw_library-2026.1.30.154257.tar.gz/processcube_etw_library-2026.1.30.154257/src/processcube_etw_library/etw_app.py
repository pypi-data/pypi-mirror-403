import asyncio
from concurrent.futures import ThreadPoolExecutor
from contextlib import asynccontextmanager
from typing import Callable, Optional

from fastapi import FastAPI
import uvicorn

from .settings import load_settings
from .health import (
    add_built_in_health_checks,
    HealthCheck,
    HealthCheckRegistry,
    setup_health_routes,
)
from .create_external_task_client import create_external_task_client
from .server_config import get_server_config
from .typed_handler import create_typed_handler_wrapper
from .processcube_client.external_task import ExternalTaskClient


class ExternalTaskWorkerApp:
    _etw_client: ExternalTaskClient
    _health_registry: HealthCheckRegistry
    _executor: ThreadPoolExecutor
    _etw_future: Optional[asyncio.Future]
    _app: FastAPI

    def __init__(
        self, etw_client: ExternalTaskClient, built_in_health_checks: bool = True
    ):
        self._executor = ThreadPoolExecutor(max_workers=1)
        self._etw_future = None
        self._etw_client = etw_client
        self._app = FastAPI(lifespan=self._lifespan)
        self._health_registry = HealthCheckRegistry()
        if built_in_health_checks:
            add_built_in_health_checks(self._health_registry)
        setup_health_routes(self._app, self._health_registry)

    @asynccontextmanager
    async def _lifespan(self, app: FastAPI):
        loop = asyncio.get_running_loop()
        self._etw_future = loop.run_in_executor(self._executor, self._etw_client.start)

        yield

        loop = asyncio.get_running_loop()
        await loop.run_in_executor(None, self._etw_client.stop)

        if self._etw_future is not None and not self._etw_future.done():
            self._etw_future.cancel()
            try:
                await self._etw_future
            except asyncio.CancelledError:
                pass

        self._executor.shutdown(wait=False)

    @property
    def fastapi_app(self) -> FastAPI:
        return self._app

    def run(self) -> None:
        config = get_server_config()
        uvicorn.run(self._app, **config)

    def subscribe_to_external_task_for_topic(
        self, topic: str, handler: Callable, **options
    ) -> None:
        settings = load_settings()
        self._etw_client.subscribe_to_external_task_topic(
            topic,
            handler,
            long_polling_timeout_in_ms=settings.processcube_etw_long_polling_timeout_in_ms,
            **options,
        )

    def subscribe_to_external_task_for_topic_typed(
        self, topic: str, handler: Callable, **options
    ) -> None:
        settings = load_settings()
        wrapper = create_typed_handler_wrapper(handler)
        self._etw_client.subscribe_to_external_task_topic(
            topic,
            wrapper,
            long_polling_timeout_in_ms=settings.processcube_etw_long_polling_timeout_in_ms,
            **options,
        )

    def add_health_check(self, check: HealthCheck) -> None:
        self._health_registry.register(check)

    def remove_health_check(self, service_name: str) -> bool:
        return self._health_registry.unregister(service_name)

    def get_health_checks(self) -> list[HealthCheck]:
        return self._health_registry.get_all()

    def get_health_check(self, service_name: str) -> Optional[HealthCheck]:
        return self._health_registry.get_by_name(service_name)


def new_external_task_worker_app(
    built_in_health_checks: bool = True,
) -> ExternalTaskWorkerApp:
    external_task_client = create_external_task_client()

    return ExternalTaskWorkerApp(
        external_task_client, built_in_health_checks=built_in_health_checks
    )
