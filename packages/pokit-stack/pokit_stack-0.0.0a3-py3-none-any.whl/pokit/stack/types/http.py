"""Enumerations related to HTTP.

Documentation in this file derived from `MDN Web Docs`_ by Mozilla Contributors, licensed under `CC-BY-SA 2.5`_.

.. _MDN Web Docs: https://developer.mozilla.org/en-US/docs/Web/HTTP/
.. _CC-BY-SA 2.5: https://creativecommons.org/licenses/by-sa/2.5/
"""

from enum import Enum


class HTTPMethod(str, Enum):
    """An enumeration of HTTP request methods.

    See https://developer.mozilla.org/en-US/docs/Web/HTTP/Reference/Methods.
    """

    GET = "GET"
    """
    The ``GET`` method requests a representation of the specified resource. Requests using ``GET``
    should only retrieve data and should not contain a request `content`_ .

    .. _content: https://developer.mozilla.org/en-US/docs/Glossary/HTTP_Content

    `MDN Docs <https://developer.mozilla.org/en-US/docs/Web/HTTP/Reference/Methods/GET>`_
    """

    HEAD = "HEAD"
    """
    The ``HEAD`` method asks for a response identical to a ``GET`` request, but without a response body.

    `MDN Docs <https://developer.mozilla.org/en-US/docs/Web/HTTP/Reference/Methods/HEAD>`_
    """

    POST = "POST"
    """
    The ``POST`` method submits an entity to the specified resource, often causing a change in state or
    side effects on the server.

    `MDN Docs <https://developer.mozilla.org/en-US/docs/Web/HTTP/Reference/Methods/POST>`_
    """

    PUT = "PUT"
    """
    The ``PUT`` method replaces all current representations of the target resource with the request
    `content`_ .

    .. _content: https://developer.mozilla.org/en-US/docs/Glossary/HTTP_Content

    `MDN Docs <https://developer.mozilla.org/en-US/docs/Web/HTTP/Reference/Methods/PUT>`_
    """

    DELETE = "DELETE"
    """
    The ``DELETE`` method deletes the specified resource.

    `MDN Docs <https://developer.mozilla.org/en-US/docs/Web/HTTP/Reference/Methods/DELETE>`_
    """

    CONNECT = "CONNECT"
    """
    The ``CONNECT`` method establishes a tunnel to the server identified by the target resource.

    `MDN Docs <https://developer.mozilla.org/en-US/docs/Web/HTTP/Reference/Methods/CONNECT>`_
    """

    OPTIONS = "OPTIONS"
    """
    The ``OPTIONS`` method describes the communication options for the target resource.

    `MDN Docs <https://developer.mozilla.org/en-US/docs/Web/HTTP/Reference/Methods/OPTIONS>`_
    """

    TRACE = "TRACE"
    """
    The ``TRACE`` method performs a message loop-back test along the path to the target resource.

    `MDN Docs <https://developer.mozilla.org/en-US/docs/Web/HTTP/Reference/Methods/TRACE>`_
    """

    PATCH = "PATCH"
    """
    The ``PATCH`` method applies partial modifications to a resource.

    `MDN Docs <https://developer.mozilla.org/en-US/docs/Web/HTTP/Reference/Methods/PATCH>`_
    """


