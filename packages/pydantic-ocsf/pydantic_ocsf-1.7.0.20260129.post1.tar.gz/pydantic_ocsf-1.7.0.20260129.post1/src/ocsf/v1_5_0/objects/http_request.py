"""HTTP Request object."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from pydantic import Field

from ocsf._base import OCSFBaseModel

if TYPE_CHECKING:
    from ocsf.v1_5_0.enums.http_method import HttpMethod
    from ocsf.v1_5_0.objects.http_header import HttpHeader
    from ocsf.v1_5_0.objects.url import Url


class HttpRequest(OCSFBaseModel):
    """The HTTP Request object represents the attributes of a request made to a web server. It encapsulates the details and metadata associated with an HTTP request, including the request method, headers, URL, query parameters, body content, and other relevant information.

    See: https://schema.ocsf.io/1.5.0/objects/http_request
    """

    args: str | None = Field(
        default=None, description="The arguments sent along with the HTTP request."
    )
    body_length: int | None = Field(
        default=None,
        description="The actual length of the HTTP request body, in number of bytes, independent of a potentially existing Content-Length header.",
    )
    http_headers: list[HttpHeader] | None = Field(
        default=None,
        description="Additional HTTP headers of an HTTP request or response. [Recommended]",
    )
    http_method: HttpMethod | None = Field(
        default=None,
        description="The <a target='_blank' href='https://developer.mozilla.org/en-US/docs/Web/HTTP/Methods'>HTTP request method</a> indicates the desired action to be performed for a given resource. [Recommended]",
    )
    length: int | None = Field(
        default=None, description="The length of the entire HTTP request, in number of bytes."
    )
    referrer: str | None = Field(
        default=None,
        description="The request header that identifies the address of the previous web page, which is linked to the current web page or resource being requested.",
    )
    uid: str | None = Field(default=None, description="The unique identifier of the http request.")
    url: Url | None = Field(
        default=None, description="The URL object that pertains to the request. [Recommended]"
    )
    user_agent: str | None = Field(
        default=None,
        description="The request header that identifies the operating system and web browser. [Recommended]",
    )
    version: str | None = Field(
        default=None, description="The Hypertext Transfer Protocol (HTTP) version. [Recommended]"
    )
    x_forwarded_for: list[Any] | None = Field(
        default=None,
        description="The X-Forwarded-For header identifying the originating IP address(es) of a client connecting to a web server through an HTTP proxy or a load balancer.",
    )
