"""The normalized type of system query performed against a device or system component. enumeration."""

from enum import IntEnum


class QueryTypeId(IntEnum):
    """The normalized type of system query performed against a device or system component.

    See: https://schema.ocsf.io/1.7.0/data_types/query_type_id
    """

    VALUE_0 = 0  # The query type was unknown or not specified.
    VALUE_1 = 1  # A query about kernel resources including system calls, shared mutex, or other kernel components.
    VALUE_2 = 2  # A query about file attributes, metadata, content, hash values, or properties.
    VALUE_3 = 3  # A query about folder attributes, metadata, content, or structure.
    VALUE_4 = 4  # A query about group membership, privileges, domain, or group properties.
    VALUE_5 = (
        5  # A query about scheduled jobs, their command lines, run states, or execution times.
    )
    VALUE_6 = 6  # A query about loaded modules, their base addresses, load types, or function entry points.
    VALUE_7 = 7  # A query about active network connections, boundaries, protocols, or TCP states.
    VALUE_8 = (
        8  # A query about physical or virtual network interfaces, their IP/MAC addresses, or types.
    )
    VALUE_9 = 9  # A query about attached peripheral devices, their classes, models, or vendor information.
    VALUE_10 = 10  # A query about running processes, command lines, ancestry, loaded modules, or execution context.
    VALUE_11 = 11  # A query about system services, their names, versions, labels, or properties.
    VALUE_12 = 12  # A query about authenticated user or service sessions, their creation times, or issuer details.
    VALUE_13 = (
        13  # A query about user accounts, their properties, credentials, or domain information.
    )
    VALUE_14 = 14  # A query about multiple users belonging to an administrative group.
    VALUE_15 = 15  # A query about startup configuration items, their run modes, start types, or current states.
    VALUE_16 = 16  # A Windows-specific query about registry keys, their paths, security descriptors, or modification times.
    VALUE_17 = (
        17  # A Windows-specific query about registry values, their data types, content, or names.
    )
    VALUE_18 = 18  # A Windows-specific query about prefetch files, their run counts, last execution times, or existence.
    VALUE_99 = 99  # The query type was not mapped to a standard category. See the query_type attribute for source-specific value.
