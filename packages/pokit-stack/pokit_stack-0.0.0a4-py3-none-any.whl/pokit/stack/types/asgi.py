"""Type definitions relating to the ASGI specification.

Content in this file was derived from the Django reference implementation.
https://github.com/django/asgiref/blob/main/asgiref/typing.py

Copyright (c) Django Software Foundation and individual contributors.
All rights reserved.

Redistribution and use in source and binary forms, with or without modification,
are permitted provided that the following conditions are met:

    1. Redistributions of source code must retain the above copyright notice,
       this list of conditions and the following disclaimer.

    2. Redistributions in binary form must reproduce the above copyright
       notice, this list of conditions and the following disclaimer in the
       documentation and/or other materials provided with the distribution.

    3. Neither the name of Django nor the names of its contributors may be used
       to endorse or promote products derived from this software without
       specific prior written permission.

THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND
ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT OWNER OR CONTRIBUTORS BE LIABLE FOR
ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES
(INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON
ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
(INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
"""

from collections.abc import Awaitable, Callable, Iterable
from typing import (
    Any,
    Literal,
    NotRequired,
    Protocol,
    TypedDict,
)


class ASGIVersions(TypedDict):
    """
    Spec versions let you understand what the server you are using understands. If
    a server tells you it only supports version ``2.0`` of this spec, then
    sending ``headers`` with a WebSocket Accept message is an error, for example.

    They are separate from the HTTP version or the ASGI version.
    """

    spec_version: str
    """
    * ``asgi["spec_version"]`` (*Unicode string*) -- The version of this spec being
      used. Optional; if missing, assume ``"2.0"``.
    """

    version: Literal["2.0"] | Literal["3.0"]
    """
    * ``asgi["version"]`` (*Unicode string*) -- Version of the ASGI spec.
    """


class HTTPScope(TypedDict):
    """
    HTTP connections have a single-request *connection scope* - that is, your
    application will be called at the start of the request, and will last until
    the end of that specific request, even if the underlying socket is still open
    and serving multiple requests.

    If you hold a response open for long-polling or similar, the *connection scope*
    will persist until the response closes from either the client or server side.

    The *connection scope* information passed in ``scope`` contains:
    """

    type: Literal["http"]
    """
    * ``type`` (*Unicode string*) -- ``"http"``.
    """

    asgi: ASGIVersions
    """
    * ``asgi["version"]`` (*Unicode string*) -- Version of the ASGI spec.

    * ``asgi["spec_version"]`` (*Unicode string*) -- The version of this spec being
      used. Optional; if missing, assume ``"2.0"``.
    """

    http_version: str
    """
    * ``http_version`` (*Unicode string*) -- One of ``"1.0"``, ``"1.1"`` or ``"2"``.
    """

    method: str
    """
    * ``method`` (*Unicode string*) -- The HTTP method name, uppercased.
    """

    scheme: str
    """
    * ``scheme`` (*Unicode string*) -- URL scheme portion (likely ``"http"`` or
      ``"https"``). Optional (but must not be empty); default is ``"http"``.
    """

    path: str
    """
    * ``path`` (*Unicode string*) -- HTTP request target excluding any query
      string, with percent-encoded sequences and UTF-8 byte sequences
      decoded into characters.
    """

    raw_path: bytes
    """
    * ``raw_path`` (*byte string*) -- The original HTTP path component,
      excluding any query string, unmodified from the bytes that were
      received by the web server. Some web server implementations may
      be unable to provide this. Optional; if missing defaults to ``None``.
    """

    query_string: bytes
    """
    * ``query_string`` (*byte string*) -- URL portion after the ``?``,
      percent-encoded.
    """

    root_path: str
    """
    * ``root_path`` (*Unicode string*) -- The root path this application
      is mounted at; same as ``SCRIPT_NAME`` in WSGI. Optional; if missing
      defaults to ``""``.
    """

    headers: Iterable[tuple[bytes, bytes]]
    """
    * ``headers`` (*Iterable[[byte string, byte string]]*) -- An iterable of
      ``[name, value]`` two-item iterables, where ``name`` is the header name, and
      ``value`` is the header value. Order of header values must be preserved from
      the original HTTP request; order of header names is not important. Duplicates
      are possible and must be preserved in the message as received. Header names
      should be lowercased, but it is not required; servers should preserve header case
      on a best-effort basis. Pseudo headers (present in HTTP/2 and HTTP/3) must be
      removed; if ``:authority`` is present its value must be added to the start of
      the iterable with ``host`` as the header name or replace any existing host
      header already present.
    """

    client: tuple[str, int] | None
    """
    * ``client`` (*Iterable[Unicode string, int]*) -- A two-item iterable
      of ``[host, port]``, where ``host`` is the remote host's IPv4 or
      IPv6 address, and ``port`` is the remote port as an
      integer. Optional; if missing defaults to ``None``.
    """

    server: tuple[str, int | None] | None
    """
    * ``server`` (*Iterable[Unicode string, Optional[int]]*) -- Either a
      two-item iterable of ``[host, port]``, where ``host`` is the
      listening address for this server, and ``port`` is the integer
      listening port, or ``[path, None]`` where ``path`` is that of the
      unix socket. Optional; if missing defaults to ``None``.
    """

    state: NotRequired[dict[str, Any]]
    """
    * ``state`` Optional(*dict[Unicode string, Any]*) -- A copy of the
      namespace passed into the lifespan corresponding to this request.
      (See :doc:`lifespan`). Optional; if missing the server does not
      support this feature.

    Servers are responsible for handling inbound and outbound chunked transfer
    encodings. A request with a ``chunked`` encoded body should be automatically
    de-chunked by the server and presented to the application as plain body bytes;
    a response that is given to the server with no ``Content-Length`` may be chunked
    as the server sees fit.
    """

    extensions: dict[str, dict[object, object]] | None
    """
    Details about any extensions installed in the ASGI server.
    """


