from __future__ import annotations
from typing import Optional


class OnDemandError(Exception):
    """
    Base exception for all OnDemand SDK errors.
    """


class ConfigurationError(OnDemandError):
    """
    Raised for invalid or missing configuration.
    """


class HTTPError(OnDemandError):
    """
    Raised for non-2xx HTTP responses.

    Attributes:
        status_code: HTTP status code
        body: Raw response body
        request_id: Optional request ID if provided by server
    """

    def __init__(
        self,
        status_code: int,
        body: str,
        request_id: Optional[str] = None,
    ):
        self.status_code = status_code
        self.body = body
        self.request_id = request_id

        msg = f"HTTP {status_code}"
        if request_id:
            msg += f" (request_id={request_id})"

        super().__init__(msg)
