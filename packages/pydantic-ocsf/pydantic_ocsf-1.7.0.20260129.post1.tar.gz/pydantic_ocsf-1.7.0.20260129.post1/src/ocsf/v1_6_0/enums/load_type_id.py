"""The normalized identifier for how the module was loaded in memory. enumeration."""

from enum import IntEnum


class LoadTypeId(IntEnum):
    """The normalized identifier for how the module was loaded in memory.

    See: https://schema.ocsf.io/1.6.0/data_types/load_type_id
    """

    VALUE_1 = 1  # A normal module loaded by the normal windows loading mechanism i.e. LoadLibrary.
    VALUE_2 = 2  # A module loaded in a way avoidant of normal windows procedures. i.e. Bootstrapped Loading/Manual Dll Loading.
    VALUE_3 = 3  # A raw module in process memory that is READWRITE_EXECUTE and had a thread started in its range.
    VALUE_4 = 4  # A memory mapped file, typically created with CreatefileMapping/MapViewOfFile.
    VALUE_5 = 5  # A module loaded in a non standard way. However, GetModuleFileName succeeds on this allocation.
