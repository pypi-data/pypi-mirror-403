"""Internal HTTP transport layer for the billing.io SDK.

Not part of the public API -- use :class:`billingio.BillingIO` instead.
"""

from __future__ import annotations

from typing import Any, Dict, Optional

import requests

from .errors import BillingIOError

_SDK_VERSION = "1.0.0"


class _HTTPClient:
    """Thin wrapper around :mod:`requests` that handles authentication,
    serialisation, and structured error responses.
    """

    def __init__(self, api_key: str, base_url: str) -> None:
        self._api_key = api_key
        self._base_url = base_url.rstrip("/")
        self._session = requests.Session()
        self._session.headers.update(
            {
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
                "Accept": "application/json",
                "User-Agent": f"billingio-python/{_SDK_VERSION}",
            }
        )

    # --------------------------------------------------------------------- #
    # Public helpers
    # --------------------------------------------------------------------- #

    def get(
        self,
        path: str,
        params: Optional[Dict[str, Any]] = None,
    ) -> Any:
        """Perform an authenticated GET request."""
        return self._request("GET", path, params=params)

    def post(
        self,
        path: str,
        json: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
    ) -> Any:
        """Perform an authenticated POST request."""
        return self._request("POST", path, json=json, extra_headers=headers)

    def delete(self, path: str) -> None:
        """Perform an authenticated DELETE request (expects 204 No Content)."""
        self._request("DELETE", path, expect_json=False)

    # --------------------------------------------------------------------- #
    # Internal
    # --------------------------------------------------------------------- #

    def _request(
        self,
        method: str,
        path: str,
        *,
        params: Optional[Dict[str, Any]] = None,
        json: Optional[Dict[str, Any]] = None,
        extra_headers: Optional[Dict[str, str]] = None,
        expect_json: bool = True,
    ) -> Any:
        url = f"{self._base_url}{path}"

        # Strip None values from query params so they are not sent as
        # literal ``None`` strings.
        if params:
            params = {k: v for k, v in params.items() if v is not None}

        headers = dict(extra_headers) if extra_headers else {}

        response = self._session.request(
            method,
            url,
            params=params,
            json=json,
            headers=headers,
        )

        if response.status_code >= 400:
            self._raise_for_error(response)

        if not expect_json or response.status_code == 204:
            return None

        return response.json()

    @staticmethod
    def _raise_for_error(response: requests.Response) -> None:
        """Parse a structured error response and raise :class:`BillingIOError`."""
        try:
            body = response.json()
            err = body.get("error", {})
            raise BillingIOError(
                err.get("message", response.text),
                type=err.get("type", "unknown_error"),
                code=err.get("code", "unknown"),
                status_code=response.status_code,
                param=err.get("param"),
            )
        except (ValueError, KeyError):
            raise BillingIOError(
                response.text or f"HTTP {response.status_code}",
                status_code=response.status_code,
            )
