import logging
from typing import Optional, Type, TypeVar

from pydantic import Field, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

from .processcube_client.app_info import AppInfoClient
from typing import TypedDict

logger = logging.getLogger(__name__)

T = TypeVar("T", bound="ETWSettings")


class DefaultsDict(TypedDict):
    PROCESSCUBE_ENGINE_URL: str
    PROCESSCUBE_ETW_CLIENT_ID: str
    PROCESSCUBE_ETW_CLIENT_SECRET: str
    PROCESSCUBE_ETW_CLIENT_SCOPES: str
    PROCESSCUBE_MAX_GET_OAUTH_ACCESS_TOKEN_RETRIES: int
    PROCESSCUBE_ETW_LONG_POLLING_TIMEOUT_IN_MS: int
    ENVIRONMENT: str


DEFAULTS: DefaultsDict = {
    "PROCESSCUBE_ENGINE_URL": "http://localhost:56000",
    "PROCESSCUBE_ETW_CLIENT_ID": "test_etw",
    "PROCESSCUBE_ETW_CLIENT_SECRET": "3ef62eb3-fe49-4c2c-ba6f-73e4d234321b",
    "PROCESSCUBE_ETW_CLIENT_SCOPES": "engine_etw",
    "PROCESSCUBE_MAX_GET_OAUTH_ACCESS_TOKEN_RETRIES": 10,
    "PROCESSCUBE_ETW_LONG_POLLING_TIMEOUT_IN_MS": 30_000,
    "ENVIRONMENT": "development",
}


def _determine_authority_url(engine_url: str) -> str:
    app_info_client = AppInfoClient(engine_url)
    authority_url = app_info_client.get_authority()
    if type(authority_url) is not str:
        raise ValueError("Could not determine authority URL from AppInfoClient")

    return authority_url


class ETWSettings(BaseSettings):
    """
    Base settings for the External Task Worker library.

    Users can extend this class to add their own settings:

        class MySettings(ETWSettings):
            my_custom_var: str = Field(default="default_value")

        # Load with custom settings class
        settings = load_settings(MySettings)
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    processcube_engine_url: str = Field(default=DEFAULTS["PROCESSCUBE_ENGINE_URL"])
    processcube_authority_url: str = Field(default="")
    processcube_etw_client_id: str = Field(
        default=DEFAULTS["PROCESSCUBE_ETW_CLIENT_ID"]
    )
    processcube_etw_client_secret: str = Field(
        default=DEFAULTS["PROCESSCUBE_ETW_CLIENT_SECRET"]
    )
    processcube_etw_client_scopes: str = Field(
        default=DEFAULTS["PROCESSCUBE_ETW_CLIENT_SCOPES"]
    )
    processcube_max_get_oauth_access_token_retries: int = Field(
        default=DEFAULTS["PROCESSCUBE_MAX_GET_OAUTH_ACCESS_TOKEN_RETRIES"]
    )
    processcube_etw_long_polling_timeout_in_ms: int = Field(
        default=DEFAULTS["PROCESSCUBE_ETW_LONG_POLLING_TIMEOUT_IN_MS"]
    )
    environment: str = Field(default=DEFAULTS["ENVIRONMENT"])

    @model_validator(mode="before")
    @classmethod
    def warn_missing_values(cls, values: dict) -> dict:
        for env_name, default_value in DEFAULTS.items():
            field_name = env_name.lower()
            if field_name not in values or values.get(field_name) is None:
                if default_value is not None:
                    logger.warning(
                        f"Environment variable '{env_name}' not set, using default: {default_value}"
                    )
        return values

    @model_validator(mode="after")
    def resolve_authority_url(self) -> "ETWSettings":
        if not self.processcube_authority_url.strip():
            self.processcube_authority_url = _determine_authority_url(
                self.processcube_engine_url
            )
            logger.info(
                f"Authority URL resolved from AppInfoClient: {self.processcube_authority_url}"
            )

        if self.processcube_etw_long_polling_timeout_in_ms >= 60_000:
            logger.warning(
                "PROCESSCUBE_ETW_LONG_POLLING_TIMEOUT_IN_MS is set to a high value "
                "({} ms). Consider reducing it to avoid potential connection issues.".format(
                    self.processcube_etw_long_polling_timeout_in_ms
                )
            )
        return self


_settings: Optional[ETWSettings] = None


def load_settings(settings_class: Type[T] = ETWSettings) -> T:
    """
    Call this with a custom settings class to extend the base settings:

        class MySettings(ETWSettings):
            my_var: str = Field(default="value")

        settings = load_settings(MySettings)
    """

    global _settings
    if _settings is None:
        _settings = settings_class()
    return _settings  # type: ignore
