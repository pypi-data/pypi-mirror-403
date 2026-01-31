"""The stage or state that the data was in when it was assessed or scanned by a data security tool. enumeration."""

from enum import IntEnum


class DataLifecycleStateId(IntEnum):
    """The stage or state that the data was in when it was assessed or scanned by a data security tool.

    See: https://schema.ocsf.io/1.7.0/data_types/data_lifecycle_state_id
    """

    VALUE_0 = 0  # The data lifecycle state is unknown.
    VALUE_1 = 1  # The data was stored on physical or logical media and was not actively moving through the network nor was being processed. E.g., data stored in a database, PDF files in a file share, or EHR records in object storage.
    VALUE_2 = 2  # The data was actively moving through the network or from one physical or logical location to another. E.g., emails being send, data replication or Change Data Capture (CDC) streams, or sensitive data processed on an API.
    VALUE_3 = 3  # The data was being processed, accessed, or read by a system, making it active in memory or CPU. E.g., sensitive data in a Business Intelligence tool, ePHI being processed in an EHR application or a user viewing data stored in a spreadsheet or PDF.
    VALUE_99 = 99  # The data lifecycle state is not mapped. See the <code>data_lifecycle_state</code> attribute, which contains a data source specific value.
