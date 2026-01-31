"""The list of normalized identifiers that describe the startup items' properties when it is running.  Use this field to capture extended information about the process, which may depend on the type of startup item.  E.g., A Windows service that interacts with the desktop. enumeration."""

from enum import IntEnum


class RunModeIds(IntEnum):
    """The list of normalized identifiers that describe the startup items' properties when it is running.  Use this field to capture extended information about the process, which may depend on the type of startup item.  E.g., A Windows service that interacts with the desktop.

    See: https://schema.ocsf.io/1.7.0/data_types/run_mode_ids
    """

    VALUE_1 = 1  # The startup item interacts with the desktop.
    VALUE_2 = 2  # The startup item runs in its own process.
    VALUE_3 = 3  # The startup item runs in a shared process.