class WebSocketScope(TypedDict):
    """
    WebSocket connections' scope lives as long as the socket itself - if the
    application dies the socket should be closed, and vice-versa.

    The *connection scope* information passed in ``scope`` contains initial connection
    metadata (mostly from the HTTP request line and headers):
    """

    type: Literal["websocket"]
    """
    * ``type`` (*Unicode string*) -- ``"websocket"``.
    """

    asgi: ASGIVersions
    """
    * ``asgi["version"]`` (*Unicode string*) -- Version of the ASGI spec.

    * ``asgi["spec_version"]`` (*Unicode string*) -- The version of this spec being
      used. Optional; if missing, assume ``"2.0"``.
    """

    http_version: str
    """
    * ``http_version`` (*Unicode string*) -- One of ``"1.1"`` or
      ``"2"``. Optional; if missing default is ``"1.1"``.
    """

    scheme: str
    """
    * ``scheme`` (*Unicode string*) -- URL scheme portion (likely ``"ws"`` or
      ``"wss"``). Optional (but must not be empty); default is ``"ws"``.
    """

    path: str
    """
    * ``path`` (*Unicode string*) -- HTTP request target excluding any query
      string, with percent-encoded sequences and UTF-8 byte sequences
      decoded into characters.
    """

    raw_path: bytes
    """
    * ``raw_path`` (*byte string*) -- The original HTTP path component,
      excluding any query string, unmodified from the bytes that were
      received by the web server. Some web server implementations may
      be unable to provide this. Optional; if missing defaults to ``None``.
    """

    query_string: bytes
    """
    * ``query_string`` (*byte string*) -- URL portion after the
      ``?``. Optional; if missing or ``None`` default is empty string.
    """

    root_path: str
    """
    * ``root_path`` (*Unicode string*) -- The root path this application is
      mounted at; same as ``SCRIPT_NAME`` in WSGI. Optional; if missing
      defaults to empty string.
    """

    headers: Iterable[tuple[bytes, bytes]]
    """
    * ``headers`` (*Iterable[[byte string, byte string]]*) -- An iterable of
      ``[name, value]`` two-item iterables, where ``name`` is the header name and
      ``value`` is the header value. Order should be preserved from the original
      HTTP request; duplicates are possible and must be preserved in the message
      as received. Header names should be lowercased, but it is not required;
      servers should preserve header case on a best-effort basis.
      Pseudo headers (present in HTTP/2 and HTTP/3) must be removed;
      if ``:authority`` is present its value must be added to the
      start of the iterable with ``host`` as the header name
      or replace any existing host header already present.
    """

    client: tuple[str, int] | None
    """
    * ``client`` (*Iterable[Unicode string, int]*) -- A two-item iterable
      of ``[host, port]``, where ``host`` is the remote host's IPv4 or
      IPv6 address, and ``port`` is the remote port. Optional; if missing
      defaults to ``None``.
    """

    server: tuple[str, int | None] | None
    """
    * ``server`` (*Iterable[Unicode string, Optional[int]]*) -- Either a
      two-item iterable of ``[host, port]``, where ``host`` is the
      listening address for this server, and ``port`` is the integer
      listening port, or ``[path, None]`` where ``path`` is that of the
      unix socket. Optional; if missing defaults to ``None``.
    """

    subprotocols: Iterable[str]
    """
    * ``subprotocols`` (*Iterable[Unicode string]*) -- Subprotocols the
      client advertised. Optional; if missing defaults to empty list.
    """

    state: NotRequired[dict[str, Any]]
    """
    * ``state`` Optional(*dict[Unicode string, Any]*) -- A copy of the
      namespace passed into the lifespan corresponding to this request.
      (See :doc:`lifespan`). Optional; if missing the server does not
      support this feature.
    """

    extensions: dict[str, dict[object, object]] | None
    """
    Details about any extensions installed in the ASGI server.
    """


