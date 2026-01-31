"""The run state ID of the job. enumeration."""

from enum import IntEnum


class RunStateId(IntEnum):
    """The run state ID of the job.

    See: https://schema.ocsf.io/1.1.0/data_types/run_state_id
    """

    VALUE_0 = 0  #
    VALUE_1 = 1  #
    VALUE_2 = 2  #
    VALUE_3 = 3  #
    VALUE_4 = 4  #
    VALUE_99 = 99  #