class HTTPStatus(int, Enum):
    """An enumeration of HTTP status codes.

    See https://developer.mozilla.org/en-US/docs/Web/HTTP/Reference/Status.
    """

    CONTINUE_100 = 100
    """
    This interim response indicates that the client should continue the request or ignore the
    response if the request is already finished.

    `MDN Docs <https://developer.mozilla.org/en-US/docs/Web/HTTP/Reference/Status/100>`_
    """

    SWITCHING_PROTOCOLS_101 = 101
    """
    This code is sent in response to an `Upgrade`_ request header from the client and indicates the
    protocol the server is switching to.

    .. _Upgrade: https://developer.mozilla.org/en-US/docs/Web/HTTP/Reference/Headers/Upgrade

    `MDN Docs <https://developer.mozilla.org/en-US/docs/Web/HTTP/Reference/Status/101>`_
    """

    PROCESSING_DEPRECATED_102 = 102
    """
    This code was used in `WebDAV`_ contexts to indicate that a request has been received by the
    server, but no status was available at the time of the response.

    .. _WebDAV: https://developer.mozilla.org/en-US/docs/Glossary/WebDAV

    `MDN Docs <https://developer.mozilla.org/en-US/docs/Web/HTTP/Reference/Status/102>`_
    """

    EARLY_HINTS_103 = 103
    """
    This status code is primarily intended to be used with the `Link`_ header, letting the user
    agent start `preloading`_ resources while the server prepares a response or `preconnect`_ to an
    origin from which the page will need resources.

    .. _Link: https://developer.mozilla.org/en-US/docs/Web/HTTP/Reference/Headers/Link
    .. _preconnect: https://developer.mozilla.org/en-US/docs/Web/HTML/Reference/Attributes/rel/preconnect
    .. _preloading: https://developer.mozilla.org/en-US/docs/Web/HTML/Reference/Attributes/rel/preload

    `MDN Docs <https://developer.mozilla.org/en-US/docs/Web/HTTP/Reference/Status/103>`_
    """

    OK_200 = 200
    """
    The request succeeded. The result and meaning of "success" depends on the HTTP method:

    - `GET`_: The resource has been fetched and transmitted in the message body.
    - `HEAD`_: Representation headers are included in the response without any message body.
    - `PUT`_ or `POST`_: The resource describing the result of the action is transmitted in the message body.
    - `TRACE`_: The message body contains the request as received by the server.

    .. _GET: https://developer.mozilla.org/en-US/docs/Web/HTTP/Reference/Methods/GET
    .. _HEAD: https://developer.mozilla.org/en-US/docs/Web/HTTP/Reference/Methods/HEAD
    .. _POST: https://developer.mozilla.org/en-US/docs/Web/HTTP/Reference/Methods/POST
    .. _PUT: https://developer.mozilla.org/en-US/docs/Web/HTTP/Reference/Methods/PUT
    .. _TRACE: https://developer.mozilla.org/en-US/docs/Web/HTTP/Reference/Methods/TRACE

    `MDN Docs <https://developer.mozilla.org/en-US/docs/Web/HTTP/Reference/Status/200>`_
    """

    CREATED_201 = 201
    """
    The request succeeded, and a new resource was created as a result. This is typically the
    response sent after `POST`_ requests, or some `PUT`_ requests.

    .. _POST: https://developer.mozilla.org/en-US/docs/Web/HTTP/Reference/Methods/POST
    .. _PUT: https://developer.mozilla.org/en-US/docs/Web/HTTP/Reference/Methods/PUT

    `MDN Docs <https://developer.mozilla.org/en-US/docs/Web/HTTP/Reference/Status/201>`_
    """

    ACCEPTED_202 = 202
    """
    The request has been received but not yet acted upon. It is noncommittal, since there is no way
    in HTTP to later send an asynchronous response indicating the outcome of the request. It is
    intended for cases where another process or server handles the request, or for batch processing.

    `MDN Docs <https://developer.mozilla.org/en-US/docs/Web/HTTP/Reference/Status/202>`_
    """

    NON_AUTHORITATIVE_INFORMATION_203 = 203
    """
    This response code means the returned metadata is not exactly the same as is available from the
    origin server, but is collected from a local or a third-party copy. This is mostly used for
    mirrors or backups of another resource. Except for that specific case, the `200 OK`_ response is
    preferred to this status.

    .. _200 OK: https://developer.mozilla.org/en-US/docs/Web/HTTP/Reference/Status/200

    `MDN Docs <https://developer.mozilla.org/en-US/docs/Web/HTTP/Reference/Status/203>`_
    """

    NO_CONTENT_204 = 204
    """
    There is no content to send for this request, but the headers are useful. The user agent may
    update its cached headers for this resource with the new ones.

    `MDN Docs <https://developer.mozilla.org/en-US/docs/Web/HTTP/Reference/Status/204>`_
    """

    RESET_CONTENT_205 = 205
    """
    Tells the user agent to reset the document which sent this request.

    `MDN Docs <https://developer.mozilla.org/en-US/docs/Web/HTTP/Reference/Status/205>`_
    """

    PARTIAL_CONTENT_206 = 206
    """
    This response code is used in response to a `range request`_ when the client has requested a
    part or parts of a resource.

    .. _range request: https://developer.mozilla.org/en-US/docs/Web/HTTP/Guides/Range_requests

    `MDN Docs <https://developer.mozilla.org/en-US/docs/Web/HTTP/Reference/Status/206>`_
    """

    MULTI_STATUS_207 = 207
    """
    Conveys information about multiple resources, for situations where multiple status codes might
    be appropriate.

    `MDN Docs <https://developer.mozilla.org/en-US/docs/Web/HTTP/Reference/Status/207>`_
    """

    ALREADY_REPORTED_208 = 208
    """
    Used inside a ``<dav:propstat>`` response element to avoid repeatedly enumerating the internal
    members of multiple bindings to the same collection.

    `MDN Docs <https://developer.mozilla.org/en-US/docs/Web/HTTP/Reference/Status/208>`_
    """

    IM_USED_HTTP_DELTA_ENCODING_226 = 226
    """
    The server has fulfilled a `GET`_ request for the resource, and the response is a representation
    of the result of one or more instance-manipulations applied to the current instance.

    .. _GET: https://developer.mozilla.org/en-US/docs/Web/HTTP/Reference/Methods/GET

    `MDN Docs <https://developer.mozilla.org/en-US/docs/Web/HTTP/Reference/Status/226>`_
    """

    MULTIPLE_CHOICES_300 = 300
    """
    In `agent-driven content negotiation`_, the request has more than one possible response and the
    user agent or user should choose one of them. There is no standardized way for clients to
    automatically choose one of the responses, so this is rarely used.

    .. _agent-driven content negotiation: 
        https://developer.mozilla.org/en-US/docs/Web/HTTP/Guides/Content_negotiation#agent-driven_negotiation

    `MDN Docs <https://developer.mozilla.org/en-US/docs/Web/HTTP/Reference/Status/300>`_
    """

    MOVED_PERMANENTLY_301 = 301
    """
    The URL of the requested resource has been changed permanently. The new URL is given in the
    response.

    `MDN Docs <https://developer.mozilla.org/en-US/docs/Web/HTTP/Reference/Status/301>`_
    """

    FOUND_302 = 302
    """
    This response code means that the URI of requested resource has been changed temporarily.
    Further changes in the URI might be made in the future, so the same URI should be used by the
    client in future requests.

    `MDN Docs <https://developer.mozilla.org/en-US/docs/Web/HTTP/Reference/Status/302>`_
    """

    SEE_OTHER_303 = 303
    """
    The server sent this response to direct the client to get the requested resource at another URI
    with a `GET`_ request.

    .. _GET: https://developer.mozilla.org/en-US/docs/Web/HTTP/Reference/Methods/GET

    `MDN Docs <https://developer.mozilla.org/en-US/docs/Web/HTTP/Reference/Status/303>`_
    """

    NOT_MODIFIED_304 = 304
    """
    This is used for caching purposes. It tells the client that the response has not been modified,
    so the client can continue to use the same `cached`_ version of the response.

    .. _cached: https://developer.mozilla.org/en-US/docs/Web/HTTP/Guides/Caching

    `MDN Docs <https://developer.mozilla.org/en-US/docs/Web/HTTP/Reference/Status/304>`_
    """

    USE_PROXY_DEPRECATED_305 = 305
    """
    Defined in a previous version of the HTTP specification to indicate that a requested response
    must be accessed by a proxy. It has been deprecated due to security concerns regarding in-band
    configuration of a proxy.

    `MDN Docs <https://developer.mozilla.org/en-US/docs/Web/HTTP/Reference/Status#305_use_proxy>`_
    """

    UNUSED_306 = 306
    """
    This response code is no longer used; but is reserved. It was used in a previous version of the
    HTTP/1.1 specification.

    `MDN Docs <https://developer.mozilla.org/en-US/docs/Web/HTTP/Reference/Status#306_unused>`_
    """

    TEMPORARY_REDIRECT_307 = 307
    """
    The server sends this response to direct the client to get the requested resource at another URI
    with the same method that was used in the prior request. This has the same semantics as the
    ``302 Found`` response code, with the exception that the user agent must not change the HTTP
    method used: if a `POST`_ was used in the first request, a ``POST`` must be used in the
    redirected request.

    .. _POST: https://developer.mozilla.org/en-US/docs/Web/HTTP/Reference/Methods/POST

    `MDN Docs <https://developer.mozilla.org/en-US/docs/Web/HTTP/Reference/Status/307>`_
    """

    PERMANENT_REDIRECT_308 = 308
    """
    This means that the resource is now permanently located at another URI, specified by the
    `Location`_ response header. This has the same semantics as the ``301 Moved Permanently`` HTTP
    response code, with the exception that the user agent must not change the HTTP method used: if a
    `POST`_ was used in the first request, a ``POST`` must be used in the second request.

    .. _Location: https://developer.mozilla.org/en-US/docs/Web/HTTP/Reference/Headers/Location
    .. _POST: https://developer.mozilla.org/en-US/docs/Web/HTTP/Reference/Methods/POST

    `MDN Docs <https://developer.mozilla.org/en-US/docs/Web/HTTP/Reference/Status/308>`_
    """

    BAD_REQUEST_400 = 400
    """
    The server cannot or will not process the request due to something that is perceived to be a
    client error (e.g., malformed request syntax, invalid request message framing, or deceptive
    request routing).

    `MDN Docs <https://developer.mozilla.org/en-US/docs/Web/HTTP/Reference/Status/400>`_
    """

    UNAUTHORIZED_401 = 401
    """
    Although the HTTP standard specifies "unauthorized", semantically this response means
    "unauthenticated". That is, the client must authenticate itself to get the requested response.

    `MDN Docs <https://developer.mozilla.org/en-US/docs/Web/HTTP/Reference/Status/401>`_
    """

    PAYMENT_REQUIRED_402 = 402
    """
    The initial purpose of this code was for digital payment systems, however this status code is
    rarely used and no standard convention exists.

    `MDN Docs <https://developer.mozilla.org/en-US/docs/Web/HTTP/Reference/Status/402>`_
    """

    FORBIDDEN_403 = 403
    """
    The client does not have access rights to the content; that is, it is unauthorized, so the
    server is refusing to give the requested resource. Unlike ``401 Unauthorized``, the client's
    identity is known to the server.

    `MDN Docs <https://developer.mozilla.org/en-US/docs/Web/HTTP/Reference/Status/403>`_
    """

    NOT_FOUND_404 = 404
    """
    The server cannot find the requested resource. In the browser, this means the URL is not
    recognized. In an API, this can also mean that the endpoint is valid but the resource itself
    does not exist. Servers may also send this response instead of ``403 Forbidden`` to hide the
    existence of a resource from an unauthorized client. This response code is probably the most
    well known due to its frequent occurrence on the web.

    `MDN Docs <https://developer.mozilla.org/en-US/docs/Web/HTTP/Reference/Status/404>`_
    """

    METHOD_NOT_ALLOWED_405 = 405
    """
    The `request method`_ is known by the server but is not supported by the target resource. For
    example, an API may not allow ``DELETE`` on a resource, or the ``TRACE`` method entirely.

    .. _request method: https://developer.mozilla.org/en-US/docs/Web/HTTP/Reference/Methods

    `MDN Docs <https://developer.mozilla.org/en-US/docs/Web/HTTP/Reference/Status/405>`_
    """

    NOT_ACCEPTABLE_406 = 406
    """
    This response is sent when the web server, after performing `server-driven content
    negotiation`_, doesn't find any content that conforms to the criteria given by the user agent.

    .. _server-driven content negotiation: 
        https://developer.mozilla.org/en-US/docs/Web/HTTP/Guides/Content_negotiation#server-driven_content_negotiation

    `MDN Docs <https://developer.mozilla.org/en-US/docs/Web/HTTP/Reference/Status/406>`_
    """

    PROXY_AUTHENTICATION_REQUIRED_407 = 407
    """
    This is similar to ``401 Unauthorized`` but authentication is needed to be done by a proxy.

    `MDN Docs <https://developer.mozilla.org/en-US/docs/Web/HTTP/Reference/Status/407>`_
    """

    REQUEST_TIMEOUT_408 = 408
    """
    This response is sent on an idle connection by some servers, even without any previous request
    by the client. It means that the server would like to shut down this unused connection. This
    response is used much more since some browsers use HTTP pre-connection mechanisms to speed up
    browsing. Some servers may shut down a connection without sending this message.

    `MDN Docs <https://developer.mozilla.org/en-US/docs/Web/HTTP/Reference/Status/408>`_
    """

    CONFLICT_409 = 409
    """
    This response is sent when a request conflicts with the current state of the server. In
    `WebDAV`_ remote web authoring, ``409`` responses are errors sent to the client so that a user
    might be able to resolve a conflict and resubmit the request.

    .. _WebDAV: https://developer.mozilla.org/en-US/docs/Glossary/WebDAV

    `MDN Docs <https://developer.mozilla.org/en-US/docs/Web/HTTP/Reference/Status/409>`_
    """

    GONE_410 = 410
    """
    This response is sent when the requested content has been permanently deleted from server, with
    no forwarding address. Clients are expected to remove their caches and links to the resource.
    The HTTP specification intends this status code to be used for "limited-time, promotional
    services". APIs should not feel compelled to indicate resources that have been deleted with this
    status code.

    `MDN Docs <https://developer.mozilla.org/en-US/docs/Web/HTTP/Reference/Status/410>`_
    """

    LENGTH_REQUIRED_411 = 411
    """
    Server rejected the request because the `Content-Length`_ header field is not defined and the
    server requires it.

    .. _Content-Length: https://developer.mozilla.org/en-US/docs/Web/HTTP/Reference/Headers/Content-Length

    `MDN Docs <https://developer.mozilla.org/en-US/docs/Web/HTTP/Reference/Status/411>`_
    """

    PRECONDITION_FAILED_412 = 412
    """
    In `conditional requests`_, the client has indicated preconditions in its headers which the
    server does not meet.

    .. _conditional requests: https://developer.mozilla.org/en-US/docs/Web/HTTP/Guides/Conditional_requests

    `MDN Docs <https://developer.mozilla.org/en-US/docs/Web/HTTP/Reference/Status/412>`_
    """

    CONTENT_TOO_LARGE_413 = 413
    """
    The request body is larger than limits defined by server. The server might close the connection
    or return a `Retry-After`_ header field.

    .. _Retry-After: https://developer.mozilla.org/en-US/docs/Web/HTTP/Reference/Headers/Retry-After

    `MDN Docs <https://developer.mozilla.org/en-US/docs/Web/HTTP/Reference/Status/413>`_
    """

    URI_TOO_LONG_414 = 414
    """
    The URI requested by the client is longer than the server is willing to interpret.

    `MDN Docs <https://developer.mozilla.org/en-US/docs/Web/HTTP/Reference/Status/414>`_
    """

    UNSUPPORTED_MEDIA_TYPE_415 = 415
    """
    The media format of the requested data is not supported by the server, so the server is
    rejecting the request.

    `MDN Docs <https://developer.mozilla.org/en-US/docs/Web/HTTP/Reference/Status/415>`_
    """

    RANGE_NOT_SATISFIABLE_416 = 416
    """
    The `ranges`_ specified by the ``Range`` header field in the request cannot be fulfilled. It's
    possible that the range is outside the size of the target resource's data.

    .. _ranges: https://developer.mozilla.org/en-US/docs/Web/HTTP/Guides/Range_requests

    `MDN Docs <https://developer.mozilla.org/en-US/docs/Web/HTTP/Reference/Status/416>`_
    """

    EXPECTATION_FAILED_417 = 417
    """
    This response code means the expectation indicated by the `Expect`_ request header field cannot
    be met by the server.

    .. _Expect: https://developer.mozilla.org/en-US/docs/Web/HTTP/Reference/Headers/Expect

    `MDN Docs <https://developer.mozilla.org/en-US/docs/Web/HTTP/Reference/Status/417>`_
    """

    IM_A_TEAPOT_418 = 418
    """
    The server refuses the attempt to brew coffee with a teapot.

    `MDN Docs <https://developer.mozilla.org/en-US/docs/Web/HTTP/Reference/Status/418>`_
    """

    MISDIRECTED_REQUEST_421 = 421
    """
    The request was directed at a server that is not able to produce a response. This can be sent by
    a server that is not configured to produce responses for the combination of scheme and authority
    that are included in the request URI.

    `MDN Docs <https://developer.mozilla.org/en-US/docs/Web/HTTP/Reference/Status/421>`_
    """

    UNPROCESSABLE_CONTENT_422 = 422
    """
    The request was well-formed but was unable to be followed due to semantic errors.

    `MDN Docs <https://developer.mozilla.org/en-US/docs/Web/HTTP/Reference/Status/422>`_
    """

    LOCKED_423 = 423
    """
    The resource that is being accessed is locked.

    `MDN Docs <https://developer.mozilla.org/en-US/docs/Web/HTTP/Reference/Status/423>`_
    """

    FAILED_DEPENDENCY_424 = 424
    """
    The request failed due to failure of a previous request.

    `MDN Docs <https://developer.mozilla.org/en-US/docs/Web/HTTP/Reference/Status/424>`_
    """

    TOO_EARLY_425 = 425
    """
    Indicates that the server is unwilling to risk processing a request that might be replayed.

    `MDN Docs <https://developer.mozilla.org/en-US/docs/Web/HTTP/Reference/Status/425>`_
    """

    UPGRADE_REQUIRED_426 = 426
    """
    The server refuses to perform the request using the current protocol but might be willing to do
    so after the client upgrades to a different protocol. The server sends an `Upgrade`_ header in a
    426 response to indicate the required protocol(s).

    .. _Upgrade: https://developer.mozilla.org/en-US/docs/Web/HTTP/Reference/Headers/Upgrade

    `MDN Docs <https://developer.mozilla.org/en-US/docs/Web/HTTP/Reference/Status/426>`_
    """

    PRECONDITION_REQUIRED_428 = 428
    """
    The origin server requires the request to be `conditional`_. This response is intended to
    prevent the 'lost update' problem, where a client `GET`_s a resource's state, modifies it and
    `PUT`_s it back to the server, when meanwhile a third party has modified the state on the
    server, leading to a conflict.

    .. _conditional: https://developer.mozilla.org/en-US/docs/Web/HTTP/Guides/Conditional_requests
    .. _GET: https://developer.mozilla.org/en-US/docs/Web/HTTP/Reference/Methods/GET
    .. _PUT: https://developer.mozilla.org/en-US/docs/Web/HTTP/Reference/Methods/PUT

    `MDN Docs <https://developer.mozilla.org/en-US/docs/Web/HTTP/Reference/Status/428>`_
    """

    TOO_MANY_REQUESTS_429 = 429
    """
    The user has sent too many requests in a given amount of time (`rate limiting`_).

    .. _rate limiting: https://developer.mozilla.org/en-US/docs/Glossary/Rate_limit

    `MDN Docs <https://developer.mozilla.org/en-US/docs/Web/HTTP/Reference/Status/429>`_
    """

    REQUEST_HEADER_FIELDS_TOO_LARGE_431 = 431
    """
    The server is unwilling to process the request because its header fields are too large. The
    request may be resubmitted after reducing the size of the request header fields.

    `MDN Docs <https://developer.mozilla.org/en-US/docs/Web/HTTP/Reference/Status/431>`_
    """

    UNAVAILABLE_FOR_LEGAL_REASONS_451 = 451
    """
    The user agent requested a resource that cannot legally be provided, such as a web page censored
    by a government.

    `MDN Docs <https://developer.mozilla.org/en-US/docs/Web/HTTP/Reference/Status/451>`_
    """

    INTERNAL_SERVER_ERROR_500 = 500
    """
    The server has encountered a situation it does not know how to handle. This error is generic,
    indicating that the server cannot find a more appropriate ``5XX`` status code to respond with.

    `MDN Docs <https://developer.mozilla.org/en-US/docs/Web/HTTP/Reference/Status/500>`_
    """

    NOT_IMPLEMENTED_501 = 501
    """
    The request method is not supported by the server and cannot be handled. The only methods that
    servers are required to support (and therefore must not return this code) are `GET`_ and
    `HEAD`_.

    .. _GET: https://developer.mozilla.org/en-US/docs/Web/HTTP/Reference/Methods/GET
    .. _HEAD: https://developer.mozilla.org/en-US/docs/Web/HTTP/Reference/Methods/HEAD

    `MDN Docs <https://developer.mozilla.org/en-US/docs/Web/HTTP/Reference/Status/501>`_
    """

    BAD_GATEWAY_502 = 502
    """
    This error response means that the server, while working as a gateway to get a response needed
    to handle the request, got an invalid response.

    `MDN Docs <https://developer.mozilla.org/en-US/docs/Web/HTTP/Reference/Status/502>`_
    """

    SERVICE_UNAVAILABLE_503 = 503
    """
    The server is not ready to handle the request. Common causes are a server that is down for
    maintenance or that is overloaded. Note that together with this response, a user-friendly page
    explaining the problem should be sent. This response should be used for temporary conditions and
    the `Retry-After`_ HTTP header should, if possible, contain the estimated time before the
    recovery of the service. The webmaster must also take care about the caching-related headers
    that are sent along with this response, as these temporary condition responses should usually
    not be cached.

    .. _Retry-After: https://developer.mozilla.org/en-US/docs/Web/HTTP/Reference/Headers/Retry-After

    `MDN Docs <https://developer.mozilla.org/en-US/docs/Web/HTTP/Reference/Status/503>`_
    """

    GATEWAY_TIMEOUT_504 = 504
    """
    This error response is given when the server is acting as a gateway and cannot get a response in
    time.

    `MDN Docs <https://developer.mozilla.org/en-US/docs/Web/HTTP/Reference/Status/504>`_
    """

    HTTP_VERSION_NOT_SUPPORTED_505 = 505
    """
    The HTTP version used in the request is not supported by the server.

    `MDN Docs <https://developer.mozilla.org/en-US/docs/Web/HTTP/Reference/Status/505>`_
    """

    VARIANT_ALSO_NEGOTIATES_506 = 506
    """
    The server has an internal configuration error: during content negotiation, the chosen variant
    is configured to engage in content negotiation itself, which results in circular references when
    creating responses.

    `MDN Docs <https://developer.mozilla.org/en-US/docs/Web/HTTP/Reference/Status/506>`_
    """

    INSUFFICIENT_STORAGE_507 = 507
    """
    The method could not be performed on the resource because the server is unable to store the
    representation needed to successfully complete the request.

    `MDN Docs <https://developer.mozilla.org/en-US/docs/Web/HTTP/Reference/Status/507>`_
    """

    LOOP_DETECTED_508 = 508
    """
    The server detected an infinite loop while processing the request.

    `MDN Docs <https://developer.mozilla.org/en-US/docs/Web/HTTP/Reference/Status/508>`_
    """

    NOT_EXTENDED_510 = 510
    """
    The client request declares an HTTP Extension (`RFC 2774`_) that should be used to process the
    request, but the extension is not supported.

    .. _RFC 2774: https://datatracker.ietf.org/doc/html/rfc2774

    `MDN Docs <https://developer.mozilla.org/en-US/docs/Web/HTTP/Reference/Status/510>`_
    """

    NETWORK_AUTHENTICATION_REQUIRED_511 = 511
    """
    Indicates that the client needs to authenticate to gain network access.

    `MDN Docs <https://developer.mozilla.org/en-US/docs/Web/HTTP/Reference/Status/511>`_
    """


