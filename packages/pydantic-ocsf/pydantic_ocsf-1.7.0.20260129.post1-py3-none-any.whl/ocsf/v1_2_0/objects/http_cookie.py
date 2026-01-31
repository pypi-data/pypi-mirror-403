"""HTTP Cookie object."""

from __future__ import annotations

from pydantic import Field

from ocsf._base import OCSFBaseModel


class HttpCookie(OCSFBaseModel):
    """The HTTP Cookie object, also known as a web cookie or browser cookie, contains details and values pertaining to a small piece of data that a server sends to a user's web browser. This data is then stored by the browser and sent back to the server with subsequent requests, allowing the server to remember and track certain information about the user's browsing session or preferences.

    See: https://schema.ocsf.io/1.2.0/objects/http_cookie
    """

    name: str = Field(..., description="The HTTP cookie name.")
    value: str = Field(..., description="The HTTP cookie value.")
    domain: str | None = Field(default=None, description="The name of the domain.")
    expiration_time: int | None = Field(
        default=None, description="The expiration time of the HTTP cookie."
    )
    http_only: bool | None = Field(
        default=None, description="A cookie attribute to make it inaccessible via JavaScript"
    )
    is_http_only: bool | None = Field(
        default=None,
        description="This attribute prevents the cookie from being accessed via JavaScript.",
    )
    is_secure: bool | None = Field(
        default=None,
        description="The cookie attribute indicates that cookies are sent to the server only when the request is encrypted using the HTTPS protocol.",
    )
    path: str | None = Field(default=None, description="The path of the HTTP cookie.")
    samesite: str | None = Field(
        default=None,
        description="The cookie attribute that lets servers specify whether/when cookies are sent with cross-site requests. Values are: Strict, Lax or None",
    )
    secure: bool | None = Field(
        default=None,
        description="The cookie attribute to only send cookies to the server with an encrypted request over the HTTPS protocol.",
    )
