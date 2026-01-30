from __future__ import annotations

import re
from typing import Any, ClassVar, TypeVar

from pydantic import GetJsonSchemaHandler, field_validator
from pydantic.json_schema import JsonSchemaValue
from pydantic_core.core_schema import CoreSchema

from ts_ids_core.annotations import Abstract, Required
from ts_ids_core.base.ids_element import IdsElement, SchemaExtraMetadataType
from ts_ids_core.base.ids_field import IdsField

IdsSchemaVersion = TypeVar("IdsSchemaVersion", str, type(None))


class IdsSchema(IdsElement):
    """
    Base top-level IDS.
    """

    #: '$id' and '$schema' are required fields in the IDS JSON schema. Their values are
    #:    the URL where the IDS is published and the JSON Schema version, respectively.
    #:    The former must be overridden in the child class but the latter should not.
    #:    for example:
    #:
    #:    .. code::
    #:
    #:        from typing import ClassVar, Dict, Union
    #:
    #:        from ts_ids_core.schema import IdsSchema
    #:
    #:        class MyIdsSchema(IdsSchema):
    #:            schema_extra_metadata: ClassVar[Dict[str, Union[str, int, float]]] = {
    #:                **IdsSchema.schema_extra_metadata,
    #:                "$id": "https://ids.tetrascience.com/common/instrument-a/v1.0.0/schema.json"
    #:            }
    #:
    #:    Note that the `ClassVar` type hint must be provided in order to indicate that
    #:    `schema_extra_metadata` is not an IDS Field.

    _validate_foreign_keys: ClassVar[bool] = True
    schema_extra_metadata: ClassVar[SchemaExtraMetadataType] = {
        "$id": NotImplemented,
        "$schema": "http://json-schema.org/draft-07/schema#",
    }

    ids_type: Abstract[Required[str]] = IdsField(
        alias="@idsType",
        description="Also known as IDS slug. Defined by TetraScience.",
    )
    ids_version: Abstract[Required[str]] = IdsField(
        alias="@idsVersion",
        description="IDS version. Defined by TetraScience.",
    )
    ids_namespace: Abstract[Required[str]] = IdsField(
        alias="@idsNamespace",
        description="IDS namespace. Defined by TetraScience.",
    )

    @field_validator("ids_version", mode="after")
    @classmethod
    def is_valid_version_string(cls, value: Any) -> IdsSchemaVersion:
        """
        Assert that the passed-in value conforms to semantic versioning if the value
        is not `None`.

        :param value: The passed-in value to be validated.
        :return:
            The passed-in value, unchanged.
        """
        version_regex = re.compile(r"^v\d{1,2}\.\d{1,2}\.\d{1,2}")

        if not version_regex.search(value):
            raise ValueError(f"'{value}' is not a valid semantic version.")

        return value


class TetraDataSchema(IdsSchema):
    """
    Top-level IDS designed to follow Tetra Data conventions.
    """

    @classmethod
    def __get_pydantic_json_schema__(
        cls, core_schema: CoreSchema, handler: GetJsonSchemaHandler
    ) -> JsonSchemaValue:
        """
        Alter JSON schema to add 'is_tetra_data_schema' which denotes that this
        model should conform to Tetra Data conventions.

        :param core_schema: Core Pydantic Schema
        :param handler: Handler to call into the next JSON schema generation function.
                        Provided by Pydantic.
        :return: Altered JSON schema
        """
        json_schema = handler(core_schema)
        json_schema = handler.resolve_ref_schema(json_schema)
        json_schema["is_tetra_data_schema"] = True
        return json_schema