class LifespanScope(TypedDict):
    """
    The lifespan scope exists for the duration of the event loop.

    The scope information passed in ``scope`` contains basic metadata:
    """

    type: Literal["lifespan"]
    """
    * ``type`` (*Unicode string*) -- ``"lifespan"``.
    """

    asgi: ASGIVersions
    """
    * ``asgi["version"]`` (*Unicode string*) -- Version of the ASGI spec.

    * ``asgi["spec_version"]`` (*Unicode string*) -- The version of this spec being
      used. Optional; if missing, assume ``"2.0"``.
    """

    state: NotRequired[dict[str, Any]]
    """
    * ``state`` Optional(*dict[Unicode string, Any]*) -- An empty namespace where
      the application can persist state to be used when handling subsequent requests.
      Optional; if missing the server does not support this feature.
    """


ASGIScope = HTTPScope | WebSocketScope | LifespanScope
"""
Every connection by a user to an ASGI application results in a call of the
application callable to handle that connection entirely. How long this lives,
and the information that describes each specific connection, is called the
connection scope.

Closely related, the first argument passed to an application callable is a
scope dictionary with all the information describing that specific connection.

For example, under HTTP the connection scope lasts just one request, but the
scope passed contains most of the request data (apart from the HTTP request
body, as this is streamed in via events).

Under WebSocket, though, the connection scope lasts for as long as the socket
is connected. And the scope passed contains information like the WebSocket's
path, but details like incoming messages come through as events instead.

Some protocols may give you a scope with very limited information up front
because they encapsulate something like a handshake. Each protocol definition
must contain information about how long its connection scope lasts, and what
information you will get in the scope parameter.

Depending on the protocol spec, applications may have to wait for an initial
opening message before communicating with the client.
"""


class HTTPRequestEvent(TypedDict):
    """
    Sent to the application to indicate an incoming request. Most of the request
    information is in the connection ``scope``; the body message serves as a way to
    stream large incoming HTTP bodies in chunks, and as a trigger to actually run
    request code (as you should not trigger on a connection opening alone).

    Note that if the request is being sent using ``Transfer-Encoding: chunked``,
    the server is responsible for handling this encoding. The ``http.request``
    messages should contain just the decoded contents of each chunk.
    """

    type: Literal["http.request"]
    """
    * ``type`` (*Unicode string*) -- ``"http.request"``.
    """

    body: bytes
    """
    * ``body`` (*byte string*) -- Body of the request. Optional; if
      missing defaults to ``b""``. If ``more_body`` is set, treat as start
      of body and concatenate on further chunks.
    """

    more_body: bool
    """
    * ``more_body`` (*bool*) -- Signifies if there is additional content
      to come (as part of a Request message). If ``True``, the consuming
      application should wait until it gets a chunk with this set to
      ``False``. If ``False``, the request is complete and should be
      processed. Optional; if missing defaults to ``False``.
    """


class HTTPResponseDebugEvent(TypedDict):
    """
    The debug extension allows a way to send debug information from an ASGI
    framework in its responses. This extension is not meant to be used in
    production, only for testing purposes, and ASGI servers should not
    implement it.

    The ASGI context sent to the framework will provide ``http.response.debug``
    in the extensions part of the scope::

        "scope": {
            ...
            "extensions": {
                "http.response.debug": {},
            },
        }

    The ASGI framework can send debug information by sending a message with
    the following keys. This message must be sent once, before the
    *Response Start* message.
    """

    type: Literal["http.response.debug"]
    """
    * ``type`` (*Unicode string*): ``"http.response.debug"``
    """

    info: dict[str, object]
    """
    * ``info`` (*Dict[Unicode string, Any]*): A dictionary containing the
      debug information. The keys and values of this dictionary are not
      defined by the ASGI specification, and are left to the ASGI framework
      to define.
    """


