"""
Custom exceptions for the mcstatusio package.
"""

import httpx


class Error(httpx.RequestError):
    """Base exception for mcstatusio."""

    pass


class TimeoutException(httpx.TimeoutException):
    """Raised when a request times out."""

    pass


class ConnectionError(httpx.ConnectError):
    """Raised when a connection fails."""

    pass


class HTTPError(httpx.HTTPStatusError):
    """Raised when an HTTP error occurs."""

    pass
