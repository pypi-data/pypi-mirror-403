"""The normalized identifier of the query result. enumeration."""

from enum import IntEnum


class QueryResultId(IntEnum):
    """The normalized identifier of the query result.

    See: https://schema.ocsf.io/1.7.0/data_types/query_result_id
    """

    VALUE_0 = 0  # The query result is unknown.
    VALUE_1 = 1  # The target was found.
    VALUE_2 = 2  # The target was partially found.
    VALUE_3 = 3  # The target was not found.
    VALUE_4 = 4  # The discovery attempt failed.
    VALUE_5 = 5  # Discovery of the target was not supported.
    VALUE_99 = 99  # The query result is not mapped. See the <code>query_result</code> attribute, which contains a data source specific value.