class HTTPResponseStartEvent(TypedDict):
    """
    Sent by the application to start sending a response to the client. Needs to be
    followed by at least one response content message.

    Protocol servers *need not* flush the data generated by this event to the
    send buffer until the first *Response Body* event is processed.
    This may give them more leeway to replace the response with an error response
    in case internal errors occur while handling the request.

    You may send a ``Transfer-Encoding`` header in this message, but the server
    must ignore it. Servers handle ``Transfer-Encoding`` themselves, and may opt
    to use ``Transfer-Encoding: chunked`` if the application presents a response
    that has no ``Content-Length`` set.

    Note that this is not the same as ``Content-Encoding``, which the application
    still controls, and which is the appropriate place to set ``gzip`` or other
    compression flags.
    """

    type: Literal["http.response.start"]
    """
    * ``type`` (*Unicode string*) -- ``"http.response.start"``.
    """

    status: int
    """
    * ``status`` (*int*) -- HTTP status code.
    """

    headers: Iterable[tuple[bytes, bytes]]
    """
    * ``headers`` (*Iterable[[byte string, byte string]]*) -- An iterable
      of ``[name, value]`` two-item iterables, where ``name`` is the
      header name, and ``value`` is the header value. Order must be
      preserved in the HTTP response.  Header names must be
      lowercased. Optional; if missing defaults to an empty list. Pseudo
      headers (present in HTTP/2 and HTTP/3) must not be present.
    """

    trailers: bool
    """
    * ``trailers`` (*bool*) -- Signifies if the application will send
      trailers. If ``True``, the server must wait until it receives a
      ``"http.response.trailers"`` message after the *Response Body* event.
      Optional; if missing defaults to ``False``.
    """


class HTTPResponseBodyEvent(TypedDict):
    """
    Continues sending a response to the client. Protocol servers must
    flush any data passed to them into the send buffer before returning from a
    send call. If ``more_body`` is set to ``False``, and the server is not
    expecting *Response Trailers* this will complete the response.
    """

    type: Literal["http.response.body"]
    """
    * ``type`` (*Unicode string*) -- ``"http.response.body"``.
    """

    body: bytes
    """
    * ``body`` (*byte string*) -- HTTP body content. Concatenated onto any
      previous ``body`` values sent in this connection scope. Optional; if
      missing defaults to ``b""``.
    """

    more_body: bool
    """
    * ``more_body`` (*bool*) -- Signifies if there is additional content
      to come (as part of a *Response Body* message). If ``False``, and the
      server is not expecting *Response Trailers* response will be taken as
      complete and closed, and any further messages on the channel will be
      ignored. Optional; if missing defaults to ``False``.
    """


class HTTPResponseTrailersEvent(TypedDict):
    """
    The Trailer response header allows the sender to include additional fields at the
    end of chunked messages in order to supply metadata that might be dynamically
    generated while the message body is sent, such as a message integrity check,
    digital signature, or post-processing status.

    ASGI servers that implement this extension will provide
    ``http.response.trailers`` in the extensions part of the scope::

        "scope": {
            ...
            "extensions": {
                "http.response.trailers": {},
            },
        }

    An ASGI framework interested in sending trailing headers to the client,
    must set the field ``trailers`` in *Response Start* as ``True``. That
    will allow the ASGI server to know that after the last
    ``http.response.body`` message (``more_body`` being ``False``), the ASGI
    framework will send a ``http.response.trailers`` message.

    The ASGI framework is in charge of sending the ``Trailer`` headers to let
    the client know which trailing headers the server will send. The ASGI
    server is not responsible for validating the ``Trailer`` headers provided.
    """

    type: Literal["http.response.trailers"]
    """
    * ``type`` (*Unicode string*): ``"http.response.trailers"``
    """

    headers: Iterable[tuple[bytes, bytes]]
    """
    * ``headers`` (*Iterable[[byte string, byte string]]*): An iterable of
      ``[name, value]`` two-item iterables, where ``name`` is the header name, and
      ``value`` is the header value. Header names must be lowercased. Pseudo
      headers (present in HTTP/2 and HTTP/3) must not be present.
    """

    more_trailers: bool
    """
    * ``more_trailers`` (*bool*): Signifies if there is additional content
      to come (as part of a *HTTP Trailers* message). If ``False``, response
      will be taken as complete and closed, and any further messages on
      the channel will be ignored. Optional; if missing defaults to
      ``False``.

    The ASGI server will only send the trailing headers in case the client
    has sent the ``TE: trailers`` header in the request.
    """


