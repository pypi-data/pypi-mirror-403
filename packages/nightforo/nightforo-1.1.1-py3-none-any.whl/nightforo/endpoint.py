"""Endpoint definitions for XenForo API."""

from enum import Enum
from typing import Any, Set


class HTTPMethod(Enum):
    GET = "GET"
    POST = "POST"
    PUT = "PUT"
    DELETE = "DELETE"
    PATCH = "PATCH"
    HEAD = "HEAD"
    OPTIONS = "OPTIONS"


class Endpoint:
    def __init__(
        self,
        url: str,
        supported_methods: Set[HTTPMethod],
    ) -> None:
        self.url = url
        self.supported_methods = supported_methods

    def __add__(self, other: Any):
        """Concatenate endpoint URL with a string.

        Args:
            other: String to append to the endpoint URL.

        Returns:
            The concatenated URL string, or NotImplemented if other is not a string.
        """
        if isinstance(other, str):
            return self.url + other
        else:
            return NotImplemented


def create_endpoint(url: str, *supported_methods: HTTPMethod):
    """Create an endpoint with supported HTTP methods.

    Args:
        url: The endpoint URL.
        supported_methods: Variable number of supported HTTP methods.

    Returns:
        An Endpoint instance.
    """
    return Endpoint(url=url, supported_methods=set(supported_methods))
