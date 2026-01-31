"""
Base client for ProcessCube® API handlers.

This module provides the base HTTP client functionality used by all handler classes.
"""

import json
import logging
from typing import Any, Callable, Dict, Optional, Protocol
from urllib.parse import urljoin

import requests


class IsDataclass(Protocol):
    """Protocol for dataclass type checking."""

    __dataclass_fields__: Dict


class BaseClient:
    """
    Base HTTP client for ProcessCube® API communication.

    This class provides low-level HTTP methods (GET, POST, PUT, DELETE) with
    automatic authentication header injection.

    Args:
        url: Base URL of the ProcessCube® Engine
        identity: Optional callable that returns identity dict with 'token' key
        api_version: API version to use (default: "v1")
    """

    def __init__(
        self,
        url: str,
        identity: Optional[Callable[[], Dict[str, str]]] = None,
        api_version: str = "v1",
    ):
        """
        Initialize the BaseClient.

        Args:
            url: Base URL of the ProcessCube® Engine (e.g., "http://localhost:56100")
            identity: Optional callable returning dict with 'token' key.
                     If None, uses default dummy token: ZHVtbXlfdG9rZW4=
            api_version: API version to use (default: "v1")
        """
        self._base_url = url.rstrip("/")
        self._api_version = api_version
        self.logger = logging.getLogger(__name__)

        if identity is not None:
            self._identity = identity
        else:
            # Default identity with dummy token from Swagger spec
            self._identity = lambda: {"token": "ZHVtbXlfdG9rZW4="}

    def _build_url(self, path: str) -> str:
        """
        Build the full API URL from a path.

        According to Swagger spec, the API is at:
        /atlas_engine/api/v1/...

        Args:
            path: API endpoint path (e.g., "process_models")

        Returns:
            Full URL to the API endpoint

        Example:
            >>> client._build_url("process_models")
            'http://localhost:56100/atlas_engine/api/v1/process_models'
        """
        # Remove leading slash from path
        path = path.lstrip("/")

        # Build API path according to Swagger spec
        api_path = f"atlas_engine/api/{self._api_version}/{path}"

        # Use urljoin for proper URL construction
        return urljoin(self._base_url + "/", api_path)

    def do_get(self, path: str, options: Optional[Dict] = None) -> Any:
        """
        Execute a GET request.

        Args:
            path: API endpoint path
            options: Optional request options (can contain 'headers')

        Returns:
            Parsed JSON response

        Raises:
            requests.HTTPError: On HTTP errors
        """
        options = options or {}
        headers = self._get_default_headers()
        headers.update(options.get("headers", {}))
        headers.update(self._get_auth_headers())

        request_url = self._build_url(path)

        self.logger.debug(f"GET {request_url}")
        response = requests.get(request_url, headers=headers)
        response.raise_for_status()

        return response.json()

    def do_delete(self, path: str, options: Optional[Dict] = None) -> None:
        """
        Execute a DELETE request.

        Args:
            path: API endpoint path
            options: Optional request options (can contain 'headers')

        Raises:
            requests.HTTPError: On HTTP errors
        """
        options = options or {}
        headers = self._get_default_headers()
        headers.update(options.get("headers", {}))
        headers.update(self._get_auth_headers())

        request_url = self._build_url(path)

        self.logger.debug(f"DELETE {request_url}")
        response = requests.delete(request_url, headers=headers)
        response.raise_for_status()

    def do_post(
        self, path: str, payload: IsDataclass, options: Optional[Dict] = None
    ) -> Any:
        """
        Execute a POST request.

        Args:
            path: API endpoint path
            payload: Dataclass payload to send
            options: Optional request options (can contain 'headers')

        Returns:
            Parsed JSON response if status is 200, empty dict otherwise

        Raises:
            requests.HTTPError: On HTTP errors
        """
        options = options or {}
        headers = self._get_default_headers()
        headers.update(options.get("headers", {}))
        headers.update(self._get_auth_headers())

        request_url = self._build_url(path)
        json_payload = json.dumps(payload)

        self.logger.debug(f"POST {request_url}")
        response = requests.post(request_url, json_payload, headers=headers)
        response.raise_for_status()

        if response.status_code == 200:
            return response.json()
        return {}

    def do_put(
        self, path: str, payload: IsDataclass, options: Optional[Dict] = None
    ) -> Any:
        """
        Execute a PUT request.

        Args:
            path: API endpoint path
            payload: Dataclass payload to send
            options: Optional request options (can contain 'headers')

        Returns:
            Parsed JSON response if status is 200, empty dict otherwise

        Raises:
            requests.HTTPError: On HTTP errors
        """
        options = options or {}
        headers = self._get_default_headers()
        headers.update(options.get("headers", {}))
        headers.update(self._get_auth_headers())

        request_url = self._build_url(path)
        json_payload = json.dumps(payload)

        self.logger.debug(f"PUT {request_url}")
        response = requests.put(request_url, json_payload, headers=headers)
        response.raise_for_status()

        if response.status_code == 200:
            return response.json()
        return {}

    def _get_auth_headers(self) -> Dict[str, str]:
        """
        Build authentication headers.

        Returns:
            Dict with Authorization header
        """
        identity = self._get_identity()
        token = identity["token"]
        return {"Authorization": f"Bearer {token}"}

    def _get_default_headers(self) -> Dict[str, str]:
        """
        Get default headers for all requests.

        Returns:
            Dict with default headers
        """
        return {"Content-Type": "application/json"}

    def _get_identity(self) -> Dict[str, str]:
        """
        Get the current identity.

        Returns:
            Identity dict with 'token' key
        """
        identity = self._identity

        if callable(self._identity):
            identity = self._identity()

        return identity


__all__ = ["BaseClient", "IsDataclass"]
