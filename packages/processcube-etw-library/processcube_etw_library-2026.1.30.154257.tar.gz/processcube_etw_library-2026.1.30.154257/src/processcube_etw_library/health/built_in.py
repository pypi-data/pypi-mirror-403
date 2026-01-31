from ..settings import load_settings
from .check import HealthCheck, create_url_health_check
from .registry import HealthCheckRegistry


def add_built_in_health_checks(registry: HealthCheckRegistry) -> None:
    settings = load_settings()

    engine_url = (
        settings.processcube_engine_url.strip("/") + "/atlas_engine/api/v1/info"
    )

    authority_url = (
        settings.processcube_authority_url.strip("/")
        + "/.well-known/openid-configuration"
    )

    registry.register(
        HealthCheck(
            create_url_health_check(engine_url, use_cache=True, ttl=300),
            service_name="ProcessCube Engine",
            tags=["core", "backend"],
            comments=["Checks if the ProcessCube Engine is reachable"],
        )
    )
    registry.register(
        HealthCheck(
            create_url_health_check(authority_url, use_cache=True, ttl=300),
            service_name="ProcessCube Authority",
            tags=["core", "auth"],
            comments=["Checks if the ProcessCube Authority is reachable"],
        )
    )
