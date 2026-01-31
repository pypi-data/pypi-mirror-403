import asyncio
from datetime import timedelta
from time import perf_counter

from fastapi.responses import JSONResponse

from .check import HealthCheck
from .models import (
    HealthCheckEntityModel,
    HealthCheckModel,
)
from .registry import HealthCheckRegistry


async def _run_health_checks(checks: list[HealthCheck]) -> HealthCheckModel:
    total_start = perf_counter()
    results = await asyncio.gather(*(check.run() for check in checks))
    total_elapsed = perf_counter() - total_start

    entities = []
    all_healthy = True
    for check, result in zip(checks, results):
        if not result.healthy:
            all_healthy = False
        entity = HealthCheckEntityModel(
            service=check.service_name,
            status="healthy" if result.healthy else "unhealthy",
            time_taken=result.time_taken,
            tags=check.tags,
            comments=check.comments,
        )
        entities.append(entity)

    return HealthCheckModel(
        status="healthy" if all_healthy else "unhealthy",
        total_time_taken=timedelta(seconds=total_elapsed),
        entities=entities,
    )


async def health_check(registry: HealthCheckRegistry) -> HealthCheckModel:
    health_result = await _run_health_checks(registry.get_all())
    status_code = 200 if health_result.status == "healthy" else 503
    return JSONResponse(content=health_result.model_dump(), status_code=status_code)
