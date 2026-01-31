"""HTTP Header object."""

from __future__ import annotations

from pydantic import Field

from ocsf._base import OCSFBaseModel


class HttpHeader(OCSFBaseModel):
    """TThe HTTP Header object represents the headers sent in an HTTP request or response. HTTP headers are key-value pairs that convey additional information about the HTTP message, including details about the content, caching, authentication, encoding, and other aspects of the communication.

    See: https://schema.ocsf.io/1.0.0/objects/http_header
    """

    name: str = Field(..., description="The name of the header")
    value: str = Field(..., description="The value of the header")
