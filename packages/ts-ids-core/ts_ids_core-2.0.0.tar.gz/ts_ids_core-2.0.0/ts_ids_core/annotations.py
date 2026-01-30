"""Type hints used throughout ``ts-ids-core``."""

from dataclasses import dataclass
from decimal import Decimal
from typing import AbstractSet, Any, Dict, Iterable, Mapping, Optional, TypeVar, Union
from uuid import UUID

import annotated_types
from pydantic import BeforeValidator, GetJsonSchemaHandler, PlainSerializer
from pydantic.json_schema import JsonSchemaValue
from pydantic_core import core_schema
from typing_extensions import Annotated, ClassVar

#: A type annotation to explicitly describe a field as nullable (i.e. the field can be a given type or `None`).
#: This is equivalent to `typing.Optional` but does not conflict with required and optional field terminology and is consistent with TetraScience terminology.
#: A field can be optional in the schema but also nullable.
Nullable = Optional
#: A type annotation to denote a field can be either a string or `None`.
NullableString = Nullable[str]
#: A type annotation to denote a field can be either a boolean or `None`.
NullableBoolean = Nullable[bool]
#: A type annotation to denote a field can be either a float or `None`.
NullableNumber = Nullable[float]
#: `NullableInt` indicates "the value is likely an integer, but since Athena doesn't
#: distinguish between integers and floats, we'll specify the value as the
#: more-permissive `float` type."
NullableInt = NullableNumber

#: Copied from `pydantic.typing` because they are not import-able.
IntStr = Union[int, str]
AbstractSetIntStr = AbstractSet[IntStr]
DictStrAny = Dict[str, Any]
MappingIntStrAny = Mapping[IntStr, Any]

T = TypeVar("T")


class RequiredAnnotation:
    """Annotation metadata indicating that a field in a Programmatic IDS class is required."""


Required = Annotated[T, RequiredAnnotation()]
"""
Define a field as ``Required[<type>]``, for example ``Required[str]`` to indicate that
this IDS field should be "required" when exported to JSON Schema
"""


class AbstractAnnotation:
    """
    Annotation metadata indicating that a field in a Programmatic IDS class is abstract.

    This means it is a field which should be overridden in a child class which inherits
    from the base class where it appears.
    """


Abstract = Annotated[T, AbstractAnnotation()]
"""
An abstract field is meant to be overridden in a child class which inherits from a base class.

For example, the ``TetraDataSchema`` class contains the ``Abstract`` field ``ids_type``: each individual
IDS which inherits from ``TetraDataSchema`` is meant to override ``ids_type`` with a constant value
specific to that IDS.
An ``UnimplementedAbstractField`` error will be raised if abstract fields are not implemented before trying
to use them.

Abstract fields can be used in an ``IdsElement`` class definition like ``foo: Abstract[str] = IdsField()``.
"""


def validate_uuid(value: Any) -> "UUIDStr":
    """
    Validate that the input value is a ``uuid.UUID`` or a valid ``str``
    representation of a UUID.
    """
    if isinstance(value, UUID):
        return str(value)
    if isinstance(value, str):
        # calling UUID validates that the string has a valid UUID format
        return str(UUID(value))

    raise ValueError(
        "Invalid value type for UUID field: value must be an instance of `uuid.UUID` or `str`"
    )


#: UUIDValidator is a Pydantic BeforeValidator to add as metadata to an Annotated string type.
#: This validator will validate that strings are valid UUIDs and will convert UUID instances to strings.
#:
#: .. code::
#:
#:     class Model(IdsElement):
#:         uuid_field: Annotated[str, UUIDValidator]
#:
#:     uuid_instance = UUID('d7696855-efc7-42eb-ac58-6cc588bf3c5c')
#:     uuid_string = 'd7696855-efc7-42eb-ac58-6cc588bf3c5c'
#:     invalid_uuid_string = "invalid"
#:
#:     assert Model(uuid_field=uuid_instance).uuid_field == 'd7696855-efc7-42eb-ac58-6cc588bf3c5c'
#:     assert Model(uuid_field=uuid_string).uuid_field == 'd7696855-efc7-42eb-ac58-6cc588bf3c5c'
#:
#:     Model(uuid_field=uuid_string)
#:     """
#:     Value error, badly formed hexadecimal UUID string [type=value_error, input_value='invalid', input_type=str]
#:     """
UUIDValidator = BeforeValidator(validate_uuid)


