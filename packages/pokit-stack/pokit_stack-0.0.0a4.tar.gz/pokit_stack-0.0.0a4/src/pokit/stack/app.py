from urllib.parse import parse_qs

from pokit.stack.types.asgi import (
    ASGIReceiveCallable,
    ASGIScope,
    ASGISendCallable,
    HTTPResponseBodyEvent,
    HTTPResponseStartEvent,
    HTTPScope,
)
from pokit.stack.types.handler import HandlerFn, RequestContext
from pokit.stack.types.http import HTTPHeader, HTTPStatus


class Stack:
    """The main application class."""

    _app_handler: HandlerFn

    def __init__(self, handler: HandlerFn):
        """Create a new Pokit Stack application."""

        self._app_handler = handler

    async def __call__(
        self,
        scope: ASGIScope,
        receive: ASGIReceiveCallable,
        send: ASGISendCallable,
    ):
        """ASGI endpoint.

        :param scope: The ASGI scope.
        :param receive: The ASGI receive data callable.
        :param send: The ASGI send data callable.
        :return:
        """

        assert scope["type"] == "http"

        request_ctx = self.create_request_ctx(scope)
        response = await self._app_handler(request=request_ctx)

        await self.send_str_response(response, send)

    @classmethod
    def create_request_ctx(cls, scope: HTTPScope) -> RequestContext:
        return RequestContext(
            path=scope["path"],
            method=scope["method"],
            query={
                k: v[0]
                for k, v in parse_qs(
                    scope["query_string"].decode(), keep_blank_values=True
                ).items()
            },
            headers={
                header_name.decode(): header_value.decode()
                for header_name, header_value in scope["headers"]
            },
        )

    @classmethod
    def encode_response_headers(
        cls, headers: dict[str, str]
    ) -> list[tuple[bytes, bytes]]:
        return [(k.encode(), v.encode()) for k, v in headers.items()]

    @classmethod
    async def send_str_response(cls, response: str, send: ASGISendCallable) -> None:
        bytes_response = response.encode()

        asgi_headers = cls.encode_response_headers(
            {
                HTTPHeader.CONTENT_TYPE: "text/plain",
                HTTPHeader.CONTENT_LENGTH: str(len(bytes_response)),
            }
        )

        await send(
            HTTPResponseStartEvent(
                type="http.response.start",
                status=HTTPStatus.OK_200,
                headers=asgi_headers,
                trailers=False,
            )
        )
        await send(
            HTTPResponseBodyEvent(
                type="http.response.body",
                body=bytes_response,
                more_body=False,
            )
        )
