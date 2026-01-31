"""The identifier of the normalized digital signature algorithm. enumeration."""

from enum import IntEnum


class AlgorithmId(IntEnum):
    """The identifier of the normalized digital signature algorithm.

    See: https://schema.ocsf.io/1.1.0/data_types/algorithm_id
    """

    VALUE_0 = 0  #
    VALUE_1 = 1  # Digital Signature Algorithm (DSA).
    VALUE_2 = 2  # Rivest-Shamir-Adleman (RSA) Algorithm.
    VALUE_3 = 3  # Elliptic Curve Digital Signature Algorithm.
    VALUE_4 = 4  # Microsoft Authenticode Digital Signature Algorithm.
    VALUE_99 = 99  #