#: A string representation of a UUID.
#:
#: Fields of this type are exported as strings when calling
#: :py:meth:`IdsElement.model_dump() <ts_ids_core.base.ids_element.IdsElement.model_dump>`.
#:
#: This means these UUID fields are compatible with ``jsonschema`` validation in
#: Python, where UUID fields need to validate against the ``"string"`` JSON Schema
#: type.
#:
#: UUID fields could use ``uuid.UUID`` as their field type, which has similar
#: Pydantic validation, but those fields are exported as ``uuid.UUID`` instances when
#: calling ``IdsElement.dict`` which is not compatible with ``jsonschema`` validation.
UUIDStr = Annotated[str, UUIDValidator]


class PrimaryKey:
    """Class to initialize as metadata in `Annotated` types to designate the type a primary key"""

    pk_metadata_field = "@primary_key"

    @classmethod
    def __get_pydantic_json_schema__(
        cls, core_schema: core_schema.CoreSchema, handler: GetJsonSchemaHandler
    ) -> JsonSchemaValue:
        """
        Add '@primary_key' to the JSON schema metadata for fields annotated with
        `PrimaryKey()`.
        """
        # First generate what the schema would have been, excluding this annotation
        field_schema = handler(core_schema)
        field_schema = handler.resolve_ref_schema(field_schema)
        # Add to the generated schema
        field_schema.update({PrimaryKey.pk_metadata_field: True})
        return field_schema


#: A UUID primary key.
#:
#: See ``UUIDForeignKey`` for example usage.
UUIDPrimaryKey = Required[Annotated[UUIDStr, PrimaryKey()]]


@dataclass(frozen=True)
class ForeignKey:
    """Class to initialize as metadata in `Annotated` types to designate the type a foreign key"""

    ids_field_arg: str = "primary_key"
    pk_reference_field: str = "@foreign_key"


#: A UUID foreign key.
#:
#: Example class using this type and UUIDPrimaryKey:
#:
#: .. code::
#:
#:     class Method(IdsElement):
#:         pk: UUIDPrimaryKey
#:
#:     class Result(IdsElement):
#:         fk_method: UUIDForeignKey = IdsField(
#:             primary_key="/properties/methods/items/properties/pk"
#:         )
#:
#:
#:     class Model(TetraDataSchema):
#:         schema_extra_metadata: ClassVar[SchemaExtraMetadataType] = {
#:             "$id": "",
#:             "$schema": "http://json-schema.org/draft-07/schema#",
#:         }
#:         ids_type: Required[Literal["demo"]] = IdsField(
#:             default="demo", alias="@idsType"
#:         )
#:         ids_version: Required[Literal["v1.0.0"]] = IdsField(
#:             default="v1.0.0", alias="@idsVersion"
#:         )
#:         ids_namespace: Required[Literal["common"]] = IdsField(
#:             default="common", alias="@idsNamespace"
#:         )
#:         methods: List[Method]
#:         results: List[Result]
#:
#: A UUIDForeignKey must be defined with a `primary_key` passed to `IdsField`. This is
#: a JSON pointer which points to the location of the primary key in the JSON schema,
#: and this is validated when IdsSchema or TetraDataSchema classes are defined.
#: This validation will only run on classes inheriting from IdsSchema or TetraDataSchema
#: which do not contain any abstract fields (fields annotated with `Abstract`),
#: i.e. only complete top-level schemas include this validation of foreign keys.
UUIDForeignKey = Required[Annotated[UUIDStr, ForeignKey()]]


class _DecimalNumber:
    """
    A class which changes Pydantic's JSON field schema for Decimal types
    to 'type': 'number'. This class should be added as metadata to an
    Annotated Decimal type. Example:

            class Model(IdsElement):
                foo: Annotated[Decimal, _DecimalNumber()]

            Model.model_json_schema()
            >> {
            "additionalProperties": False,
            "properties": {"foo": {"type": "number"}},
            "type": "object",
            }
    """

    location: ClassVar[str] = "ts_ids_core.annotations.DecimalNumber"

    @classmethod
    def __get_pydantic_json_schema__(
        cls, core_schema: core_schema.CoreSchema, handler: GetJsonSchemaHandler
    ) -> JsonSchemaValue:
        """
        Replace the default `anyOf` schema produced by Pydantic with {"type": "number"}
        """
        # First generate what the schema would have been, excluding this annotation
        field_schema = handler(core_schema)
        field_schema = handler.resolve_ref_schema(field_schema)
        # Remove standard decimal schema
        field_schema.pop("anyOf")
        # Replace with number type
        field_schema.update({"type": "number"})
        return field_schema


