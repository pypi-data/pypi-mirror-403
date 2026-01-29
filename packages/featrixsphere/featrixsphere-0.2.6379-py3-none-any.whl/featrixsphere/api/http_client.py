"""
HTTP Client functionality for FeatrixSphere API.

This module provides the base HTTP client mixin that handles all
communication with the FeatrixSphere server.
"""

import time
import logging
import requests
from typing import Dict, Any, Optional, BinaryIO
from requests.exceptions import HTTPError, ConnectionError, Timeout

logger = logging.getLogger(__name__)


class HTTPClientMixin:
    """
    Mixin providing HTTP client functionality.

    Classes using this mixin must have:
        - self._session: requests.Session
        - self._base_url: str
        - self._default_max_retries: int
        - self._retry_base_delay: float
        - self._retry_max_delay: float
    """

    def _make_request(
        self,
        method: str,
        endpoint: str,
        max_retries: Optional[int] = None,
        max_retry_time: Optional[float] = None,
        **kwargs
    ) -> requests.Response:
        """
        Make an HTTP request with retry logic.

        Args:
            method: HTTP method (GET, POST, DELETE, etc.)
            endpoint: API endpoint (e.g., "/session/123/predict")
            max_retries: Maximum retry attempts
            max_retry_time: Maximum total retry time in seconds
            **kwargs: Additional arguments passed to requests

        Returns:
            Response object

        Raises:
            HTTPError: If request fails after retries
        """
        if max_retries is None:
            max_retries = self._default_max_retries

        # Auto-add /compute prefix for session endpoints
        if endpoint.startswith('/session/') and not endpoint.startswith('/compute/session/'):
            endpoint = f"/compute{endpoint}"

        # Special handling for upload endpoints
        is_upload = '/upload_with_new_session' in endpoint
        if is_upload:
            if 'timeout' not in kwargs:
                kwargs['timeout'] = 600  # 10 minutes for uploads
            if max_retry_time is None:
                max_retry_time = 600.0
        elif max_retry_time is None:
            max_retry_time = 120.0

        url = f"{self._base_url}{endpoint}"
        start_time = time.time()
        attempt = 0
        last_error = None

        while True:
            attempt += 1
            elapsed = time.time() - start_time

            try:
                response = self._session.request(method, url, **kwargs)
                response.raise_for_status()
                return response

            except HTTPError as e:
                last_error = e
                status_code = e.response.status_code if e.response is not None else None

                # Retry on certain status codes
                if status_code in (500, 502, 503, 504):
                    if attempt < max_retries and elapsed < max_retry_time:
                        delay = min(
                            self._retry_base_delay * (2 ** (attempt - 1)),
                            self._retry_max_delay
                        )
                        logger.warning(
                            f"HTTP {status_code} on {method} {endpoint}, "
                            f"retrying in {delay:.1f}s (attempt {attempt}/{max_retries})"
                        )
                        time.sleep(delay)
                        continue
                raise

            except (ConnectionError, Timeout) as e:
                last_error = e
                if attempt < max_retries and elapsed < max_retry_time:
                    delay = min(
                        self._retry_base_delay * (2 ** (attempt - 1)),
                        self._retry_max_delay
                    )
                    logger.warning(
                        f"Connection error on {method} {endpoint}, "
                        f"retrying in {delay:.1f}s (attempt {attempt}/{max_retries})"
                    )
                    time.sleep(delay)
                    continue
                raise

        # Should not reach here, but just in case
        if last_error:
            raise last_error

    def _unwrap_response(self, response_json: Dict[str, Any]) -> Dict[str, Any]:
        """
        Unwrap server response, handling the 'response' wrapper if present.

        The server sometimes wraps responses in {"response": {...}}.
        """
        if isinstance(response_json, dict) and 'response' in response_json and len(response_json) == 1:
            return response_json['response']
        return response_json

    def _get_json(
        self,
        endpoint: str,
        max_retries: Optional[int] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """Make a GET request and return JSON response."""
        response = self._make_request("GET", endpoint, max_retries=max_retries, **kwargs)
        return self._unwrap_response(response.json())

    def _post_json(
        self,
        endpoint: str,
        data: Optional[Dict[str, Any]] = None,
        max_retries: Optional[int] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """Make a POST request with JSON data and return JSON response."""
        if data is not None:
            kwargs['json'] = data
        response = self._make_request("POST", endpoint, max_retries=max_retries, **kwargs)
        return self._unwrap_response(response.json())

    def _delete_json(
        self,
        endpoint: str,
        max_retries: Optional[int] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """Make a DELETE request and return JSON response."""
        response = self._make_request("DELETE", endpoint, max_retries=max_retries, **kwargs)
        return self._unwrap_response(response.json())

    def _post_multipart(
        self,
        endpoint: str,
        data: Optional[Dict[str, Any]] = None,
        files: Optional[Dict[str, Any]] = None,
        max_retries: Optional[int] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """Make a POST request with multipart/form-data and return JSON response."""
        response = self._make_request(
            "POST", endpoint,
            data=data, files=files,
            max_retries=max_retries,
            **kwargs
        )
        return self._unwrap_response(response.json())


class ClientContext:
    """
    Context object passed to resource classes to access HTTP client.

    This allows resource classes (FoundationalModel, Predictor, etc.) to
    make API calls without directly inheriting from the main client.
    """

    def __init__(self, client: 'HTTPClientMixin'):
        self._client = client

    @property
    def base_url(self) -> str:
        return self._client._base_url

    def get_json(self, endpoint: str, **kwargs) -> Dict[str, Any]:
        return self._client._get_json(endpoint, **kwargs)

    def post_json(self, endpoint: str, data: Dict[str, Any] = None, **kwargs) -> Dict[str, Any]:
        return self._client._post_json(endpoint, data, **kwargs)

    def delete_json(self, endpoint: str, **kwargs) -> Dict[str, Any]:
        return self._client._delete_json(endpoint, **kwargs)

    def post_multipart(self, endpoint: str, data: Dict[str, Any] = None,
                       files: Dict[str, Any] = None, **kwargs) -> Dict[str, Any]:
        return self._client._post_multipart(endpoint, data, files, **kwargs)
