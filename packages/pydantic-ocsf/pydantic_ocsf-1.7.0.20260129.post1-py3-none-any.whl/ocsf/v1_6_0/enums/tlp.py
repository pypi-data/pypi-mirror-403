"""The <a target='_blank' href='https://www.first.org/tlp/'>Traffic Light Protocol</a> was created to facilitate greater sharing of potentially sensitive information and more effective collaboration. TLP provides a simple and intuitive schema for indicating with whom potentially sensitive information can be shared. enumeration."""

from enum import IntEnum


class Tlp(IntEnum):
    """The <a target='_blank' href='https://www.first.org/tlp/'>Traffic Light Protocol</a> was created to facilitate greater sharing of potentially sensitive information and more effective collaboration. TLP provides a simple and intuitive schema for indicating with whom potentially sensitive information can be shared.

    See: https://schema.ocsf.io/1.6.0/data_types/tlp
    """