class HTTPResponsePathsendEvent(TypedDict):
    """
    Path Send allows you to send the contents of a file path to the
    HTTP client without handling file descriptors, offloading the operation
    directly to the server.

    ASGI servers that implement this extension will provide
    ``http.response.pathsend`` in the extensions part of the scope::

        "scope": {
            ...
            "extensions": {
                "http.response.pathsend": {},
            },
        }

    The ASGI framework can initiate a path-send by sending a message with
    the following keys. This message can be sent at any time after the
    *Response Start* message, and cannot be mixed with ``http.response.body``.
    It can be called just one time in one response.
    Except for the characteristics of path-send, it should behave the same
    as ordinary ``http.response.body``.
    """

    type: Literal["http.response.pathsend"]
    """
    * ``type`` (*Unicode string*): ``"http.response.pathsend"``
    """

    path: str
    """
    * ``path`` (*Unicode string*): The string representation of the absolute
      file path to be sent by the server, platform specific.

    The ASGI application itself is responsible to send the relevant headers
    in the *Response Start* message, like the ``Content-Type`` and
    ``Content-Length`` headers for the file to be sent.
    """


class HTTPServerPushEvent(TypedDict):
    """
    HTTP/2 allows for a server to push a resource to a client by sending a
    push promise. ASGI servers that implement this extension will provide
    ``http.response.push`` in the extensions part of the scope::

        "scope": {
            ...
            "extensions": {
                "http.response.push": {},
            },
        }

    An ASGI framework can initiate a server push by sending a message with
    the following keys. This message can be sent at any time after the
    *Response Start* message but before the final *Response Body* message.
    """

    type: Literal["http.response.push"]
    """
    * ``type`` (*Unicode string*): ``"http.response.push"``
    """

    path: str
    """
    * ``path`` (*Unicode string*): HTTP path from URL, with percent-encoded
      sequences and UTF-8 byte sequences decoded into characters.
    """

    headers: Iterable[tuple[bytes, bytes]]
    """
    * ``headers`` (*Iterable[[byte string, byte string]]*): An iterable of
      ``[name, value]`` two-item iterables, where ``name`` is the header name,
      and ``value`` is the header value. Header names must be lowercased.
      Pseudo headers (present in HTTP/2 and HTTP/3) must not be present.

    The ASGI server should then attempt to send a server push (or push
    promise) to the client. If the client supports server push, the server
    should create a new connection to a new instance of the application
    and treat it as if the client had made a request.

    The ASGI server should set the pseudo ``:authority`` header value to
    be the same value as the request that triggered the push promise.
    """


class HTTPDisconnectEvent(TypedDict):
    """
    Sent to the application if receive is called after a response has been
    sent or after the HTTP connection has been closed. This is mainly useful
    for long-polling, where you may want to trigger cleanup code if the
    connection closes early.

    Once you have received this event, you should expect future calls to ``send()``
    to raise an exception, as described above. However, if you have highly
    concurrent code, you may find calls to ``send()`` erroring slightly before you
    receive this event.
    """

    type: Literal["http.disconnect"]
    """
    * ``type`` (*Unicode string*) -- ``"http.disconnect"``.
    """


class WebSocketConnectEvent(TypedDict):
    """
    Sent to the application when the client initially opens a connection and is about
    to finish the WebSocket handshake.

    This message must be responded to with either an *Accept* message
    or a *Close* message before the socket will pass ``websocket.receive``
    messages. The protocol server must send this message
    during the handshake phase of the WebSocket and not complete the handshake
    until it gets a reply, returning HTTP status code ``403`` if the connection is
    denied.
    """

    type: Literal["websocket.connect"]
    """
    * ``type`` (*Unicode string*) -- ``"websocket.connect"``.
    """


class WebSocketAcceptEvent(TypedDict):
    """
    Sent by the application when it wishes to accept an incoming connection.
    """

    type: Literal["websocket.accept"]
    """
    * ``type`` (*Unicode string*) -- ``"websocket.accept"``.
    """

    subprotocol: str | None
    """
    * ``subprotocol`` (*Unicode string*) -- The subprotocol the server
      wishes to accept. Optional; if missing defaults to ``None``.
    """

    headers: Iterable[tuple[bytes, bytes]]
    """
    * ``headers`` (*Iterable[[byte string, byte string]]*) -- An iterable
      of ``[name, value]`` two-item iterables, where ``name`` is the
      header name, and ``value`` is the header value. Order must be
      preserved in the HTTP response.  Header names must be
      lowercased. Must not include a header named
      ``sec-websocket-protocol``; use the ``subprotocol`` key
      instead. Optional; if missing defaults to an empty list. *Added in
      spec version 2.1*. Pseudo headers (present in HTTP/2 and HTTP/3)
      must not be present.
    """


