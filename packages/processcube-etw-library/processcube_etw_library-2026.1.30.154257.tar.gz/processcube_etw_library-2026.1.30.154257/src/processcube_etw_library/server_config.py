from typing import TypedDict

from .settings import load_settings


class ServerConfig(TypedDict, total=False):
    host: str
    port: int
    log_level: str
    access_log: bool
    reload: bool


def get_server_config() -> ServerConfig:
    settings = load_settings()

    if settings.environment == "production":
        return ServerConfig(
            host="0.0.0.0",
            port=8000,
            log_level="warning",
            access_log=False,
        )
    else:
        return ServerConfig(
            host="0.0.0.0",
            port=8000,
            log_level="debug",
            access_log=True,
        )
