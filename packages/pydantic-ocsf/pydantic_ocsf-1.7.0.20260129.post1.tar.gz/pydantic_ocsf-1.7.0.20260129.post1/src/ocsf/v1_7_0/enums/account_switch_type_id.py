"""The normalized identifier of the account switch method. enumeration."""

from enum import IntEnum


class AccountSwitchTypeId(IntEnum):
    """The normalized identifier of the account switch method.

    See: https://schema.ocsf.io/1.7.0/data_types/account_switch_type_id
    """

    VALUE_0 = 0  # The account switch type is unknown.
    VALUE_1 = 1  # A utility like <code>sudo</code>, <code>su</code>, or equivalent was used to perform actions in the context of another user.
    VALUE_2 = 2  # An API like <code>ImpersonateLoggedOnUser()</code> or equivalent was used to perform actions in the context of another user.
    VALUE_99 = 99  # The account switch type is not mapped. See the <code>account_switch_type</code> attribute, which contains a data source specific value.
