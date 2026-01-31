"""The normalized reputation score identifier. enumeration."""

from enum import IntEnum


class ScoreId(IntEnum):
    """The normalized reputation score identifier.

    See: https://schema.ocsf.io/1.0.0/data_types/score_id
    """

    VALUE_0 = 0  # The reputation score is unknown.
    VALUE_1 = 1  # Long history of good behavior.
    VALUE_2 = 2  # Consistently good behavior.
    VALUE_3 = 3  # Reasonable history of good behavior.
    VALUE_4 = 4  # Starting to establish a history of normal behavior.
    VALUE_5 = 5  # No established history of normal behavior.
    VALUE_6 = 6  # Starting to establish a history of suspicious or risky behavior.
    VALUE_7 = 7  # A site with a history of suspicious or risky behavior. (spam, scam, potentially unwanted software, potentially malicious).
    VALUE_8 = 8  # Strong possibility of maliciousness.
    VALUE_9 = 9  # Indicators of maliciousness.
    VALUE_10 = 10  # Proven evidence of maliciousness.
    VALUE_99 = 99  # The reputation score is not mapped. See the <code>rep_score</code> attribute, which contains a data source specific value.
