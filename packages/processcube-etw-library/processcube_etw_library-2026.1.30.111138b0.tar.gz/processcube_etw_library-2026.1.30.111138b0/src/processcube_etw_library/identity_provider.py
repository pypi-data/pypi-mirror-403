import logging
import sys

from oauth2_client.credentials_manager import CredentialManager, ServiceInformation
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
)
from requests import exceptions

logger = logging.getLogger("processcube.oauth")


def exit_after_retries(retry_state):
    logger.error(
        f"Failed to obtain OAuth access token after {retry_state} attempts. Exiting."
    )
    sys.exit(1)


def log_failed_attempt(retry_state):
    logger.warning(
        f"Attempt {retry_state.attempt_number} to obtain OAuth access token failed: {retry_state.outcome.exception()}"
    )


class IdentityProvider:
    def __init__(
        self,
        authority_url: str,
        client_name: str,
        client_secret: str,
        client_scopes: str,
        max_get_oauth_access_token_retries: int,
    ):
        self._authority_url = authority_url
        self._client_name = client_name
        self._client_secret = client_secret
        self._client_scopes = client_scopes
        self._max_get_oauth_access_token_retries = max_get_oauth_access_token_retries

        self._access_token_caller = self._prepare_get_access_token_caller()
        logger.debug(
            f"Prepare identity provider with (authority_url={authority_url}, client_name={client_name}, client_secret=***, client_scopes={client_scopes})."
        )

    def __call__(self):
        return self._access_token_caller()

    def _prepare_get_access_token_caller(self):
        @retry(
            stop=stop_after_attempt(self._max_get_oauth_access_token_retries),
            wait=wait_exponential(multiplier=1, min=2, max=30),
            retry=retry_if_exception_type(exceptions.ConnectionError),
            after=log_failed_attempt,
            retry_error_callback=exit_after_retries,
        )
        def get_access_token(authority_url, client_name, client_secret, client_scopes):
            logger.debug(
                f"Get access token from ProcessCube (authority_url={authority_url}, client_name={client_name}, client_secret=***, client_scopes={client_scopes})."
            )

            client_scopes = client_scopes.split(" ")

            service_information = ServiceInformation(
                f"{authority_url}/auth",
                f"{authority_url}/token",
                client_name,
                client_secret,
                client_scopes,
            )
            manager = CredentialManager(service_information)

            manager.init_with_client_credentials()

            return {"token": manager._access_token}

        return lambda: get_access_token(
            self._authority_url,
            self._client_name,
            self._client_secret,
            self._client_scopes,
        )
