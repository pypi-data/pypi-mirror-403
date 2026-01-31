"""HTTP Response object."""

from __future__ import annotations

from typing import TYPE_CHECKING

from pydantic import Field

from ocsf._base import OCSFBaseModel

if TYPE_CHECKING:
    from ocsf.v1_5_0.objects.http_header import HttpHeader


class HttpResponse(OCSFBaseModel):
    """The HTTP Response object contains detailed information about the response sent from a web server to the requester. It encompasses attributes and metadata that describe the response status, headers, body content, and other relevant information.

    See: https://schema.ocsf.io/1.5.0/objects/http_response
    """

    code: int = Field(
        ...,
        description="The Hypertext Transfer Protocol (HTTP) status code returned from the web server to the client. For example, 200.",
    )
    body_length: int | None = Field(
        default=None,
        description="The actual length of the HTTP response body, in number of bytes, independent of a potentially existing Content-Length header.",
    )
    content_type: str | None = Field(
        default=None,
        description="The request header that identifies the original <a target='_blank' href='https://www.iana.org/assignments/media-types/media-types.xhtml'>media type </a> of the resource (prior to any content encoding applied for sending).",
    )
    http_headers: list[HttpHeader] | None = Field(
        default=None,
        description="Additional HTTP headers of an HTTP request or response. [Recommended]",
    )
    latency: int | None = Field(
        default=None, description="The HTTP response latency measured in milliseconds."
    )
    length: int | None = Field(
        default=None, description="The length of the entire HTTP response, in number of bytes."
    )
    message: str | None = Field(
        default=None, description="The description of the event/finding, as defined by the source."
    )
    status: str | None = Field(
        default=None,
        description="The response status. For example: A successful HTTP status of 'OK' which corresponds to a code of 200.",
    )
