"""The normalized severity identifier that maps severity levels to standard severity levels. For example CIS Benchmark: <code>Level 2</code> maps to <code>4</code> (High), <code>Level 1</code> maps to <code>3</code> (Medium). For DISA STIG: <code>CAT I</code> maps to <code>5</code> (Critical), <code>CAT II</code> maps to <code>4</code> (High), and <code>CAT III</code> maps to <code>3</code> (Medium). enumeration."""

from enum import IntEnum


class SeverityId(IntEnum):
    """The normalized severity identifier that maps severity levels to standard severity levels. For example CIS Benchmark: <code>Level 2</code> maps to <code>4</code> (High), <code>Level 1</code> maps to <code>3</code> (Medium). For DISA STIG: <code>CAT I</code> maps to <code>5</code> (Critical), <code>CAT II</code> maps to <code>4</code> (High), and <code>CAT III</code> maps to <code>3</code> (Medium).

    See: https://schema.ocsf.io/1.7.0/data_types/severity_id
    """

    VALUE_0 = 0  # The severity is unknown.
    VALUE_1 = 1  # Informational message. No action required.
    VALUE_2 = 2  # The user decides if action is needed.
    VALUE_3 = 3  # Maps to CIS Benchmark <code>Level 1</code> - Essential security settings recommended for all systems, or DISA STIG <code>CAT III</code> - Action is required but the situation is not serious at this time.
    VALUE_4 = 4  # Maps to CIS Benchmark <code>Level 2</code> - More restrictive and security-focused settings for sensitive environments, or DISA STIG <code>CAT II</code> - Action is required immediately.
    VALUE_5 = 5  # Maps to DISA STIG <code>CAT I</code> - Action is required immediately and the scope is broad.
    VALUE_6 = 6  # An error occurred but it is too late to take remedial action.
    VALUE_99 = 99  # The severity is not mapped. See the <code>severity</code> attribute, which contains a data source specific value.