class WebSocketReceiveEvent(TypedDict):
    """
    Sent to the application when a data message is received from the client.
    """

    type: Literal["websocket.receive"]
    """
    * ``type`` (*Unicode string*) -- ``"websocket.receive"``.
    """

    bytes: bytes | None
    """
    * ``bytes`` (*byte string*) -- The message content, if it was binary
      mode, or ``None``. Optional; if missing, it is equivalent to
      ``None``.
    """

    text: str | None
    """
    * ``text`` (*Unicode string*) -- The message content, if it was text
      mode, or ``None``. Optional; if missing, it is equivalent to
      ``None``.

    Exactly one of ``bytes`` or ``text`` must be non-``None``. One or both
    keys may be present, however.
    """


class WebSocketSendEvent(TypedDict):
    """
    Sent by the application to send a data message to the client.
    """

    type: Literal["websocket.send"]
    """
    * ``type`` (*Unicode string*) -- ``"websocket.send"``.
    """

    bytes: bytes | None
    """
    * ``bytes`` (*byte string*) -- Binary message content, or ``None``.
       Optional; if missing, it is equivalent to ``None``.

    Exactly one of ``bytes`` or ``text`` must be non-``None``. One or both
    keys may be present, however.
    """

    text: str | None
    """
    * ``text`` (*Unicode string*) -- Text message content, or ``None``.
       Optional; if missing, it is equivalent to ``None``.

    Exactly one of ``bytes`` or ``text`` must be non-``None``. One or both
    keys may be present, however.
    """


class WebSocketResponseStartEvent(TypedDict):
    """
    Websocket connections start with the client sending a HTTP request
    containing the appropriate upgrade headers. On receipt of this request
    a server can choose to either upgrade the connection or respond with an
    HTTP response (denying the upgrade). The core ASGI specification does
    not allow for any control over the denial response, instead specifying
    that the HTTP status code ``403`` should be returned, whereas this
    extension allows an ASGI framework to control the
    denial response. Rather than being a core part of
    ASGI, this is an extension for what is considered a niche feature as most
    clients do not utilise the denial response.

    ASGI Servers that implement this extension will provide
    ``websocket.http.response`` in the extensions part of the scope::

        "scope": {
            ...
            "extensions": {
                "websocket.http.response": {},
            },
        }

    This will allow the ASGI Framework to send HTTP response messages
    after the ``websocket.connect`` message. These messages cannot be
    followed by any other websocket messages as the server should send a
    HTTP response and then close the connection.

    The messages themselves should be ``websocket.http.response.start``
    and ``websocket.http.response.body`` with a structure that matches the
    ``http.response.start`` and ``http.response.body`` messages defined in
    the HTTP part of the core ASGI specification.
    """

    type: Literal["websocket.http.response.start"]
    """
    * ``type`` (*Unicode string*) -- ``"websocket.http.response.start"``.
    """

    status: int
    """
    * ``status`` (*int*) -- HTTP status code.
    """

    headers: Iterable[tuple[bytes, bytes]]
    """
    * ``headers`` (*Iterable[[byte string, byte string]]*) -- An iterable
      of ``[name, value]`` two-item iterables, where ``name`` is the
      header name, and ``value`` is the header value. Order must be
      preserved in the HTTP response.  Header names must be
      lowercased. Optional; if missing defaults to an empty list. Pseudo
      headers (present in HTTP/2 and HTTP/3) must not be present.
    """


class WebSocketResponseBodyEvent(TypedDict):
    """
    Websocket connections start with the client sending a HTTP request
    containing the appropriate upgrade headers. On receipt of this request
    a server can choose to either upgrade the connection or respond with an
    HTTP response (denying the upgrade). The core ASGI specification does
    not allow for any control over the denial response, instead specifying
    that the HTTP status code ``403`` should be returned, whereas this
    extension allows an ASGI framework to control the
    denial response. Rather than being a core part of
    ASGI, this is an extension for what is considered a niche feature as most
    clients do not utilise the denial response.

    ASGI Servers that implement this extension will provide
    ``websocket.http.response`` in the extensions part of the scope::

        "scope": {
            ...
            "extensions": {
                "websocket.http.response": {},
            },
        }

    This will allow the ASGI Framework to send HTTP response messages
    after the ``websocket.connect`` message. These messages cannot be
    followed by any other websocket messages as the server should send a
    HTTP response and then close the connection.

    The messages themselves should be ``websocket.http.response.start``
    and ``websocket.http.response.body`` with a structure that matches the
    ``http.response.start`` and ``http.response.body`` messages defined in
    the HTTP part of the core ASGI specification.
    """

    type: Literal["websocket.http.response.body"]
    """
    * ``type`` (*Unicode string*) -- ``"websocket.http.response.body"``.
    """

    body: bytes
    """
    * ``body`` (*byte string*) -- HTTP body content. Concatenated onto any
      previous ``body`` values sent in this connection scope. Optional; if
      missing defaults to ``b""``.
    """

    more_body: bool
    """
    * ``more_body`` (*bool*) -- Signifies if there is additional content
      to come (as part of a *Response Body* message). If ``False``, and the
      server is not expecting *Response Trailers* response will be taken as
      complete and closed, and any further messages on the channel will be
      ignored. Optional; if missing defaults to ``False``.
    """


