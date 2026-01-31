"""File object."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from pydantic import Field

from ocsf._base import OCSFBaseModel

if TYPE_CHECKING:
    from ocsf.v1_7_0.enums.confidentiality_id import ConfidentialityId
    from ocsf.v1_7_0.enums.drive_type_id import DriveTypeId
    from ocsf.v1_7_0.enums.type_id import TypeId
    from ocsf.v1_7_0.objects.digital_signature import DigitalSignature
    from ocsf.v1_7_0.objects.encryption_details import EncryptionDetails
    from ocsf.v1_7_0.objects.fingerprint import Fingerprint
    from ocsf.v1_7_0.objects.key_value_object import KeyValueObject
    from ocsf.v1_7_0.objects.object import Object
    from ocsf.v1_7_0.objects.product import Product
    from ocsf.v1_7_0.objects.url import Url
    from ocsf.v1_7_0.objects.user import User


class File(OCSFBaseModel):
    """The File object represents the metadata associated with a file stored in a computer system. It encompasses information about the file itself, including its attributes, properties, and organizational details.

    See: https://schema.ocsf.io/1.7.0/objects/file
    """

    name: Any = Field(
        ..., description="The name of the file. For example: <code>svchost.exe</code>"
    )
    type_id: TypeId = Field(
        ...,
        description="The file type ID. Note the distinction between a <code>Regular File</code> and an <code>Executable File</code>. If the distinction is not known, or not indicated by the log, use <code>Regular File</code>. In this case, it should not be assumed that a Regular File is not executable.",
    )
    accessed_time: int | None = Field(
        default=None, description="The time when the file was last accessed."
    )
    accessor: User | None = Field(
        default=None, description="The name of the user who last accessed the object."
    )
    attributes: int | None = Field(
        default=None, description="The bitmask value that represents the file attributes."
    )
    company_name: str | None = Field(
        default=None,
        description="The name of the company that published the file. For example: <code>Microsoft Corporation</code>.",
    )
    confidentiality: str | None = Field(
        default=None,
        description="The file content confidentiality, normalized to the confidentiality_id value. In the case of 'Other', it is defined by the event source.",
    )
    confidentiality_id: ConfidentialityId | None = Field(
        default=None,
        description="The normalized identifier of the file content confidentiality indicator.",
    )
    created_time: int | None = Field(
        default=None, description="The time when the file was created."
    )
    creator: User | None = Field(default=None, description="The user that created the file.")
    desc: str | None = Field(
        default=None,
        description="The description of the file, as returned by file system. For example: the description as returned by the Unix file command or the Windows file type.",
    )
    drive_type: str | None = Field(
        default=None,
        description="The drive type, normalized to the caption of the <code>drive_type_id</code> value. In the case of <code>Other</code>, it is defined by the source.",
    )
    drive_type_id: DriveTypeId | None = Field(
        default=None, description="Identifies the type of a disk drive, i.e. fixed, removable, etc."
    )
    encryption_details: EncryptionDetails | None = Field(
        default=None,
        description="The encryption details of the file. Should be populated if the file is encrypted.",
    )
    ext: str | None = Field(
        default=None,
        description="The extension of the file, excluding the leading dot. For example: <code>exe</code> from <code>svchost.exe</code>, or <code>gz</code> from <code>export.tar.gz</code>. [Recommended]",
    )
    hashes: list[Fingerprint] | None = Field(
        default=None, description="An array of hash attributes. [Recommended]"
    )
    include: str | None = Field(default=None, description="")
    internal_name: str | None = Field(
        default=None,
        description='The name of the file as identified within the file itself. This contrasts with the name by which the file is known on disk. Where available, the internal name is widely used by security practitioners and detection content because the on-disk file name is not reliable. On the Windows OS, most PE files contain a <a href="https://learn.microsoft.com/en-us/windows/win32/menurc/versioninfo-resource">VERSIONINFO</a> resource from which the internal name can be obtained. On macOS, binaries can optionally embed a copy of the application\'s Info.plist file which in turn contains the name of the executable.',
    )
    is_deleted: bool | None = Field(
        default=None, description="Indicates if the file was deleted from the filesystem."
    )
    is_encrypted: bool | None = Field(
        default=None, description="Indicates if the file is encrypted."
    )
    is_public: bool | None = Field(
        default=None,
        description="Indicates if the file is publicly accessible. For example in an object's public access in AWS S3",
    )
    is_readonly: bool | None = Field(
        default=None, description="Indicates that the file cannot be modified."
    )
    is_system: bool | None = Field(
        default=None,
        description="The indication of whether the object is part of the operating system.",
    )
    mime_type: str | None = Field(
        default=None,
        description="The Multipurpose Internet Mail Extensions (MIME) type of the file, if applicable.",
    )
    modified_time: int | None = Field(
        default=None, description="The time when the file was last modified."
    )
    modifier: User | None = Field(default=None, description="The user that last modified the file.")
    owner: User | None = Field(default=None, description="The user that owns the file/object.")
    parent_folder: str | None = Field(
        default=None,
        description="The parent folder in which the file resides. For example: <code>c:\\windows\\system32</code>",
    )
    path: Any | None = Field(
        default=None,
        description="The full path to the file. For example: <code>c:\\windows\\system32\\svchost.exe</code>. [Recommended]",
    )
    product: Product | None = Field(
        default=None, description="The product that created or installed the file."
    )
    security_descriptor: str | None = Field(
        default=None, description="The object security descriptor."
    )
    signature: DigitalSignature | None = Field(
        default=None, description="The digital signature of the file."
    )
    size: int | None = Field(default=None, description="The size of data, in bytes.")
    storage_class: str | None = Field(
        default=None,
        description="The storage class of the file. For example in AWS S3: <code>STANDARD, STANDARD_IA, GLACIER</code>.",
    )
    tags: list[KeyValueObject] | None = Field(
        default=None,
        description="The list of tags; <code>{key:value}</code> pairs associated to the file.",
    )
    type_: str | None = Field(default=None, description="The file type.")
    uid: str | None = Field(
        default=None,
        description="The unique identifier of the file as defined by the storage system, such the file system file ID.",
    )
    uri: Any | None = Field(
        default=None,
        description="The file URI, such as those reporting by static analysis tools. E.g., <code>file:///C:/dev/sarif/sarif-tutorials/samples/Introduction/simple-example.js</code>",
    )
    url: Url | None = Field(default=None, description="The URL of the file, when applicable.")
    version: str | None = Field(
        default=None, description="The file version. For example: <code>8.0.7601.17514</code>."
    )
    volume: str | None = Field(
        default=None, description="The volume on the storage device where the file is located."
    )
    xattributes: Object | None = Field(
        default=None,
        description="An unordered collection of zero or more name/value pairs where each pair represents a file or folder extended attribute.</p>For example: Windows alternate data stream attributes (ADS stream name, ADS size, etc.), user-defined or application-defined attributes, ACL, owner, primary group, etc. Examples from DCS: </p><ul><li><strong>ads_name</strong></li><li><strong>ads_size</strong></li><li><strong>dacl</strong></li><li><strong>owner</strong></li><li><strong>primary_group</strong></li><li><strong>link_name</strong> - name of the link associated to the file.</li><li><strong>hard_link_count</strong> - the number of links that are associated to the file.</li></ul>",
    )
