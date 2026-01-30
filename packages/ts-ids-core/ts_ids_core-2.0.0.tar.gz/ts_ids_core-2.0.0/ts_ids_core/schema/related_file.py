from __future__ import annotations

from ts_ids_core.annotations import Nullable, Required
from ts_ids_core.base.ids_element import IdsElement
from ts_ids_core.base.ids_field import IdsField
from ts_ids_core.schema.value_unit import ValueUnit


class Checksum(IdsElement):
    """Checksum value and algorithm associated with a file."""

    value: Required[str] = IdsField(description="Checksum string value.")
    algorithm: Required[Nullable[str]] = IdsField(
        description="Checksum algorithm, e.g. 'md5', 'sha256'."
    )


class Pointer(IdsElement):
    """
    A pointer stores the location metadata of the file on TDP.
    """

    fileKey: Required[str] = IdsField(description="AWS S3 file key.")
    version: Required[str] = IdsField(description="AWS S3 file version number.")
    bucket: Required[str] = IdsField(description="AWS S3 bucket.")
    type_: Required[str] = IdsField(
        alias="type", description="Type of the file, e.g. 's3file', 'parquet'."
    )
    fileId: Required[str] = IdsField(description="File ID (UUID) in TDP.")


# One instance of this class is an item in the `related_files` array.
class RelatedFile(IdsElement):
    """A reference to a file related to this IDS stored on the Tetra Data Platform."""

    name: Nullable[str] = IdsField(description="File name.")
    path: Nullable[str] = IdsField(description="File path.")
    size: ValueUnit = IdsField(description="File size.")
    checksum: Checksum = IdsField(description="File checksum.")
    pointer: Required[Pointer] = IdsField(
        description="File pointer to location on TDP."
    )
