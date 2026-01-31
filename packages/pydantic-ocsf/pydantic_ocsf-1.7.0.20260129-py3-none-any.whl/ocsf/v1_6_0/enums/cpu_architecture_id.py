"""The normalized identifier of the CPU architecture. enumeration."""

from enum import IntEnum


class CpuArchitectureId(IntEnum):
    """The normalized identifier of the CPU architecture.

    See: https://schema.ocsf.io/1.6.0/data_types/cpu_architecture_id
    """

    VALUE_0 = 0  # The CPU architecture is unknown.
    VALUE_1 = 1  # CPU uses the x86 ISA. For bitness, refer to <code>cpu_bits</code>.
    VALUE_2 = 2  # CPU uses the ARM ISA. For bitness, refer to <code>cpu_bits</code>.
    VALUE_3 = 3  # CPU uses the RISC-V ISA. For bitness, refer to <code>cpu_bits</code>.
    VALUE_99 = 99  # The CPU architecture is not mapped. See the <code>cpu_architecture</code> attribute, which contains a data source specific value.
