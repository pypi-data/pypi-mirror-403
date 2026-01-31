"""LDAP Person object."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from pydantic import Field

from ocsf._base import OCSFBaseModel

if TYPE_CHECKING:
    from ocsf.v1_1_0.objects.location import Location
    from ocsf.v1_1_0.objects.user import User


class LdapPerson(OCSFBaseModel):
    """The additional LDAP attributes that describe a person.

    See: https://schema.ocsf.io/1.1.0/objects/ldap_person
    """

    cost_center: str | None = Field(
        default=None, description="The cost center associated with the user."
    )
    created_time: int | None = Field(
        default=None, description="The timestamp when the user was created."
    )
    deleted_time: int | None = Field(
        default=None,
        description="The timestamp when the user was deleted. In Active Directory (AD), when a user is deleted they are moved to a temporary container and then removed after 30 days. So, this field can be populated even after a user is deleted for the next 30 days.",
    )
    email_addrs: list[Any] | None = Field(
        default=None, description="A list of additional email addresses for the user."
    )
    employee_uid: str | None = Field(
        default=None,
        description="The employee identifier assigned to the user by the organization.",
    )
    given_name: str | None = Field(default=None, description="The given or first name of the user.")
    hire_time: int | None = Field(
        default=None,
        description="The timestamp when the user was or will be hired by the organization.",
    )
    job_title: str | None = Field(default=None, description="The user's job title.")
    labels: list[str] | None = Field(
        default=None,
        description="The labels associated with the user. For example in AD this could be the <code>userType</code>, <code>employeeType</code>. For example: <code>Member, Employee</code>.",
    )
    last_login_time: int | None = Field(
        default=None, description="The last time when the user logged in."
    )
    ldap_cn: str | None = Field(
        default=None,
        description="The LDAP and X.500 <code>commonName</code> attribute, typically the full name of the person. For example, <code>John Doe</code>.",
    )
    ldap_dn: str | None = Field(
        default=None,
        description="The X.500 Distinguished Name (DN) is a structured string that uniquely identifies an entry, such as a user, in an X.500 directory service For example, <code>cn=John Doe,ou=People,dc=example,dc=com</code>.",
    )
    leave_time: int | None = Field(
        default=None,
        description="The timestamp when the user left or will be leaving the organization.",
    )
    location: Location | None = Field(
        default=None,
        description="The geographical location associated with a user. This is typically the user's usual work location.",
    )
    manager: User | None = Field(
        default=None,
        description="The user's manager. This helps in understanding an org hierarchy. This should only ever be populated once in an event. I.e. there should not be a manager's manager in an event.",
    )
    modified_time: int | None = Field(
        default=None, description="The timestamp when the user entry was last modified."
    )
    office_location: str | None = Field(
        default=None,
        description="The primary office location associated with the user. This could be any string and isn't a specific address. For example, <code>South East Virtual</code>.",
    )
    surname: str | None = Field(default=None, description="The last or family name for the user.")
