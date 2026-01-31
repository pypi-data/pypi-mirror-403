"""HTTP Response object."""

from __future__ import annotations

from pydantic import Field

from ocsf._base import OCSFBaseModel


class HttpResponse(OCSFBaseModel):
    """The HTTP Response object contains detailed information about the response sent from a web server to the requester. It encompasses attributes and metadata that describe the response status, headers, body content, and other relevant information.

    See: https://schema.ocsf.io/1.0.0/objects/http_response
    """

    code: int = Field(
        ..., description="The numeric code sent from the web server to the requester."
    )
    content_type: str | None = Field(
        default=None,
        description="The request header that identifies the original <a target='_blank' href='https://www.iana.org/assignments/media-types/media-types.xhtml'>media type </a> of the resource (prior to any content encoding applied for sending).",
    )
    latency: int | None = Field(
        default=None, description="TODO: The HTTP response latency. In seconds, milliseconds, etc.?"
    )
    length: int | None = Field(
        default=None, description="The HTTP response length, in number of bytes."
    )
    message: str | None = Field(
        default=None, description="The description of the event, as defined by the event source."
    )
    status: str | None = Field(
        default=None,
        description="The response status. For example: Kubernetes responseStatus.status.",
    )
