"""Object object."""

from __future__ import annotations

from ocsf._base import OCSFBaseModel


class Object(OCSFBaseModel):
    """An unordered collection of attributes. It defines a set of attributes available in all objects. It can be also used as a generic object to log objects that are not otherwise defined by the schema.

    See: https://schema.ocsf.io/1.6.0/objects/object
    """
