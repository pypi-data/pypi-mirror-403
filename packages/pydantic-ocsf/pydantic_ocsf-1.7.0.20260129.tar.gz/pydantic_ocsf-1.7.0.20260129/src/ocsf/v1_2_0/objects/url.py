"""Uniform Resource Locator object."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from pydantic import Field

from ocsf._base import OCSFBaseModel

if TYPE_CHECKING:
    from ocsf.v1_2_0.enums.category_ids import CategoryIds


class Url(OCSFBaseModel):
    """The Uniform Resource Locator(URL) object describes the characteristics of a URL. Defined in <a target='_blank' href='https://datatracker.ietf.org/doc/html/rfc1738'>RFC 1738</a> and by D3FEND <a target='_blank' href='https://d3fend.mitre.org/dao/artifact/d3f:URL/'>d3f:URL</a>.

    See: https://schema.ocsf.io/1.2.0/objects/url
    """

    categories: list[str] | None = Field(
        default=None,
        description="The Website categorization names, as defined by <code>category_ids</code> enum values.",
    )
    category_ids: list[CategoryIds] | None = Field(
        default=None, description="The Website categorization identifiers. [Recommended]"
    )
    hostname: Any | None = Field(
        default=None,
        description="The URL host as extracted from the URL. For example: <code>www.example.com</code> from <code>www.example.com/download/trouble</code>. [Recommended]",
    )
    path: str | None = Field(
        default=None,
        description="The URL path as extracted from the URL. For example: <code>/download/trouble</code> from <code>www.example.com/download/trouble</code>. [Recommended]",
    )
    port: Any | None = Field(
        default=None, description="The URL port. For example: <code>80</code>. [Recommended]"
    )
    query_string: str | None = Field(
        default=None,
        description="The query portion of the URL. For example: the query portion of the URL <code>http://www.example.com/search?q=bad&sort=date</code> is <code>q=bad&sort=date</code>. [Recommended]",
    )
    resource_type: str | None = Field(
        default=None, description="The context in which a resource was retrieved in a web request."
    )
    scheme: str | None = Field(
        default=None,
        description="The scheme portion of the URL. For example: <code>http</code>, <code>https</code>, <code>ftp</code>, or <code>sftp</code>. [Recommended]",
    )
    subdomain: str | None = Field(
        default=None,
        description="The subdomain portion of the URL. For example: <code>sub</code> in <code>https://sub.example.com</code> or <code>sub2.sub1</code> in <code>https://sub2.sub1.example.com</code>.",
    )
    url_string: Any | None = Field(
        default=None,
        description="The URL string. See RFC 1738. For example: <code>http://www.example.com/download/trouble.exe</code>. Note: The URL path should not populate the URL string. [Recommended]",
    )