class HTTPHeader(str, Enum):
    """Common HTTP header names.

    https://developer.mozilla.org/en-US/docs/Web/HTTP/Reference/Headers
    """

    ACCEPT = "accept"
    """
    Informs the server about the `types`_ of data that can be sent back.

    .. _types: https://developer.mozilla.org/en-US/docs/Glossary/MIME_type

    `MDN Docs <https://developer.mozilla.org/en-US/docs/Web/HTTP/Reference/Headers/Accept>`_
    """

    ACCEPT_CH = "accept-ch"
    """
    Servers can advertise support for Client Hints using the ``Accept-CH`` header field or
    an equivalent HTML ``<meta>`` element with `http-equiv`_ attribute.

    .. _http-equiv: https://developer.mozilla.org/en-US/docs/Web/HTML/Reference/Elements/meta/http-equiv

    `MDN Docs <https://developer.mozilla.org/en-US/docs/Web/HTTP/Reference/Headers/Accept-CH>`_
    """

    ACCEPT_ENCODING = "accept-encoding"
    """
    The encoding algorithm, usually a `compression algorithm`_ , that can be used on the
    resource sent back.

    .. _compression algorithm: https://developer.mozilla.org/en-US/docs/Web/HTTP/Guides/Compression

    `MDN Docs <https://developer.mozilla.org/en-US/docs/Web/HTTP/Reference/Headers/Accept-Encoding>`_
    """

    ACCEPT_LANGUAGE = "accept-language"
    """
    Informs the server about the human language the server is expected to send back. This is
    a hint and is not necessarily under the full control of the user: the server should
    always pay attention not to override an explicit user choice (like selecting a language
    from a dropdown).

    `MDN Docs <https://developer.mozilla.org/en-US/docs/Web/HTTP/Reference/Headers/Accept-Language>`_
    """

    ACCEPT_PATCH = "accept-patch"
    """
    A request content negotiation response header that advertises which `media type`_ the
    server is able to understand in a `PATCH`_ request.

    .. _media type: https://developer.mozilla.org/en-US/docs/Web/HTTP/Guides/MIME_types
    .. _PATCH: https://developer.mozilla.org/en-US/docs/Web/HTTP/Reference/Methods/PATCH

    `MDN Docs <https://developer.mozilla.org/en-US/docs/Web/HTTP/Reference/Headers/Accept-Patch>`_
    """

    ACCEPT_POST = "accept-post"
    """
    A request content negotiation response header that advertises which `media type`_ the
    server is able to understand in a `POST`_ request.

    .. _media type: https://developer.mozilla.org/en-US/docs/Web/HTTP/Guides/MIME_types
    .. _POST: https://developer.mozilla.org/en-US/docs/Web/HTTP/Reference/Methods/POST

    `MDN Docs <https://developer.mozilla.org/en-US/docs/Web/HTTP/Reference/Headers/Accept-Post>`_
    """

    ACCEPT_RANGES = "accept-ranges"
    """
    Indicates if the server supports range requests, and if so in which unit the range can
    be expressed.

    `MDN Docs <https://developer.mozilla.org/en-US/docs/Web/HTTP/Reference/Headers/Accept-Ranges>`_
    """

    ACCESS_CONTROL_ALLOW_CREDENTIALS = "access-control-allow-credentials"
    """
    Indicates whether the response to the request can be exposed when the credentials flag
    is true.

    `MDN Docs <https://developer.mozilla.org/en-US/docs/Web/HTTP/Reference/Headers/Access-Control-Allow-Credentials>`_
    """

    ACCESS_CONTROL_ALLOW_HEADERS = "access-control-allow-headers"
    """
    Used in response to a `preflight request`_ to indicate which HTTP headers can be used
    when making the actual request.

    .. _preflight request: https://developer.mozilla.org/en-US/docs/Glossary/Preflight_request

    `MDN Docs <https://developer.mozilla.org/en-US/docs/Web/HTTP/Reference/Headers/Access-Control-Allow-Headers>`_
    """

    ACCESS_CONTROL_ALLOW_METHODS = "access-control-allow-methods"
    """
    Specifies the methods allowed when accessing the resource in response to a preflight
    request.

    `MDN Docs <https://developer.mozilla.org/en-US/docs/Web/HTTP/Reference/Headers/Access-Control-Allow-Methods>`_
    """

    ACCESS_CONTROL_ALLOW_ORIGIN = "access-control-allow-origin"
    """
    Indicates whether the response can be shared.

    `MDN Docs <https://developer.mozilla.org/en-US/docs/Web/HTTP/Reference/Headers/Access-Control-Allow-Origin>`_
    """

    ACCESS_CONTROL_EXPOSE_HEADERS = "access-control-expose-headers"
    """
    Indicates which headers can be exposed as part of the response by listing their names.

    `MDN Docs <https://developer.mozilla.org/en-US/docs/Web/HTTP/Reference/Headers/Access-Control-Expose-Headers>`_
    """

    ACCESS_CONTROL_MAX_AGE = "access-control-max-age"
    """
    Indicates how long the results of a preflight request can be cached.

    `MDN Docs <https://developer.mozilla.org/en-US/docs/Web/HTTP/Reference/Headers/Access-Control-Max-Age>`_
    """

    ACCESS_CONTROL_REQUEST_HEADERS = "access-control-request-headers"
    """
    Used when issuing a preflight request to let the server know which HTTP headers will be
    used when the actual request is made.

    `MDN Docs <https://developer.mozilla.org/en-US/docs/Web/HTTP/Reference/Headers/Access-Control-Request-Headers>`_
    """

    ACCESS_CONTROL_REQUEST_METHOD = "access-control-request-method"
    """
    Used when issuing a preflight request to let the server know which `HTTP method`_ will
    be used when the actual request is made.

    .. _HTTP method: https://developer.mozilla.org/en-US/docs/Web/HTTP/Reference/Methods

    `MDN Docs <https://developer.mozilla.org/en-US/docs/Web/HTTP/Reference/Headers/Access-Control-Request-Method>`_
    """

    ACTIVATE_STORAGE_ACCESS = "activate-storage-access"
    """
    Used in response to ``Sec-Fetch-Storage-Access`` to indicate that the browser can
    activate an existing permission for secure access and retry the request with cookies, or
    load a resource with cookie access if it already has an activated permission.

    `MDN Docs <https://developer.mozilla.org/en-US/docs/Web/HTTP/Reference/Headers/Activate-Storage-Access>`_
    """

    AGE = "age"
    """
    The time, in seconds, that the object has been in a proxy cache.

    `MDN Docs <https://developer.mozilla.org/en-US/docs/Web/HTTP/Reference/Headers/Age>`_
    """

    ALLOW = "allow"
    """
    Lists the set of HTTP request methods supported by a resource.

    `MDN Docs <https://developer.mozilla.org/en-US/docs/Web/HTTP/Reference/Headers/Allow>`_
    """

    ALT_SVC = "alt-svc"
    """
    Used to list alternate ways to reach this service.

    `MDN Docs <https://developer.mozilla.org/en-US/docs/Web/HTTP/Reference/Headers/Alt-Svc>`_
    """

    ALT_USED = "alt-used"
    """
    Used to identify the alternative service in use.

    `MDN Docs <https://developer.mozilla.org/en-US/docs/Web/HTTP/Reference/Headers/Alt-Used>`_
    """

    ATTRIBUTION_REPORTING_ELIGIBLE = "attribution-reporting-eligible"
    """
    Used to indicate that the response corresponding to the current request is eligible to
    take part in attribution reporting, by registering either an attribution source or
    trigger.

    `MDN Docs <https://developer.mozilla.org/en-US/docs/Web/HTTP/Reference/Headers/Attribution-Reporting-Eligible>`_
    """

    ATTRIBUTION_REPORTING_REGISTER_SOURCE = "attribution-reporting-register-source"
    """
    Included as part of a response to a request that included an ``Attribution-Reporting-
    Eligible`` header, this is used to register an attribution source.

    `MDN Docs <https://developer.mozilla.org/en-US/docs/Web/HTTP/Reference/Headers/Attribution-Reporting-Register-Source>`_
    """

    ATTRIBUTION_REPORTING_REGISTER_TRIGGER = "attribution-reporting-register-trigger"
    """
    Included as part of a response to a request that included an ``Attribution-Reporting-
    Eligible`` header, this is used to register an attribution trigger.

    `MDN Docs <https://developer.mozilla.org/en-US/docs/Web/HTTP/Reference/Headers/Attribution-Reporting-Register-Trigger>`_
    """

    AUTHORIZATION = "authorization"
    """
    Contains the credentials to authenticate a user-agent with a server.

    `MDN Docs <https://developer.mozilla.org/en-US/docs/Web/HTTP/Reference/Headers/Authorization>`_
    """

    AVAILABLE_DICTIONARY = "available-dictionary"
    """
    A browser can use this request header to indicate the best dictionary it has available
    for the server to use for compression.

    `MDN Docs <https://developer.mozilla.org/en-US/docs/Web/HTTP/Reference/Headers/Available-Dictionary>`_
    """

    CACHE_CONTROL = "cache-control"
    """
    Directives for caching mechanisms in both requests and responses.

    `MDN Docs <https://developer.mozilla.org/en-US/docs/Web/HTTP/Reference/Headers/Cache-Control>`_
    """

    CLEAR_SITE_DATA = "clear-site-data"
    """
    Clears browsing data (e.g., cookies, storage, cache) associated with the requesting
    website.

    `MDN Docs <https://developer.mozilla.org/en-US/docs/Web/HTTP/Reference/Headers/Clear-Site-Data>`_
    """

    CONNECTION = "connection"
    """
    Controls whether the network connection stays open after the current transaction
    finishes.

    `MDN Docs <https://developer.mozilla.org/en-US/docs/Web/HTTP/Reference/Headers/Connection>`_
    """

    CONTENT_DIGEST = "content-digest"
    """
    Provides a `digest`_ of the stream of octets framed in an HTTP message (the message
    content) dependent on `Content-Encoding`_ and `Content-Range`_ .

    .. _digest: https://developer.mozilla.org/en-US/docs/Glossary/Hash_function
    .. _Content-Encoding: https://developer.mozilla.org/en-US/docs/Web/HTTP/Reference/Headers/Content-Encoding
    .. _Content-Range: https://developer.mozilla.org/en-US/docs/Web/HTTP/Reference/Headers/Content-Range

    `MDN Docs <https://developer.mozilla.org/en-US/docs/Web/HTTP/Reference/Headers/Content-Digest>`_
    """

    CONTENT_DISPOSITION = "content-disposition"
    """
    Indicates if the resource transmitted should be displayed inline (default behavior
    without the header), or if it should be handled like a download and the browser should
    present a "Save As" dialog.

    `MDN Docs <https://developer.mozilla.org/en-US/docs/Web/HTTP/Reference/Headers/Content-Disposition>`_
    """

    CONTENT_ENCODING = "content-encoding"
    """
    Used to specify the compression algorithm.

    `MDN Docs <https://developer.mozilla.org/en-US/docs/Web/HTTP/Reference/Headers/Content-Encoding>`_
    """

    CONTENT_LANGUAGE = "content-language"
    """
    Describes the human language(s) intended for the audience, so that it allows a user to
    differentiate according to the users' own preferred language.

    `MDN Docs <https://developer.mozilla.org/en-US/docs/Web/HTTP/Reference/Headers/Content-Language>`_
    """

    CONTENT_LENGTH = "content-length"
    """
    The size of the resource, in decimal number of bytes.

    `MDN Docs <https://developer.mozilla.org/en-US/docs/Web/HTTP/Reference/Headers/Content-Length>`_
    """

    CONTENT_LOCATION = "content-location"
    """
    Indicates an alternate location for the returned data.

    `MDN Docs <https://developer.mozilla.org/en-US/docs/Web/HTTP/Reference/Headers/Content-Location>`_
    """

    CONTENT_RANGE = "content-range"
    """
    Indicates where in a full body message a partial message belongs.

    `MDN Docs <https://developer.mozilla.org/en-US/docs/Web/HTTP/Reference/Headers/Content-Range>`_
    """

    CONTENT_SECURITY_POLICY = "content-security-policy"
    """
    Controls resources the user agent is allowed to load for a given page.

    `MDN Docs <https://developer.mozilla.org/en-US/docs/Web/HTTP/Reference/Headers/Content-Security-Policy>`_
    """

    CONTENT_SECURITY_POLICY_REPORT_ONLY = "content-security-policy-report-only"
    """
    Allows web developers to experiment with policies by monitoring, but not enforcing,
    their effects. These violation reports consist of `JSON`_ documents sent via an HTTP
    ``POST`` request to the specified URI.

    .. _JSON: https://developer.mozilla.org/en-US/docs/Glossary/JSON

    `MDN Docs <https://developer.mozilla.org/en-US/docs/Web/HTTP/Reference/Headers/Content-Security-Policy-Report-Only>`_
    """

    CONTENT_TYPE = "content-type"
    """
    Indicates the media type of the resource.

    `MDN Docs <https://developer.mozilla.org/en-US/docs/Web/HTTP/Reference/Headers/Content-Type>`_
    """

    COOKIE = "cookie"
    """
    Contains stored `HTTP cookies`_ previously sent by the server with the `Set-Cookie`_
    header.

    .. _HTTP cookies: https://developer.mozilla.org/en-US/docs/Web/HTTP/Guides/Cookies
    .. _Set-Cookie: https://developer.mozilla.org/en-US/docs/Web/HTTP/Reference/Headers/Set-Cookie

    `MDN Docs <https://developer.mozilla.org/en-US/docs/Web/HTTP/Reference/Headers/Cookie>`_
    """

    CRITICAL_CH = "critical-ch"
    """
    Servers use ``Critical-CH`` along with `Accept-CH`_ to specify that accepted client
    hints are also `critical client hints`_ .

    .. _Accept-CH: https://developer.mozilla.org/en-US/docs/Web/HTTP/Reference/Headers/Accept-CH
    .. _critical client hints: https://developer.mozilla.org/en-US/docs/Web/HTTP/Guides/Client_hints#critical_client_hints

    `MDN Docs <https://developer.mozilla.org/en-US/docs/Web/HTTP/Reference/Headers/Critical-CH>`_
    """

    CROSS_ORIGIN_EMBEDDER_POLICY = "cross-origin-embedder-policy"
    """
    Allows a server to declare an embedder policy for a given document.

    `MDN Docs <https://developer.mozilla.org/en-US/docs/Web/HTTP/Reference/Headers/Cross-Origin-Embedder-Policy>`_
    """

    CROSS_ORIGIN_OPENER_POLICY = "cross-origin-opener-policy"
    """
    Prevents other domains from opening/controlling a window.

    `MDN Docs <https://developer.mozilla.org/en-US/docs/Web/HTTP/Reference/Headers/Cross-Origin-Opener-Policy>`_
    """

    CROSS_ORIGIN_RESOURCE_POLICY = "cross-origin-resource-policy"
    """
    Prevents other domains from reading the response of the resources to which this header
    is applied. See also `CORP explainer article`_ .

    .. _CORP explainer article: https://developer.mozilla.org/en-US/docs/Web/HTTP/Guides/Cross-Origin_Resource_Policy

    `MDN Docs <https://developer.mozilla.org/en-US/docs/Web/HTTP/Reference/Headers/Cross-Origin-Resource-Policy>`_
    """

    DATE = "date"
    """
    Contains the date and time at which the message was originated.

    `MDN Docs <https://developer.mozilla.org/en-US/docs/Web/HTTP/Reference/Headers/Date>`_
    """

    DEVICE_MEMORY = "device-memory"
    """
    Standardized as `Sec-CH-Device-Memory`_

    .. _Sec-CH-Device-Memory: https://developer.mozilla.org/en-US/docs/Web/HTTP/Reference/Headers/Sec-CH-Device-Memory

    `MDN Docs <https://developer.mozilla.org/en-US/docs/Web/HTTP/Reference/Headers/Device-Memory>`_
    """

    DICTIONARY_ID = "dictionary-id"
    """
    Used when a browser already has a dictionary available for a resource and the server
    provided an ``id`` for the dictionary in the ``Use-As-Dictionary`` header. Requests for
    resources that can use the dictionary have an ``Available-Dictionary`` header and the
    server-provided dictionary ``id`` in the ``Dictionary-ID`` header.

    `MDN Docs <https://developer.mozilla.org/en-US/docs/Web/HTTP/Reference/Headers/Dictionary-ID>`_
    """

    DNT = "dnt"
    """
    Request header that indicates the user's tracking preference (Do Not Track). Deprecated
    in favor of Global Privacy Control (GPC), which is communicated to servers using the
    `Sec-GPC`_ header, and accessible to clients via `navigator.globalPrivacyControl`_ .

    .. _Sec-GPC: https://developer.mozilla.org/en-US/docs/Web/HTTP/Reference/Headers/Sec-GPC
    .. _navigator.globalPrivacyControl: https://developer.mozilla.org/en-US/docs/Web/API/Navigator/globalPrivacyControl

    `MDN Docs <https://developer.mozilla.org/en-US/docs/Web/HTTP/Reference/Headers/DNT>`_
    """

    DOWNLINK = "downlink"
    """
    Approximate bandwidth of the client's connection to the server, in Mbps. This is part of
    the `Network Information API`_ .

    .. _Network Information API: https://developer.mozilla.org/en-US/docs/Web/API/Network_Information_API

    `MDN Docs <https://developer.mozilla.org/en-US/docs/Web/HTTP/Reference/Headers/Downlink>`_
    """

    DPR = "dpr"
    """
    Standardized as `Sec-CH-DPR`_

    .. _Sec-CH-DPR: https://developer.mozilla.org/en-US/docs/Web/HTTP/Reference/Headers/Sec-CH-DPR

    `MDN Docs <https://developer.mozilla.org/en-US/docs/Web/HTTP/Reference/Headers/DPR>`_
    """

    ECT = "ect"
    """
    The `effective connection type`_ ("network profile") that best matches the connection's
    latency and bandwidth. This is part of the `Network Information API`_ .

    .. _effective connection type: https://developer.mozilla.org/en-US/docs/Glossary/Effective_connection_type
    .. _Network Information API: https://developer.mozilla.org/en-US/docs/Web/API/Network_Information_API

    `MDN Docs <https://developer.mozilla.org/en-US/docs/Web/HTTP/Reference/Headers/ECT>`_
    """

    ETAG = "etag"
    """
    A unique string identifying the version of the resource. Conditional requests using `If-
    Match`_ and `If-None-Match`_ use this value to change the behavior of the request.

    .. _If-Match: https://developer.mozilla.org/en-US/docs/Web/HTTP/Reference/Headers/If-Match
    .. _If-None-Match: https://developer.mozilla.org/en-US/docs/Web/HTTP/Reference/Headers/If-None-Match

    `MDN Docs <https://developer.mozilla.org/en-US/docs/Web/HTTP/Reference/Headers/ETag>`_
    """

    EXPECT = "expect"
    """
    Indicates expectations that need to be fulfilled by the server to properly handle the
    request.

    `MDN Docs <https://developer.mozilla.org/en-US/docs/Web/HTTP/Reference/Headers/Expect>`_
    """

    EXPECT_CT = "expect-ct"
    """
    Lets sites opt in to reporting and enforcement of `Certificate Transparency`_ to detect
    use of misissued certificates for that site.

    .. _Certificate Transparency: https://developer.mozilla.org/en-US/docs/Web/Security/Defenses/Certificate_Transparency

    `MDN Docs <https://developer.mozilla.org/en-US/docs/Web/HTTP/Reference/Headers/Expect-CT>`_
    """

    EXPIRES = "expires"
    """
    The date/time after which the response is considered stale.

    `MDN Docs <https://developer.mozilla.org/en-US/docs/Web/HTTP/Reference/Headers/Expires>`_
    """

    FORWARDED = "forwarded"
    """
    Contains information from the client-facing side of proxy servers that is altered or
    lost when a proxy is involved in the path of the request.

    `MDN Docs <https://developer.mozilla.org/en-US/docs/Web/HTTP/Reference/Headers/Forwarded>`_
    """

    FROM = "from"
    """
    Contains an Internet email address for a human user who controls the requesting user
    agent.

    `MDN Docs <https://developer.mozilla.org/en-US/docs/Web/HTTP/Reference/Headers/From>`_
    """

    HOST = "host"
    """
    Specifies the domain name of the server (for virtual hosting), and (optionally) the TCP
    port number on which the server is listening.

    `MDN Docs <https://developer.mozilla.org/en-US/docs/Web/HTTP/Reference/Headers/Host>`_
    """

    IF_MATCH = "if-match"
    """
    Makes the request conditional, and applies the method only if the stored resource
    matches one of the given ETags.

    `MDN Docs <https://developer.mozilla.org/en-US/docs/Web/HTTP/Reference/Headers/If-Match>`_
    """

    IF_MODIFIED_SINCE = "if-modified-since"
    """
    Makes the request conditional, and expects the resource to be transmitted only if it has
    been modified after the given date. This is used to transmit data only when the cache is
    out of date.

    `MDN Docs <https://developer.mozilla.org/en-US/docs/Web/HTTP/Reference/Headers/If-Modified-Since>`_
    """

    IF_NONE_MATCH = "if-none-match"
    """
    Makes the request conditional, and applies the method only if the stored resource
    doesn't match any of the given ETags. This is used to update caches (for safe requests),
    or to prevent uploading a new resource when one already exists.

    `MDN Docs <https://developer.mozilla.org/en-US/docs/Web/HTTP/Reference/Headers/If-None-Match>`_
    """

    IF_RANGE = "if-range"
    """
    Creates a conditional range request that is only fulfilled if the given etag or date
    matches the remote resource. Used to prevent downloading two ranges from incompatible
    version of the resource.

    `MDN Docs <https://developer.mozilla.org/en-US/docs/Web/HTTP/Reference/Headers/If-Range>`_
    """

    IF_UNMODIFIED_SINCE = "if-unmodified-since"
    """
    Makes the request conditional, and expects the resource to be transmitted only if it has
    not been modified after the given date. This ensures the coherence of a new fragment of
    a specific range with previous ones, or to implement an optimistic concurrency control
    system when modifying existing documents.

    `MDN Docs <https://developer.mozilla.org/en-US/docs/Web/HTTP/Reference/Headers/If-Unmodified-Since>`_
    """

    INTEGRITY_POLICY = "integrity-policy"
    """
    Ensures that all resources the user agent loads (of a certain type) have `Subresource
    Integrity`_ guarantees.

    .. _Subresource Integrity: https://developer.mozilla.org/en-US/docs/Web/Security/Defenses/Subresource_Integrity

    `MDN Docs <https://developer.mozilla.org/en-US/docs/Web/HTTP/Reference/Headers/Integrity-Policy>`_
    """

    INTEGRITY_POLICY_REPORT_ONLY = "integrity-policy-report-only"
    """
    Reports on resources that the user agent loads that would violate `Subresource
    Integrity`_ guarantees if the integrity policy were enforced (using the ``Integrity-
    Policy`` header).

    .. _Subresource Integrity: https://developer.mozilla.org/en-US/docs/Web/Security/Defenses/Subresource_Integrity

    `MDN Docs <https://developer.mozilla.org/en-US/docs/Web/HTTP/Reference/Headers/Integrity-Policy-Report-Only>`_
    """

    KEEP_ALIVE = "keep-alive"
    """
    Controls how long a persistent connection should stay open.

    `MDN Docs <https://developer.mozilla.org/en-US/docs/Web/HTTP/Reference/Headers/Keep-Alive>`_
    """

    LAST_MODIFIED = "last-modified"
    """
    The last modification date of the resource, used to compare several versions of the same
    resource. It is less accurate than `ETag`_ , but easier to calculate in some
    environments. Conditional requests using `If-Modified-Since`_ and `If-Unmodified-Since`_
    use this value to change the behavior of the request.

    .. _ETag: https://developer.mozilla.org/en-US/docs/Web/HTTP/Reference/Headers/ETag
    .. _If-Modified-Since: https://developer.mozilla.org/en-US/docs/Web/HTTP/Reference/Headers/If-Modified-Since
    .. _If-Unmodified-Since: https://developer.mozilla.org/en-US/docs/Web/HTTP/Reference/Headers/If-Unmodified-Since

    `MDN Docs <https://developer.mozilla.org/en-US/docs/Web/HTTP/Reference/Headers/Last-Modified>`_
    """

    LINK = "link"
    """
    This entity-header field provides a means for serializing one or more links in HTTP
    headers. It is semantically equivalent to the HTML `<link>`_ element.

    .. _<link>: https://developer.mozilla.org/en-US/docs/Web/HTML/Reference/Elements/link

    `MDN Docs <https://developer.mozilla.org/en-US/docs/Web/HTTP/Reference/Headers/Link>`_
    """

    LOCATION = "location"
    """
    Indicates the URL to redirect a page to.

    `MDN Docs <https://developer.mozilla.org/en-US/docs/Web/HTTP/Reference/Headers/Location>`_
    """

    MAX_FORWARDS = "max-forwards"
    """
    When using `TRACE`_ , indicates the maximum number of hops the request can do before
    being reflected to the sender.

    .. _TRACE: https://developer.mozilla.org/en-US/docs/Web/HTTP/Reference/Methods/TRACE

    `MDN Docs <https://developer.mozilla.org/en-US/docs/Web/HTTP/Reference/Headers/Max-Forwards>`_
    """

    NEL = "nel"
    """
    Defines a mechanism that enables developers to declare a network error reporting policy.

    `MDN Docs <https://developer.mozilla.org/en-US/docs/Web/HTTP/Reference/Headers/NEL>`_
    """

    NO_VARY_SEARCH = "no-vary-search"
    """
    Specifies a set of rules that define how a URL's query parameters will affect cache
    matching. These rules dictate whether the same URL with different URL parameters should
    be saved as separate browser cache entries.

    `MDN Docs <https://developer.mozilla.org/en-US/docs/Web/HTTP/Reference/Headers/No-Vary-Search>`_
    """

    OBSERVE_BROWSING_TOPICS = "observe-browsing-topics"
    """
    Response header used to mark topics of interest inferred from a calling site's URL as
    observed in the response to a request generated by a `feature that enables the Topics
    API`_ .

    .. _feature that enables the Topics API: https://developer.mozilla.org/en-US/docs/Web/API/Topics_API/Using#what_api_features_enable_the_topics_api

    `MDN Docs <https://developer.mozilla.org/en-US/docs/Web/HTTP/Reference/Headers/Observe-Browsing-Topics>`_
    """

    ORIGIN = "origin"
    """
    Indicates where a fetch originates from.

    `MDN Docs <https://developer.mozilla.org/en-US/docs/Web/HTTP/Reference/Headers/Origin>`_
    """

    ORIGIN_AGENT_CLUSTER = "origin-agent-cluster"
    """
    Response header used to indicate that the associated `Document`_ should be placed in an
    origin-keyed `agent cluster`_ . This isolation allows user agents to allocate
    implementation-specific resources for agent clusters, such as processes or threads, more
    efficiently.

    .. _Document: https://developer.mozilla.org/en-US/docs/Web/API/Document
    .. _agent cluster: https://tc39.es/ecma262/#sec-agent-clusters

    `MDN Docs <https://developer.mozilla.org/en-US/docs/Web/HTTP/Reference/Headers/Origin-Agent-Cluster>`_
    """

    PERMISSIONS_POLICY = "permissions-policy"
    """
    Provides a mechanism to allow and deny the use of browser features in a website's own
    frame, and in `<iframe>`_ s that it embeds.

    .. _<iframe>: https://developer.mozilla.org/en-US/docs/Web/HTML/Reference/Elements/iframe

    `MDN Docs <https://developer.mozilla.org/en-US/docs/Web/HTTP/Reference/Headers/Permissions-Policy>`_
    """

    PRAGMA = "pragma"
    """
    Implementation-specific header that may have various effects anywhere along the request-
    response chain. Used for backwards compatibility with HTTP/1.0 caches where the ``Cache-
    Control`` header is not yet present.

    `MDN Docs <https://developer.mozilla.org/en-US/docs/Web/HTTP/Reference/Headers/Pragma>`_
    """

    PREFER = "prefer"
    """
    Indicates preferences for specific server behaviors during request processing. For
    example, it can request minimal response content ( ``return=minimal`` ) or asynchronous
    processing ( ``respond-async`` ). The server processes the request normally if the
    header is unsupported.

    `MDN Docs <https://developer.mozilla.org/en-US/docs/Web/HTTP/Reference/Headers/Prefer>`_
    """

    PREFERENCE_APPLIED = "preference-applied"
    """
    Informs the client which preferences specified in the ``Prefer`` header were applied by
    the server. It is a response-only header providing transparency about preference
    handling.

    `MDN Docs <https://developer.mozilla.org/en-US/docs/Web/HTTP/Reference/Headers/Preference-Applied>`_
    """

    PRIORITY = "priority"
    """
    Provides a hint from about the priority of a particular resource request on a particular
    connection. The value can be sent in a request to indicate the client priority, or in a
    response if the server chooses to reprioritize the request.

    `MDN Docs <https://developer.mozilla.org/en-US/docs/Web/HTTP/Reference/Headers/Priority>`_
    """

    PROXY_AUTHENTICATE = "proxy-authenticate"
    """
    Defines the authentication method that should be used to access a resource behind a
    proxy server.

    `MDN Docs <https://developer.mozilla.org/en-US/docs/Web/HTTP/Reference/Headers/Proxy-Authenticate>`_
    """

    PROXY_AUTHORIZATION = "proxy-authorization"
    """
    Contains the credentials to authenticate a user agent with a proxy server.

    `MDN Docs <https://developer.mozilla.org/en-US/docs/Web/HTTP/Reference/Headers/Proxy-Authorization>`_
    """

    RANGE = "range"
    """
    Indicates the part of a document that the server should return.

    `MDN Docs <https://developer.mozilla.org/en-US/docs/Web/HTTP/Reference/Headers/Range>`_
    """

    REFERER = "referer"
    """
    The address of the previous web page from which a link to the currently requested page
    was followed.

    `MDN Docs <https://developer.mozilla.org/en-US/docs/Web/HTTP/Reference/Headers/Referer>`_
    """

    REFERRER_POLICY = "referrer-policy"
    """
    Governs which referrer information sent in the `Referer`_ header should be included with
    requests made.

    .. _Referer: https://developer.mozilla.org/en-US/docs/Web/HTTP/Reference/Headers/Referer

    `MDN Docs <https://developer.mozilla.org/en-US/docs/Web/HTTP/Reference/Headers/Referrer-Policy>`_
    """

    REFRESH = "refresh"
    """
    Directs the browser to reload the page or redirect to another. Takes the same value as
    the ``meta`` element with `http-equiv="refresh"`_ .

    .. _http-equiv="refresh": https://developer.mozilla.org/en-US/docs/Web/HTML/Reference/Elements/meta/http-equiv

    `MDN Docs <https://developer.mozilla.org/en-US/docs/Web/HTTP/Reference/Headers/Refresh>`_
    """

    REPORT_TO = "report-to"
    """
    Response header used to specify server endpoints where the browser should send warning
    and error reports when using the `Reporting API`_ .

    .. _Reporting API: https://developer.mozilla.org/en-US/docs/Web/API/Reporting_API

    `MDN Docs <https://developer.mozilla.org/en-US/docs/Web/HTTP/Reference/Headers/Report-To>`_
    """

    REPORTING_ENDPOINTS = "reporting-endpoints"
    """
    Response header that allows website owners to specify one or more endpoints used to
    receive errors such as CSP violation reports, `Cross-Origin-Opener-Policy`_ reports, or
    other generic violations.

    .. _Cross-Origin-Opener-Policy: https://developer.mozilla.org/en-US/docs/Web/HTTP/Reference/Headers/Cross-Origin-Opener-Policy

    `MDN Docs <https://developer.mozilla.org/en-US/docs/Web/HTTP/Reference/Headers/Reporting-Endpoints>`_
    """

    REPR_DIGEST = "repr-digest"
    """
    Provides a `digest`_ of the selected representation of the target resource before
    transmission. Unlike the `Content-Digest`_ , the digest does not consider `Content-
    Encoding`_ or `Content-Range`_ .

    .. _digest: https://developer.mozilla.org/en-US/docs/Glossary/Hash_function
    .. _Content-Digest: https://developer.mozilla.org/en-US/docs/Web/HTTP/Reference/Headers/Content-Digest
    .. _Content-Encoding: https://developer.mozilla.org/en-US/docs/Web/HTTP/Reference/Headers/Content-Encoding
    .. _Content-Range: https://developer.mozilla.org/en-US/docs/Web/HTTP/Reference/Headers/Content-Range

    `MDN Docs <https://developer.mozilla.org/en-US/docs/Web/HTTP/Reference/Headers/Repr-Digest>`_
    """

    RETRY_AFTER = "retry-after"
    """
    Indicates how long the user agent should wait before making a follow-up request.

    `MDN Docs <https://developer.mozilla.org/en-US/docs/Web/HTTP/Reference/Headers/Retry-After>`_
    """

    RTT = "rtt"
    """
    Application layer round trip time (RTT) in milliseconds, which includes the server
    processing time. This is part of the `Network Information API`_ .

    .. _Network Information API: https://developer.mozilla.org/en-US/docs/Web/API/Network_Information_API

    `MDN Docs <https://developer.mozilla.org/en-US/docs/Web/HTTP/Reference/Headers/RTT>`_
    """

    SAVE_DATA = "save-data"
    """
    A string ``on`` that indicates the user agent's preference for reduced data usage.

    `MDN Docs <https://developer.mozilla.org/en-US/docs/Web/HTTP/Reference/Headers/Save-Data>`_
    """

    SEC_BROWSING_TOPICS = "sec-browsing-topics"
    """
    Request header that sends the selected topics for the current user along with the
    associated request, which are used by an ad tech platform to choose a personalized ad to
    display.

    `MDN Docs <https://developer.mozilla.org/en-US/docs/Web/HTTP/Reference/Headers/Sec-Browsing-Topics>`_
    """

    SEC_CH_DEVICE_MEMORY = "sec-ch-device-memory"
    """
    Approximate amount of available client RAM memory. This is part of the `Device Memory
    API`_ .

    .. _Device Memory API: https://developer.mozilla.org/en-US/docs/Web/API/Device_Memory_API

    `MDN Docs <https://developer.mozilla.org/en-US/docs/Web/HTTP/Reference/Headers/Sec-CH-Device-Memory>`_
    """

    SEC_CH_DPR = "sec-ch-dpr"
    """
    Request header that provides the client device pixel ratio (the number of physical
    `device pixels`_ for each `CSS pixel`_ ).

    .. _device pixels: https://developer.mozilla.org/en-US/docs/Glossary/Device_pixel
    .. _CSS pixel: https://developer.mozilla.org/en-US/docs/Glossary/CSS_pixel

    `MDN Docs <https://developer.mozilla.org/en-US/docs/Web/HTTP/Reference/Headers/Sec-CH-DPR>`_
    """

    SEC_CH_PREFERS_COLOR_SCHEME = "sec-ch-prefers-color-scheme"
    """
    User's preference of dark or light color scheme.

    `MDN Docs <https://developer.mozilla.org/en-US/docs/Web/HTTP/Reference/Headers/Sec-CH-Prefers-Color-Scheme>`_
    """

    SEC_CH_PREFERS_REDUCED_MOTION = "sec-ch-prefers-reduced-motion"
    """
    User's preference to see fewer animations and content layout shifts.

    `MDN Docs <https://developer.mozilla.org/en-US/docs/Web/HTTP/Reference/Headers/Sec-CH-Prefers-Reduced-Motion>`_
    """

    SEC_CH_PREFERS_REDUCED_TRANSPARENCY = "sec-ch-prefers-reduced-transparency"
    """
    Request header indicates the user agent's preference for reduced transparency.

    `MDN Docs <https://developer.mozilla.org/en-US/docs/Web/HTTP/Reference/Headers/Sec-CH-Prefers-Reduced-Transparency>`_
    """

    SEC_CH_UA = "sec-ch-ua"
    """
    User agent's branding and version.

    `MDN Docs <https://developer.mozilla.org/en-US/docs/Web/HTTP/Reference/Headers/Sec-CH-UA>`_
    """

    SEC_CH_UA_ARCH = "sec-ch-ua-arch"
    """
    User agent's underlying platform architecture.

    `MDN Docs <https://developer.mozilla.org/en-US/docs/Web/HTTP/Reference/Headers/Sec-CH-UA-Arch>`_
    """

    SEC_CH_UA_BITNESS = "sec-ch-ua-bitness"
    """
    User agent's underlying CPU architecture bitness (for example "64" bit).

    `MDN Docs <https://developer.mozilla.org/en-US/docs/Web/HTTP/Reference/Headers/Sec-CH-UA-Bitness>`_
    """

    SEC_CH_UA_FORM_FACTORS = "sec-ch-ua-form-factors"
    """
    User agent's form-factors, describing how the user interacts with the user-agent.

    `MDN Docs <https://developer.mozilla.org/en-US/docs/Web/HTTP/Reference/Headers/Sec-CH-UA-Form-Factors>`_
    """

    SEC_CH_UA_FULL_VERSION = "sec-ch-ua-full-version"
    """
    User agent's full version string.

    `MDN Docs <https://developer.mozilla.org/en-US/docs/Web/HTTP/Reference/Headers/Sec-CH-UA-Full-Version>`_
    """

    SEC_CH_UA_FULL_VERSION_LIST = "sec-ch-ua-full-version-list"
    """
    Full version for each brand in the user agent's brand list.

    `MDN Docs <https://developer.mozilla.org/en-US/docs/Web/HTTP/Reference/Headers/Sec-CH-UA-Full-Version-List>`_
    """

    SEC_CH_UA_MOBILE = "sec-ch-ua-mobile"
    """
    User agent is running on a mobile device or, more generally, prefers a "mobile" user
    experience.

    `MDN Docs <https://developer.mozilla.org/en-US/docs/Web/HTTP/Reference/Headers/Sec-CH-UA-Mobile>`_
    """

    SEC_CH_UA_MODEL = "sec-ch-ua-model"
    """
    User agent's device model.

    `MDN Docs <https://developer.mozilla.org/en-US/docs/Web/HTTP/Reference/Headers/Sec-CH-UA-Model>`_
    """

    SEC_CH_UA_PLATFORM = "sec-ch-ua-platform"
    """
    User agent's underlying operation system/platform.

    `MDN Docs <https://developer.mozilla.org/en-US/docs/Web/HTTP/Reference/Headers/Sec-CH-UA-Platform>`_
    """

    SEC_CH_UA_PLATFORM_VERSION = "sec-ch-ua-platform-version"
    """
    User agent's underlying operation system version.

    `MDN Docs <https://developer.mozilla.org/en-US/docs/Web/HTTP/Reference/Headers/Sec-CH-UA-Platform-Version>`_
    """

    SEC_CH_UA_WOW64 = "sec-ch-ua-wow64"
    """
    Whether or not the user agent binary is running in 32-bit mode on 64-bit Windows.

    `MDN Docs <https://developer.mozilla.org/en-US/docs/Web/HTTP/Reference/Headers/Sec-CH-UA-WoW64>`_
    """

    SEC_CH_VIEWPORT_HEIGHT = "sec-ch-viewport-height"
    """
    Request header provides the client's layout viewport height in `CSS pixels`_ .

    .. _CSS pixels: https://developer.mozilla.org/en-US/docs/Glossary/CSS_pixel

    `MDN Docs <https://developer.mozilla.org/en-US/docs/Web/HTTP/Reference/Headers/Sec-CH-Viewport-Height>`_
    """

    SEC_CH_VIEWPORT_WIDTH = "sec-ch-viewport-width"
    """
    Request header provides the client's layout viewport width in `CSS pixels`_ .

    .. _CSS pixels: https://developer.mozilla.org/en-US/docs/Glossary/CSS_pixel

    `MDN Docs <https://developer.mozilla.org/en-US/docs/Web/HTTP/Reference/Headers/Sec-CH-Viewport-Width>`_
    """

    SEC_CH_WIDTH = "sec-ch-width"
    """
    Request header provides the image's width in `CSS pixels`_ .

    .. _CSS pixels: https://developer.mozilla.org/en-US/docs/Glossary/CSS_pixel

    `MDN Docs <https://developer.mozilla.org/en-US/docs/Web/HTTP/Reference/Headers/Sec-CH-Width>`_
    """

    SEC_FETCH_DEST = "sec-fetch-dest"
    """
    Indicates the request's destination. It is a Structured Header whose value is a token
    with possible values ``audio`` , ``audioworklet`` , ``document`` , ``embed`` , ``empty``
    , ``font`` , ``image`` , ``manifest`` , ``object`` , ``paintworklet`` , ``report`` ,
    ``script`` , ``serviceworker`` , ``sharedworker`` , ``style`` , ``track`` , ``video`` ,
    ``worker`` , and ``xslt`` .

    `MDN Docs <https://developer.mozilla.org/en-US/docs/Web/HTTP/Reference/Headers/Sec-Fetch-Dest>`_
    """

    SEC_FETCH_MODE = "sec-fetch-mode"
    """
    Indicates the request's mode to a server. It is a Structured Header whose value is a
    token with possible values ``cors`` , ``navigate`` , ``no-cors`` , ``same-origin`` , and
    ``websocket`` .

    `MDN Docs <https://developer.mozilla.org/en-US/docs/Web/HTTP/Reference/Headers/Sec-Fetch-Mode>`_
    """

    SEC_FETCH_SITE = "sec-fetch-site"
    """
    Indicates the relationship between a request initiator's origin and its target's origin.
    It is a Structured Header whose value is a token with possible values ``cross-site`` ,
    ``same-origin`` , ``same-site`` , and ``none`` .

    `MDN Docs <https://developer.mozilla.org/en-US/docs/Web/HTTP/Reference/Headers/Sec-Fetch-Site>`_
    """

    SEC_FETCH_STORAGE_ACCESS = "sec-fetch-storage-access"
    """
    Indicates the "storage access status" for the current fetch context, which will be one
    of ``none`` , ``inactive`` , or ``active`` . The server may respond with ``Activate-
    Storage-Access`` to request that the browser activate an ``inactive`` permission and
    retry the request, or to load a resource with access to its third-party cookies if the
    status is ``active`` .

    `MDN Docs <https://developer.mozilla.org/en-US/docs/Web/HTTP/Reference/Headers/Sec-Fetch-Storage-Access>`_
    """

    SEC_FETCH_USER = "sec-fetch-user"
    """
    Indicates whether or not a navigation request was triggered by user activation. It is a
    Structured Header whose value is a boolean so possible values are ``?0`` for false and
    ``?1`` for true.

    `MDN Docs <https://developer.mozilla.org/en-US/docs/Web/HTTP/Reference/Headers/Sec-Fetch-User>`_
    """

    SEC_GPC = "sec-gpc"
    """
    Indicates whether the user consents to a website or service selling or sharing their
    personal information with third parties.

    `MDN Docs <https://developer.mozilla.org/en-US/docs/Web/HTTP/Reference/Headers/Sec-GPC>`_
    """

    SEC_PURPOSE = "sec-purpose"
    """
    Indicates the purpose of the request, when the purpose is something other than immediate
    use by the user-agent. The header currently has one possible value, ``prefetch`` , which
    indicates that the resource is being fetched preemptively for a possible future
    navigation.

    `MDN Docs <https://developer.mozilla.org/en-US/docs/Web/HTTP/Reference/Headers/Sec-Purpose>`_
    """

    SEC_WEBSOCKET_ACCEPT = "sec-websocket-accept"
    """
    Response header that indicates that the server is willing to upgrade to a WebSocket
    connection.

    `MDN Docs <https://developer.mozilla.org/en-US/docs/Web/HTTP/Reference/Headers/Sec-WebSocket-Accept>`_
    """

    SEC_WEBSOCKET_EXTENSIONS = "sec-websocket-extensions"
    """
    In requests, this header indicates the WebSocket extensions supported by the client in
    preferred order. In responses, it indicates the extension selected by the server from
    the client's preferences.

    `MDN Docs <https://developer.mozilla.org/en-US/docs/Web/HTTP/Reference/Headers/Sec-WebSocket-Extensions>`_
    """

    SEC_WEBSOCKET_KEY = "sec-websocket-key"
    """
    Request header containing a key that verifies that the client explicitly intends to open
    a ``WebSocket`` .

    `MDN Docs <https://developer.mozilla.org/en-US/docs/Web/HTTP/Reference/Headers/Sec-WebSocket-Key>`_
    """

    SEC_WEBSOCKET_PROTOCOL = "sec-websocket-protocol"
    """
    In requests, this header indicates the sub-protocols supported by the client in
    preferred order. In responses, it indicates the sub-protocol selected by the server from
    the client's preferences.

    `MDN Docs <https://developer.mozilla.org/en-US/docs/Web/HTTP/Reference/Headers/Sec-WebSocket-Protocol>`_
    """

    SEC_WEBSOCKET_VERSION = "sec-websocket-version"
    """
    In requests, this header indicates the version of the WebSocket protocol used by the
    client. In responses, it is sent only if the requested protocol version is not supported
    by the server, and lists the versions that the server supports.

    `MDN Docs <https://developer.mozilla.org/en-US/docs/Web/HTTP/Reference/Headers/Sec-WebSocket-Version>`_
    """

    SERVER = "server"
    """
    Contains information about the software used by the origin server to handle the request.

    `MDN Docs <https://developer.mozilla.org/en-US/docs/Web/HTTP/Reference/Headers/Server>`_
    """

    SERVER_TIMING = "server-timing"
    """
    Communicates one or more metrics and descriptions for the given request-response cycle.

    `MDN Docs <https://developer.mozilla.org/en-US/docs/Web/HTTP/Reference/Headers/Server-Timing>`_
    """

    SERVICE_WORKER = "service-worker"
    """
    Included in fetches for a service worker's script resource. This header helps
    administrators log service worker script requests for monitoring purposes.

    `MDN Docs <https://developer.mozilla.org/en-US/docs/Web/HTTP/Reference/Headers/Service-Worker>`_
    """

    SERVICE_WORKER_ALLOWED = "service-worker-allowed"
    """
    Used to remove the `path restriction`_ by including this header `in the response of the
    Service Worker script`_ .

    .. _path restriction: https://developer.mozilla.org/en-US/docs/Web/API/Service_Worker_API/Using_Service_Workers#why_is_my_service_worker_failing_to_register
    .. _in the response of the Service Worker script: https://w3c.github.io/ServiceWorker/#service-worker-script-response

    `MDN Docs <https://developer.mozilla.org/en-US/docs/Web/HTTP/Reference/Headers/Service-Worker-Allowed>`_
    """

    SERVICE_WORKER_NAVIGATION_PRELOAD = "service-worker-navigation-preload"
    """
    A request header sent in preemptive request to `fetch()`_ a resource during service
    worker boot. The value, which is set with `NavigationPreloadManager.setHeaderValue()`_ ,
    can be used to inform a server that a different resource should be returned than in a
    normal ``fetch()`` operation.

    .. _fetch(): https://developer.mozilla.org/en-US/docs/Web/API/Window/fetch
    .. _NavigationPreloadManager.setHeaderValue(): https://developer.mozilla.org/en-US/docs/Web/API/NavigationPreloadManager/setHeaderValue

    `MDN Docs <https://developer.mozilla.org/en-US/docs/Web/HTTP/Reference/Headers/Service-Worker-Navigation-Preload>`_
    """

    SET_COOKIE = "set-cookie"
    """
    Send cookies from the server to the user-agent.

    `MDN Docs <https://developer.mozilla.org/en-US/docs/Web/HTTP/Reference/Headers/Set-Cookie>`_
    """

    SOURCEMAP = "sourcemap"
    """
    Links to a `source map`_ so that debuggers can step through original source code instead
    of generated or transformed code.

    .. _source map: https://developer.mozilla.org/en-US/docs/Glossary/Source_map

    `MDN Docs <https://developer.mozilla.org/en-US/docs/Web/HTTP/Reference/Headers/SourceMap>`_
    """

    STRICT_TRANSPORT_SECURITY = "strict-transport-security"
    """
    Force communication using HTTPS instead of HTTP.

    `MDN Docs <https://developer.mozilla.org/en-US/docs/Web/HTTP/Reference/Headers/Strict-Transport-Security>`_
    """

    TE = "te"
    """
    Specifies the transfer encodings the user agent is willing to accept.

    `MDN Docs <https://developer.mozilla.org/en-US/docs/Web/HTTP/Reference/Headers/TE>`_
    """

    TIMING_ALLOW_ORIGIN = "timing-allow-origin"
    """
    Specifies origins that are allowed to see values of attributes retrieved via features of
    the `Resource Timing API`_ , which would otherwise be reported as zero due to cross-
    origin restrictions.

    .. _Resource Timing API: https://developer.mozilla.org/en-US/docs/Web/API/Performance_API/Resource_timing

    `MDN Docs <https://developer.mozilla.org/en-US/docs/Web/HTTP/Reference/Headers/Timing-Allow-Origin>`_
    """

    TK = "tk"
    """
    Response header that indicates the tracking status that applied to the corresponding
    request. Used in conjunction with DNT.

    `MDN Docs <https://developer.mozilla.org/en-US/docs/Web/HTTP/Reference/Headers/Tk>`_
    """

    TRAILER = "trailer"
    """
    Allows the sender to include additional fields at the end of chunked message.

    `MDN Docs <https://developer.mozilla.org/en-US/docs/Web/HTTP/Reference/Headers/Trailer>`_
    """

    TRANSFER_ENCODING = "transfer-encoding"
    """
    Specifies the form of encoding used to safely transfer the resource to the user.

    `MDN Docs <https://developer.mozilla.org/en-US/docs/Web/HTTP/Reference/Headers/Transfer-Encoding>`_
    """

    UPGRADE = "upgrade"
    """
    This HTTP/1.1 (only) header can be used to upgrade an already established client/server
    connection to a different protocol (over the same transport protocol). For example, it
    can be used by a client to upgrade a connection from HTTP 1.1 to HTTP 2.0, or an HTTP or
    HTTPS connection into a WebSocket.

    `MDN Docs <https://developer.mozilla.org/en-US/docs/Web/HTTP/Reference/Headers/Upgrade>`_
    """

    UPGRADE_INSECURE_REQUESTS = "upgrade-insecure-requests"
    """
    Sends a signal to the server expressing the client's preference for an encrypted and
    authenticated response, and that it can successfully handle the `upgrade-insecure-
    requests`_ directive.

    .. _upgrade-insecure-requests: https://developer.mozilla.org/en-US/docs/Web/HTTP/Reference/Headers/Content-Security-Policy/upgrade-insecure-requests

    `MDN Docs <https://developer.mozilla.org/en-US/docs/Web/HTTP/Reference/Headers/Upgrade-Insecure-Requests>`_
    """

    USE_AS_DICTIONARY = "use-as-dictionary"
    """
    Lists the matching criteria that the dictionary can be used for in future requests.

    `MDN Docs <https://developer.mozilla.org/en-US/docs/Web/HTTP/Reference/Headers/Use-As-Dictionary>`_
    """

    USER_AGENT = "user-agent"
    """
    Contains a characteristic string that allows the network protocol peers to identify the
    application type, operating system, software vendor or software version of the
    requesting software user agent.

    `MDN Docs <https://developer.mozilla.org/en-US/docs/Web/HTTP/Reference/Headers/User-Agent>`_
    """

    VARY = "vary"
    """
    Determines how to match request headers to decide whether a cached response can be used
    rather than requesting a fresh one from the origin server.

    `MDN Docs <https://developer.mozilla.org/en-US/docs/Web/HTTP/Reference/Headers/Vary>`_
    """

    VIA = "via"
    """
    Added by proxies, both forward and reverse proxies, and can appear in the request
    headers and the response headers.

    `MDN Docs <https://developer.mozilla.org/en-US/docs/Web/HTTP/Reference/Headers/Via>`_
    """

    VIEWPORT_WIDTH = "viewport-width"
    """
    Standardized as `Sec-CH-Viewport-Width`_

    .. _Sec-CH-Viewport-Width: https://developer.mozilla.org/en-US/docs/Web/HTTP/Reference/Headers/Sec-CH-Viewport-Width

    `MDN Docs <https://developer.mozilla.org/en-US/docs/Web/HTTP/Reference/Headers/Viewport-Width>`_
    """

    WANT_CONTENT_DIGEST = "want-content-digest"
    """
    States the wish for a `Content-Digest`_ header. It is the ``Content-`` analogue of
    `Want-Repr-Digest`_ .

    .. _Content-Digest: https://developer.mozilla.org/en-US/docs/Web/HTTP/Reference/Headers/Content-Digest
    .. _Want-Repr-Digest: https://developer.mozilla.org/en-US/docs/Web/HTTP/Reference/Headers/Want-Repr-Digest

    `MDN Docs <https://developer.mozilla.org/en-US/docs/Web/HTTP/Reference/Headers/Want-Content-Digest>`_
    """

    WANT_REPR_DIGEST = "want-repr-digest"
    """
    States the wish for a `Repr-Digest`_ header. It is the ``Repr-`` analogue of `Want-
    Content-Digest`_ .

    .. _Repr-Digest: https://developer.mozilla.org/en-US/docs/Web/HTTP/Reference/Headers/Repr-Digest
    .. _Want-Content-Digest: https://developer.mozilla.org/en-US/docs/Web/HTTP/Reference/Headers/Want-Content-Digest

    `MDN Docs <https://developer.mozilla.org/en-US/docs/Web/HTTP/Reference/Headers/Want-Repr-Digest>`_
    """

    WARNING = "warning"
    """
    General warning information about possible problems.

    `MDN Docs <https://developer.mozilla.org/en-US/docs/Web/HTTP/Reference/Headers/Warning>`_
    """

    WIDTH = "width"
    """
    Standardized as `Sec-CH-Width`_

    .. _Sec-CH-Width: https://developer.mozilla.org/en-US/docs/Web/HTTP/Reference/Headers/Sec-CH-Width

    `MDN Docs <https://developer.mozilla.org/en-US/docs/Web/HTTP/Reference/Headers/Width>`_
    """

    WWW_AUTHENTICATE = "www-authenticate"
    """
    Defines the authentication method that should be used to access a resource.

    `MDN Docs <https://developer.mozilla.org/en-US/docs/Web/HTTP/Reference/Headers/WWW-Authenticate>`_
    """

    X_CONTENT_TYPE_OPTIONS = "x-content-type-options"
    """
    Disables MIME sniffing and forces browser to use the type given in `Content-Type`_ .

    .. _Content-Type: https://developer.mozilla.org/en-US/docs/Web/HTTP/Reference/Headers/Content-Type

    `MDN Docs <https://developer.mozilla.org/en-US/docs/Web/HTTP/Reference/Headers/X-Content-Type-Options>`_
    """

    X_DNS_PREFETCH_CONTROL = "x-dns-prefetch-control"
    """
    Controls DNS prefetching, a feature by which browsers proactively perform domain name
    resolution on both links that the user may choose to follow as well as URLs for items
    referenced by the document, including images, CSS, JavaScript, and so forth.

    `MDN Docs <https://developer.mozilla.org/en-US/docs/Web/HTTP/Reference/Headers/X-DNS-Prefetch-Control>`_
    """

    X_FORWARDED_FOR = "x-forwarded-for"
    """
    Identifies the originating IP addresses of a client connecting to a web server through
    an HTTP proxy or a load balancer.

    `MDN Docs <https://developer.mozilla.org/en-US/docs/Web/HTTP/Reference/Headers/X-Forwarded-For>`_
    """

    X_FORWARDED_HOST = "x-forwarded-host"
    """
    Identifies the original host requested that a client used to connect to your proxy or
    load balancer.

    `MDN Docs <https://developer.mozilla.org/en-US/docs/Web/HTTP/Reference/Headers/X-Forwarded-Host>`_
    """

    X_FORWARDED_PROTO = "x-forwarded-proto"
    """
    Identifies the protocol (HTTP or HTTPS) that a client used to connect to your proxy or
    load balancer.

    `MDN Docs <https://developer.mozilla.org/en-US/docs/Web/HTTP/Reference/Headers/X-Forwarded-Proto>`_
    """

    X_FRAME_OPTIONS = "x-frame-options"
    """
    Indicates whether a browser should be allowed to render a page in a `<frame>`_ ,
    `<iframe>`_ , `<embed>`_ or `<object>`_ .

    .. _<frame>: https://developer.mozilla.org/en-US/docs/Web/HTML/Reference/Elements/frame
    .. _<iframe>: https://developer.mozilla.org/en-US/docs/Web/HTML/Reference/Elements/iframe
    .. _<embed>: https://developer.mozilla.org/en-US/docs/Web/HTML/Reference/Elements/embed
    .. _<object>: https://developer.mozilla.org/en-US/docs/Web/HTML/Reference/Elements/object

    `MDN Docs <https://developer.mozilla.org/en-US/docs/Web/HTTP/Reference/Headers/X-Frame-Options>`_
    """

    X_PERMITTED_CROSS_DOMAIN_POLICIES = "x-permitted-cross-domain-policies"
    """
    A cross-domain policy file may grant clients, such as Adobe Acrobat or Apache Flex
    (among others), permission to handle data across domains that would otherwise be
    restricted due to the `Same-Origin Policy`_ . The ``X-Permitted-Cross-Domain-Policies``
    header overrides such policy files so that clients still block unwanted requests.

    .. _Same-Origin Policy: https://developer.mozilla.org/en-US/docs/Web/Security/Defenses/Same-origin_policy

    `MDN Docs <https://developer.mozilla.org/en-US/docs/Web/HTTP/Reference/Headers/X-Permitted-Cross-Domain-Policies>`_
    """

    X_POWERED_BY = "x-powered-by"
    """
    May be set by hosting environments or other frameworks and contains information about
    them while not providing any usefulness to the application or its visitors. Unset this
    header to avoid exposing potential vulnerabilities.

    `MDN Docs <https://developer.mozilla.org/en-US/docs/Web/HTTP/Reference/Headers/X-Powered-By>`_
    """

    X_ROBOTS_TAG = "x-robots-tag"
    """
    The `X-Robots-Tag`_ HTTP header is used to indicate how a web page is to be indexed
    within public search engine results. The header is equivalent to `<meta name="robots">`_
    elements.

    .. _X-Robots-Tag: https://developers.google.com/search/docs/crawling-indexing/robots-meta-tag
    .. _<meta name="robots">: https://developer.mozilla.org/en-US/docs/Web/HTML/Reference/Elements/meta/name/robots

    `MDN Docs <https://developer.mozilla.org/en-US/docs/Web/HTTP/Reference/Headers/X-Robots-Tag>`_
    """

    X_XSS_PROTECTION = "x-xss-protection"
    """
    Enables cross-site scripting filtering.

    `MDN Docs <https://developer.mozilla.org/en-US/docs/Web/HTTP/Reference/Headers/X-XSS-Protection>`_
    """