class _DecimalString:
    """
    A class which changes Pydantic's JSON field schema for Decimal types
    to 'type': 'string'. This class should be added as metadata to an
    Annotated Decimal type. Example:

            class Model(IdsElement):
                foo: Annotated[Decimal, _DecimalString()]

            Model.model_json_schema()
            >> {
            "additionalProperties": False,
            "properties": {"foo": {"type": "string"}},
            "type": "object",
            }
    """

    location: ClassVar[str] = "ts_ids_core.annotations.DecimalString"

    @classmethod
    def __get_pydantic_json_schema__(
        cls, core_schema: core_schema.CoreSchema, handler: GetJsonSchemaHandler
    ) -> JsonSchemaValue:
        """
        Replace the default `anyOf` schema produced by Pydantic with {"type": "string"}
        """
        # First generate what the schema would have been, excluding this annotation
        field_schema = handler(core_schema)
        field_schema = handler.resolve_ref_schema(field_schema)
        # Remove standard decimal schema
        field_schema.pop("anyOf")
        # Replace with string type
        field_schema.update({"type": "string"})
        return field_schema


#: A Decimal type whose JSON schema type is ``number`` and whose instance's field
#: value when serialized to JSON is a float value. This type preserves the standard
#: python ``decimal.Decimal`` type when not serializing to JSON. Example:
#:
#: .. code::
#:
#:     class Model(IdsElement):
#:         foo: DecimalNumber
#:
#:     model = Model(foo="1.500")
#:
#:     assert model.model_json_schema() == {
#:            "additionalProperties": False,
#:            "properties": {"foo": {"type": "number"}},
#:            "type": "object",
#:        }
#:     assert model.model_dump() == {"foo": Decimal("1.500")}
#:     assert model.model_dump_json() == '{"foo":1.5}'
DecimalNumber = Annotated[
    Decimal,
    _DecimalNumber(),
    PlainSerializer(lambda x: float(x), return_type=float, when_used="json"),
]


#: A Decimal type whose JSON schema type is ``string`` and whose instance's field
#: value when serialized to JSON is a string value. This type preserves the standard
#: python ``decimal.Decimal`` type when not serializing to JSON. Example:
#:
#: .. code::
#:
#:     class Model(IdsElement):
#:         foo: DecimalString
#:
#:     model = Model(foo="1.500")
#:
#:     assert model.model_json_schema() == {
#:            "additionalProperties": False,
#:            "properties": {"foo": {"type": "string"}},
#:            "type": "object",
#:        }
#:     assert model.model_dump() == {"foo": Decimal("1.500")}
#:     assert model.model_dump_json() == '{"foo": "1.500"}'
DecimalString = Annotated[
    Decimal,
    _DecimalString(),
    PlainSerializer(lambda x: str(x), return_type=str, when_used="json"),
]


def fixed_length(length: int) -> annotated_types.Len:
    """Annotation metadata meaning a sequence has a fixed length.

    For example, to define a list of strings of length 2:
    ``my_array: Annotated[List[str], fixed_length(2)]``
    """
    return annotated_types.Len(length, length)


def resolve_length_annotation_metadata(
    annotations: Iterable[Any],
) -> Optional[annotated_types.Len]:
    """Find the min and max length of a sequence from its `Annotated` metadata

    If there is duplication, the later elements take precedence, to match
    Pydantic. For example, ``[Len(2, 2), MinLen(1)]`` returns ``Len(1, 2)``, the
    min_length of 2 in the first element is overwritten by 1 from the second element.
    """
    # In the annotated_types ecosystem, min_length is 0 by default
    min_length = 0
    max_length = None
    any_constraints = False
    for annotation in annotations:
        if isinstance(annotation, annotated_types.MinLen):
            min_length = annotation.min_length
            any_constraints = True
        elif isinstance(annotation, annotated_types.MaxLen):
            max_length = annotation.max_length
            any_constraints = True
        elif isinstance(annotation, annotated_types.Len):
            min_length = annotation.min_length
            max_length = annotation.max_length
            any_constraints = True
    if not any_constraints:
        return None
    return annotated_types.Len(min_length, max_length)