class WebSocketDisconnectEvent(TypedDict):
    """
    Sent to the application when either connection to the client is lost, either from
    the client closing the connection, the server closing the connection, or loss of the
    socket.

    Once you have received this event, you should expect future calls to ``send()``
    to raise an exception, as described below. However, if you have highly
    concurrent code, you may find calls to ``send()`` erroring slightly before you
    receive this event.
    """

    type: Literal["websocket.disconnect"]
    """
    * ``type`` (*Unicode string*) -- ``"websocket.disconnect"``
    """

    code: int
    """
    * ``code`` (*int*) -- The WebSocket close code, as per the WebSocket
      spec. If no code was received in the frame from the client, the server
      should set this to ``1005`` (the default value in the WebSocket
      specification).
    """

    reason: str | None
    """
    * ``reason`` (*Unicode string*) -- A reason given for the disconnect, can
      be any string. Optional; if missing or ``None`` default is empty
      string.
    """


class WebSocketCloseEvent(TypedDict):
    """
    Sent by the application to tell the server to close the connection.

    If this is sent before the socket is accepted, the server
    must close the connection with a HTTP 403 error code
    (Forbidden), and not complete the WebSocket handshake; this may present on some
    browsers as a different WebSocket error code (such as 1006, Abnormal Closure).

    If this is sent after the socket is accepted, the server must close the socket
    with the close code passed in the message (or 1000 if none is specified).
    """

    type: Literal["websocket.close"]
    """
    * ``type`` (*Unicode string*) -- ``"websocket.close"``.
    """

    code: int
    """
    * ``code`` (*int*) -- The WebSocket close code, as per the WebSocket
      spec.  Optional; if missing defaults to ``1000``.
    """

    reason: str | None
    """
    * ``reason`` (*Unicode string*) -- A reason given for the closure, can
      be any string. Optional; if missing or ``None`` default is empty
      string.
    """


class LifespanStartupEvent(TypedDict):
    """
    Sent to the application when the server is ready to startup and receive connections,
    but before it has started to do so.
    """

    type: Literal["lifespan.startup"]
    """
    * ``type`` (*Unicode string*) -- ``"lifespan.startup"``.
    """


class LifespanShutdownEvent(TypedDict):
    """
    Sent to the application when the server has stopped accepting connections and closed
    all active connections.
    """

    type: Literal["lifespan.shutdown"]
    """
    * ``type`` (*Unicode string*) --  ``"lifespan.shutdown"``.
    """


class LifespanStartupCompleteEvent(TypedDict):
    """
    Sent by the application when it has completed its startup. A server
    must wait for this message before it starts processing connections.
    """

    type: Literal["lifespan.startup.complete"]
    """
    * ``type`` (*Unicode string*) -- ``"lifespan.startup.complete"``.
    """


class LifespanStartupFailedEvent(TypedDict):
    """
    Sent by the application when it has failed to complete its startup. If a server
    sees this it should log/print the message provided and then exit.
    """

    type: Literal["lifespan.startup.failed"]
    """
    * ``type`` (*Unicode string*) -- ``"lifespan.startup.failed"``.
    """

    message: str
    """
    * ``message`` (*Unicode string*) -- Optional; if missing defaults to ``""``.
    """


class LifespanShutdownCompleteEvent(TypedDict):
    """
    Sent by the application when it has completed its cleanup. A server
    must wait for this message before terminating.
    """

    type: Literal["lifespan.shutdown.complete"]
    """
    * ``type`` (*Unicode string*) -- ``"lifespan.shutdown.complete"``.
    """


