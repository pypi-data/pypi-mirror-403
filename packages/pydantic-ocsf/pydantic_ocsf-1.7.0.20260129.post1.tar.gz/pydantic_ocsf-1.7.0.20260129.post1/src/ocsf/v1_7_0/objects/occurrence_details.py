"""Occurrence Details object."""

from __future__ import annotations

from pydantic import Field

from ocsf._base import OCSFBaseModel


class OccurrenceDetails(OCSFBaseModel):
    """Details about where in the target entity, specified information was discovered. Only the attributes, relevant to the target entity type should be populated.

    See: https://schema.ocsf.io/1.7.0/objects/occurrence_details
    """

    cell_name: str | None = Field(
        default=None, description="The cell name/reference in a spreadsheet. e.g <code>A2</code>"
    )
    column_name: str | None = Field(
        default=None,
        description="The column name in a spreadsheet, where the information was discovered.",
    )
    column_number: int | None = Field(
        default=None,
        description="The column number in a spreadsheet or a plain text document, where the information was discovered.",
    )
    end_line: int | None = Field(
        default=None,
        description="The line number of the last line of the file, where the information was discovered.",
    )
    json_path: str | None = Field(
        default=None,
        description="The JSON path of the attribute in a json record, where the information was discovered",
    )
    page_number: int | None = Field(
        default=None,
        description="The page number in a document, where the information was discovered.",
    )
    record_index_in_array: int | None = Field(
        default=None,
        description="The index of the record in the array of records, where the information was discovered. e.g. the index of a record in an array of JSON records in a file.",
    )
    row_number: int | None = Field(
        default=None,
        description="The row number in a spreadsheet, where the information was discovered.",
    )
    start_line: int | None = Field(
        default=None,
        description="The line number of the first line of the file, where the information was discovered.",
    )
