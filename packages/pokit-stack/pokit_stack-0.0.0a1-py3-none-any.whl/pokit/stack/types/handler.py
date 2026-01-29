from typing import Protocol

from msgspec import Struct


class HandlerFn(Protocol):
    async def __call__(self, request: "RequestContext") -> str: ...


class RequestContext(Struct):
    """The context of a request."""

    path: str
    """The path of the request."""

    method: str
    """The HTTP method of the request."""

    query: dict[str, str]
    """The query parameters of the request."""

    headers: dict[str, str]
    """The headers of the request."""
