"""The normalized identifier for the authentication factor. enumeration."""

from enum import IntEnum


class FactorTypeId(IntEnum):
    """The normalized identifier for the authentication factor.

    See: https://schema.ocsf.io/1.7.0/data_types/factor_type_id
    """

    VALUE_0 = 0  #
    VALUE_1 = 1  # User receives and inputs a code sent to their mobile device via SMS text message.
    VALUE_2 = 2  # The user responds to a security question as part of a question-based authentication factor
    VALUE_3 = 3  # System calls the user's registered phone number and requires the user to answer and provide a response.
    VALUE_4 = 4  # Devices that verify identity-based on user's physical identifiers, such as fingerprint scanners or retina scanners.
    VALUE_5 = 5  # Push notification is sent to user's registered device and requires the user to acknowledge.
    VALUE_6 = 6  # Physical device that generates a code to be used for authentication.
    VALUE_7 = 7  # Application generates a one-time password (OTP) for use in authentication.
    VALUE_8 = 8  # A code or link is sent to a user's registered email address.
    VALUE_9 = 9  # Typically involves a hardware token, which the user physically interacts with to authenticate.
    VALUE_10 = 10  # Web-based API that enables users to register devices as authentication factors.
    VALUE_11 = 11  # The user enters a password that they have previously established.
    VALUE_99 = 99  #
