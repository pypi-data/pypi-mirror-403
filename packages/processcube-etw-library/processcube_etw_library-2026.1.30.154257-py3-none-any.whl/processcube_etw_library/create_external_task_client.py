from .processcube_client.external_task import ExternalTaskClient

from .identity_provider import IdentityProvider
from .settings import load_settings


def create_external_task_client() -> ExternalTaskClient:
    settings = load_settings()
    authority_url = settings.processcube_authority_url
    engine_url = settings.processcube_engine_url
    client_name = settings.processcube_etw_client_id
    client_secret = settings.processcube_etw_client_secret
    client_scopes = settings.processcube_etw_client_scopes
    max_get_oauth_access_token_retries = (
        settings.processcube_max_get_oauth_access_token_retries
    )

    identity_provider = IdentityProvider(
        authority_url,
        client_name,
        client_secret,
        client_scopes,
        max_get_oauth_access_token_retries,
    )
    client = ExternalTaskClient(
        engine_url,
        identity=identity_provider,
        install_signals=False,
    )

    return client