class LifespanShutdownFailedEvent(TypedDict):
    """
    Sent by the application when it has failed to complete its cleanup. If a server
    sees this it should log/print the message provided and then terminate.
    """

    type: Literal["lifespan.shutdown.failed"]
    """
    * ``type`` (*Unicode string*) -- ``"lifespan.shutdown.failed"``.
    """

    message: str
    """
    * ``message`` (*Unicode string*) -- Optional; if missing defaults to ``""``.
    """


HTTPReceiveEvent = HTTPRequestEvent | HTTPDisconnectEvent

WebsocketReceiveEvent = (
    WebSocketConnectEvent | WebSocketReceiveEvent | WebSocketDisconnectEvent
)

LifespanReceiveEvent = LifespanStartupEvent | LifespanShutdownEvent

ASGIReceiveEvent = HTTPReceiveEvent | WebsocketReceiveEvent | LifespanReceiveEvent
"""
ASGI decomposes protocols into a series of *events* that an application must
*receive* and react to, and *events* the application might *send* in response.
For HTTP, this is as simple as *receiving* two events in order - ``http.request``
and ``http.disconnect``, and *sending* the corresponding event messages back. For
something like a WebSocket, it could be more like *receiving* ``websocket.connect``,
*sending* a ``websocket.send``, *receiving* a ``websocket.receive``, and finally
*receiving* a ``websocket.disconnect``.

Each event is a ``dict`` with a top-level ``type`` key that contains a
Unicode string of the message type. Users are free to invent their own message
types and send them between application instances for high-level events - for
example, a chat application might send chat messages with a user type of
``mychat.message``. It is expected that applications should be able to handle
a mixed set of events, some sourced from the incoming client connection and
some from other parts of the application.

Because these messages could be sent over a network, they need to be
serializable, and so they are only allowed to contain the following types:

* Byte strings
* Unicode strings
* Integers (within the signed 64-bit range)
* Floating point numbers (within the IEEE 754 double precision range; no
  ``Nan`` or infinities)
* Lists (tuples should be encoded as lists)
* Dicts (keys must be Unicode strings)
* Booleans
* ``None``
"""

HTTPSendEvent = (
    HTTPResponseStartEvent
    | HTTPResponseBodyEvent
    | HTTPResponseTrailersEvent
    | HTTPServerPushEvent
    | HTTPDisconnectEvent
)

WebsocketSendEvent = (
    WebSocketAcceptEvent
    | WebSocketSendEvent
    | WebSocketResponseStartEvent
    | WebSocketResponseBodyEvent
    | WebSocketCloseEvent
)

LifespanSendEvent = (
    LifespanStartupCompleteEvent
    | LifespanStartupFailedEvent
    | LifespanShutdownCompleteEvent
    | LifespanShutdownFailedEvent
)


ASGISendEvent = HTTPSendEvent | WebsocketSendEvent | LifespanSendEvent
"""
ASGI decomposes protocols into a series of *events* that an application must
*receive* and react to, and *events* the application might *send* in response.
For HTTP, this is as simple as *receiving* two events in order - ``http.request``
and ``http.disconnect``, and *sending* the corresponding event messages back. For
something like a WebSocket, it could be more like *receiving* ``websocket.connect``,
*sending* a ``websocket.send``, *receiving* a ``websocket.receive``, and finally
*receiving* a ``websocket.disconnect``.

Each event is a ``dict`` with a top-level ``type`` key that contains a
Unicode string of the message type. Users are free to invent their own message
types and send them between application instances for high-level events - for
example, a chat application might send chat messages with a user type of
``mychat.message``. It is expected that applications should be able to handle
a mixed set of events, some sourced from the incoming client connection and
some from other parts of the application.

Because these messages could be sent over a network, they need to be
serializable, and so they are only allowed to contain the following types:

* Byte strings
* Unicode strings
* Integers (within the signed 64-bit range)
* Floating point numbers (within the IEEE 754 double precision range; no
  ``Nan`` or infinities)
* Lists (tuples should be encoded as lists)
* Dicts (keys must be Unicode strings)
* Booleans
* ``None``
"""


ASGIReceiveCallable = Callable[[], Awaitable[ASGIReceiveEvent]]
ASGISendCallable = Callable[[ASGISendEvent], Awaitable[None]]


class ASGI2Protocol(Protocol):
    def __init__(self, scope: ASGIScope) -> None: ...

    async def __call__(
        self, receive: ASGIReceiveCallable, send: ASGISendCallable
    ) -> None: ...


ASGI2Application = type[ASGI2Protocol]
ASGI3Application = Callable[
    [
        ASGIScope,
        ASGIReceiveCallable,
        ASGISendCallable,
    ],
    Awaitable[None],
]
ASGIApplication = ASGI2Application | ASGI3Application
