"""The normalized identifier of the relationship between two software components. enumeration."""

from enum import IntEnum


class RelationshipId(IntEnum):
    """The normalized identifier of the relationship between two software components.

    See: https://schema.ocsf.io/1.5.0/data_types/relationship_id
    """

    VALUE_0 = 0  # The relationship is unknown.
    VALUE_1 = 1  # The component is a dependency of another component. Can be used to define both direct and transitive dependencies.
    VALUE_99 = 99  # The relationship is not mapped. See the <code>relationship</code> attribute, which contains a data source specific value.
