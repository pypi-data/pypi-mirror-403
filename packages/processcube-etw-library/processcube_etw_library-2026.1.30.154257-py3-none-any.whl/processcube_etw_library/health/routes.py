from fastapi import FastAPI

from .registry import HealthCheckRegistry
from .handlers import health_check
from .models import (
    HealthCheckModel,
    LivezResponse,
)


def setup_health_routes(app: FastAPI, registry: HealthCheckRegistry) -> None:
    @app.get(
        "/healthyz",
        response_model=HealthCheckModel,
        responses={503: {"model": HealthCheckModel}},
    )
    @app.get(
        "/readyz",
        response_model=HealthCheckModel,
        responses={503: {"model": HealthCheckModel}},
    )
    async def health_check_route() -> HealthCheckModel:
        return await health_check(registry)

    @app.get("/livez", response_model=LivezResponse)
    def livez() -> LivezResponse:
        return LivezResponse(status="alive")
