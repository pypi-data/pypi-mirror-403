from __future__ import annotations

import inspect
import json
from enum import Enum
from typing import Any, ClassVar, Dict, Iterable, List, Optional, Set, Type, Union

from pydantic import (
    BaseModel,
    ConfigDict,
    PydanticInvalidForJsonSchema,
    model_validator,
)
from pydantic.json_schema import (
    GenerateJsonSchema,
    JsonSchemaMode,
    JsonSchemaValue,
    model_json_schema,
)
from pydantic_core import (
    CoreSchema,
    PydanticOmit,
    PydanticUndefined,
    core_schema,
    to_jsonable_python,
)
from typing_extensions import Literal, TypeAlias, dataclass_transform

from ts_ids_core.annotations import (
    AbstractAnnotation,
    AbstractSetIntStr,
    DictStrAny,
    MappingIntStrAny,
)
from ts_ids_core.base.ids_field import IdsField
from ts_ids_core.base.ids_undefined_type import IDS_UNDEFINED
from ts_ids_core.base.meta import (
    ForeignKeyField,
    _get_field_default,
    _has_metadata_instance,
    ids_model_init,
)
from ts_ids_core.errors import (
    InvalidSchemaMetadata,
    MultipleTypesError,
    NullableReferenceError,
    UnimplementedAbstractField,
)

#: The type to be used for ``IdsElement.schema_extra_metadata``. Wrap the type in
#: ``typing.ClassVar`` so the full type of ``schema_extra_metadata`` is
#: ``ClassVar[SchemaExtraMetadataType]``
SchemaExtraMetadataType = Dict[str, Union[str, int, float, bool]]
FieldsFilterType = Union[AbstractSetIntStr, MappingIntStrAny, None]
IncEx: TypeAlias = "set[int] | set[str] | dict[int, Any] | dict[str, Any] | None"

# IDS definitions are stored at root of the schema under 'definitions'
DEFAULT_REF_TEMPLATE = "#/definitions/{model}"

# A flag which can be switched to `True` during doc builds, to enable/disable features
# which we only want during building docs.
_BUILDING_DOCS = False


def _python_types_to_json_schema_type(types: Set[Type[Any]]) -> List[str] | str:
    """Convert Python types to JSON Schema types.

    If there are no recognized types (`types` is an empty set or contains only
    non-primitive types), an empty list is returned.

    If there is only 1 type, it is returned as a string rather than list[str], to
    match JSON Schema's type definition.
    """
    json_type: List[str] = []

    if str in types:
        json_type.append("string")
    if int in types:
        json_type.append("integer")
    if float in types:
        json_type.append("number")
    if bool in types:
        json_type.append("boolean")
    if list in types:
        json_type.append("array")

    if type(None) in types:
        json_type.append("null")

    if len(json_type) == 1:
        # When there's just 1 type (not nullable), don't make the type a list
        return json_type[0]

    return json_type


class IdsSchemaGenerator(GenerateJsonSchema):
    """JSON Schema generation which follows TetraScience IDS conventions."""

    schema_dialect = "http://json-schema.org/draft-07/schema#"
    ref_template = DEFAULT_REF_TEMPLATE

    def union_schema(self, schema: core_schema.UnionSchema) -> JsonSchemaValue:
        """Generates a JSON schema that matches a schema that allows values matching any of the given schemas.

        Args:
            schema: The core schema.

        Returns:
            The generated JSON schema.
        """
        generated: JsonSchemaValue = {}

        choices = schema["choices"]

        json_types = []
        for choice in choices:
            # Replicate Pydantic internal logic for tuples
            choice_schema = choice[0] if isinstance(choice, tuple) else choice
            try:
                inner_json_schema = self.generate_inner(choice_schema)
                if "$ref" in inner_json_schema:
                    # There's no easy way to allow a nullable reference, so we won't allow it at all
                    raise MultipleTypesError(
                        "In IDS models, only primitive types may be used in a union."
                    )
                generated.update(inner_json_schema)
                if "type" in generated:
                    # "type" should always be present because `_validate_annotation`
                    # only allows types which have a corresponding JSON Schema "type"
                    json_types.append(generated["type"])
            except (PydanticOmit, PydanticInvalidForJsonSchema):
                # Skip the same cases as Pydantic does by default
                continue
        if len(json_types) > 2 or (len(json_types) == 2 and "null" not in json_types):
            raise MultipleTypesError(
                "Each field may have at most 1 type, optionally combined with 'null'. "
                f"Found the following types: {json_types}."
            )
        if len(json_types) == 1:
            json_types = json_types[0]
        generated["type"] = json_types

        return generated

    def nullable_schema(self, schema: core_schema.NullableSchema) -> JsonSchemaValue:
        """Generates a JSON schema that matches a schema that allows null values.

        Args:
            schema: The core schema.

        Returns:
            The generated JSON schema.
        """

        inner_json_schema = self.generate_inner(schema["schema"])
        if "$ref" in inner_json_schema:
            # There's no easy way to allow a nullable reference, so we won't allow it at all
            raise NullableReferenceError(
                "fields that contain a reference cannot be nullable."
            )

        if isinstance(inner_json_schema["type"], list):
            inner_json_schema["type"].append("null")
        elif isinstance(inner_json_schema["type"], str):
            if inner_json_schema["type"] == "null":
                return inner_json_schema
            inner_json_schema["type"] = [inner_json_schema["type"], "null"]
        return inner_json_schema

    def literal_schema(self, schema: core_schema.LiteralSchema) -> JsonSchemaValue:
        """Generates a JSON schema that matches a literal value.

        This is a modification of Pydantic's built-in literal schema, to define a type
        for `const` values, where Pydantic excludes the "type".
        """
        # Same logic as in Pydantic:
        expected = [v.value if isinstance(v, Enum) else v for v in schema["expected"]]
        # jsonify the expected values
        expected = [to_jsonable_python(v) for v in expected]

        # Custom logic for IDS requirements:
        result: JsonSchemaValue = {"enum": expected}
        if len(expected) == 1:
            result = {"const": expected[0]}

        types = {type(e) for e in expected}
        json_type = _python_types_to_json_schema_type(types)
        if json_type:
            # A type or a nullable type was identified which matches the enum
            result.update({"type": json_type})

        return result

    def enum_schema(self, schema: core_schema.EnumSchema) -> JsonSchemaValue:
        """Generates a JSON schema that matches an Enum value.

        This is a modification of Pydantic's built-in enum schema, to allow the type
        to be nullable, e.g. `"type": ["string", "null"]` for an enum containing strings
        and null values. Pydantic's default is to omit the "type" in this case.
        """
        # Same as in Pydantic:
        enum_type = schema["cls"]
        description = (
            None if not enum_type.__doc__ else inspect.cleandoc(enum_type.__doc__)
        )
        if (
            description == "An enumeration."
        ):  # This is the default value provided by enum.EnumMeta.__new__; don't use it
            description = None
        result: dict[str, Any] = {
            "title": enum_type.__name__,
            "description": description,
        }
        result = {k: v for k, v in result.items() if v is not None}

        expected = [to_jsonable_python(v.value) for v in schema["members"]]

        result["enum"] = expected
        if len(expected) == 1:
            result["const"] = expected[0]

        # Custom logic for IDS requirements:
        types = {type(e) for e in expected}
        json_type = _python_types_to_json_schema_type(types)
        if json_type:
            # A type or a nullable type was identified which matches the enum
            result.update({"type": json_type})

        return result

    def handle_ref_overrides(self, json_schema: JsonSchemaValue) -> JsonSchemaValue:
        """When a `$ref` appears next to other JSON Schema metadata, do nothing.

        In the default `handle_ref_overrides`, Pydantic moves `$ref` into an `allOf` if
        if appears next to sibling metadata.
        However, typically in IDS JSON Schemas, we want to avoid using `allOf` and just
        allow `$ref` with sibling metadata (i.e. this method should do nothing).

        For example, this is allowed:
        `{"description": "My quantity description", "$ref": "#/definitions/ValueUnit"}`.

        Note this is also supported by `jsonref.replace_refs` with `merge_props=True`:
        https://jsonref.readthedocs.io/en/latest/#the-replace-refs-function for any
        downstream handling of `definitions`.
        """
        return json_schema

    def default_schema(self, schema: core_schema.WithDefaultSchema) -> JsonSchemaValue:
        """Generates a JSON schema that matches a schema with a default value.

        Args:
            schema: The core schema.

        Returns:
            The generated JSON schema.
        """
        json_schema = self.generate_inner(schema["schema"])

        return json_schema

    def generate(
        self, schema: CoreSchema, mode: JsonSchemaMode = "validation"
    ) -> JsonSchemaValue:
        """Generates a JSON schema for a specified schema in a specified mode.

        Args:
            schema: A Pydantic model.
            mode: The mode in which to generate the schema. Defaults to 'validation'.

        Returns:
            A JSON schema representing the specified schema.

        Raises:
            PydanticUserError: If the JSON schema generator has already been used to generate a JSON schema.
        """
        json_schema = super().generate(schema)
        if "$defs" in json_schema:
            # Pydantic hard-codes definitions go in "$defs" but we conventionally
            # put them in "definitions" instead
            json_schema["definitions"] = json_schema.pop("$defs")
        # Pydantic offers minimal customization of titles so we have to recursively
        # remove them. Format and default may stop being excluded in a future version
        self._remove_keys_from_schema(json_schema, {"title", "format", "default"})
        return json_schema

    @classmethod
    def _remove_keys_from_schema(cls, schema: DictStrAny, keys: Iterable[str]) -> None:
        """
        Remove the provided keys from the top level, "properties" field and
        "definitions" fields.
        """
        properties = schema.get("properties", {})
        definitions = schema.get("definitions", {})

        for key in keys:
            for _, value in properties.items():
                value.pop(key, None)
            for _, value in definitions.items():
                cls._remove_keys_from_schema(value, keys)
            schema.pop(key, None)


@dataclass_transform(
    # `kw_only_default` is `True` so that `IdsElement` fields can define or omit
    # `IdsField` field descriptors in any order, without creating the type checking issue
    # "Fields without default values cannot appear after fields with default values"
    kw_only_default=True,
    field_specifiers=(IdsField,),
)
class IdsElement(BaseModel):
    """Base class for IDS models."""

    #: Key/value pairs to add to the JSON Schema. These values will not be in the
    #: output of method :meth:`~IdsElement.dict` nor :meth:`~IdsElement.json`. That is,
    #: they won't be in the IDS instance. To indicate that the
    #: key/value pair is abstract and thus expected to be overridden by the child class,
    #: set the value to :const:`NotImplemented`.
    #: Note that in child classes the :any:`typing.ClassVar` type hint must be
    #: provided in order to indicate that ``schema_extra_metadata`` is not an IDS Field.
    schema_extra_metadata: ClassVar[SchemaExtraMetadataType] = {}

    #: Whether or not to validate that foreign keys point to primary keys which exist.
    #: This should be set to `True` on any top-level model which contains both the
    #: primary keys and the foreign keys which point to those primary keys, such as the
    #: `IdsSchema` class.
    _validate_foreign_keys: ClassVar[bool] = False

    #: Contains the union of all foreign keys defined in this `IdsElement`, as well as
    #: all `_foreign_keys` defined in fields of this model whose type inherits from
    #: `IdsElement`.
    _foreign_keys: ClassVar[Set[ForeignKeyField]] = set()

    #: See the `pydantic docs <https://pydantic-docs.helpmanual.io/usage/model_config/#options>`_
    #: for documentation on model configuration.
    model_config = ConfigDict(
        arbitrary_types_allowed=True,
        extra="forbid",
        populate_by_name=True,
        use_enum_values=True,
        coerce_numbers_to_str=True,
        validate_assignment=True,
    )

    @classmethod
    def __pydantic_init_subclass__(cls, **kwargs: Any) -> None:
        """IDS-specific class initialization when an IdsElement class is defined."""
        ids_model_init(cls, **kwargs)

    # no-self-argument: Use `__pydantic_self__` to be consistent with the base class'
    #   constructor implementation.
    def __init__(__pydantic_self__, **data: Any) -> None:  # type: ignore
        """Create a new model by parsing and validating input data from keyword arguments.

        Raises [`ValidationError`][pydantic_core.ValidationError] if the input data cannot be
        validated to form a valid model.

        `__init__` uses `__pydantic_self__` instead of the more common `self` for the first arg to
        allow `self` as a field name.

        This modifies the default Pydantic initialization to remove `IDS_UNDEFINED` items
        before the core Pydantic model instantiation.
        """
        cls = __pydantic_self__.__class__
        # Default values need to be explicitly populated so that they're included when
        # serializing model instances with `exclude_unset`.
        for field_name, field_info in cls.model_fields.items():
            field_alias = (
                field_info.alias if field_info.alias is not None else field_name
            )
            if field_alias in data:
                continue
            if field_name in data and cls.model_config["populate_by_name"]:
                continue
            default = _get_field_default(field_info, call_default_factory=True)
            if default != PydanticUndefined:
                data[field_alias] = default
                continue

        # Any IDS_UNDEFINED fields are removed before validation so that Pydantic treats them as excluded.
        # This catches when IDS_UNDEFINED is explicitly passed as a value when instantiating a model.
        data = {field: value for field, value in data.items() if value != IDS_UNDEFINED}
        super().__init__(**data)

    def __setattr__(self, name: str, value: Any) -> None:
        """
        After setting the attribute according to Pydantic, also treat
        `IDS_UNDEFINED` as an unset field.
        """
        skip = False
        if value in (IDS_UNDEFINED, PydanticUndefined):
            skip = True
            # When model_config has `validate_assignment=True`, validators may fail
            # on `IDS_UNDEFINED`, but they are not run for `PydanticUndefined`
            value = PydanticUndefined

        super().__setattr__(name, value)

        if skip:
            # `IDS_UNDEFINED`` values are treated as unset fields
            self.model_fields_set.discard(name)
            if name in self.__dict__:
                # Replace `PydanticUndefined` with `IDS_UNDEFINED` as the final value
                self.__dict__[name] = IDS_UNDEFINED

    @model_validator(mode="before")
    @classmethod
    def all_abstract_fields_implemented(
        cls,
        data: Any,
    ) -> Any:
        """
        Assert no fields are abstract before being populated, i.e. they have
        all been implemented.
        """
        abstract_fields = []
        for name, field_info in cls.model_fields.items():
            if _has_metadata_instance(field_info.metadata, AbstractAnnotation):
                abstract_fields.append(name)
        if abstract_fields:
            raise UnimplementedAbstractField(
                "One or more fields of are being populated but they are abstract: "
                f"{abstract_fields}. "
                "These fields come from a class with an `Abstract` field annotation, "
                "meaning the child class has to redefine that field concretely before "
                "it can be populated."
            )
        return data

    @classmethod
    def model_json_schema(
        cls,
        by_alias: bool = True,
        ref_template: str = DEFAULT_REF_TEMPLATE,
        schema_generator: Type[GenerateJsonSchema] = IdsSchemaGenerator,
        mode: JsonSchemaMode = "validation",
    ) -> Dict[str, Any]:
        """Generates a JSON schema for a model class.

        :param by_alias:
            Whether to use field aliases in the JSON Schema. Defaults to `True`.
        :param ref_template:
            The ``$ref`` template. Defaults to '#/definitions/{model}', where ``model`` is replaced
            with the :class:`ts_ids_core.base.ids_element.IdsElement`'s class name.
        :return:
            The JSON Schema, as described above.
        :raise UnimplementedAbstractField:
            One or more abstract field(s) are not implemented.
        :raise InvalidSchemaMetadata:
            One or more of the schema metadata fields specified in
            :attr:`ts_ids_core.base.ids_element.schema_extra_metadata` are invalid values.
        """
        if _BUILDING_DOCS:
            # When building API docs, `autodoc-pydantic` calls `model_json_schema` and
            # we want it to succeed so that JSON Schemas are published to docs, even
            # for models which contain abstract fields which would fail the validation
            # below. This flag is set to `True` only during documentation generation, to
            # skip that validation.
            return model_json_schema(
                cls,
                by_alias=by_alias,
                ref_template=DEFAULT_REF_TEMPLATE,
                schema_generator=schema_generator,
                mode=mode,
            )

        unimplemented_abstract_fields = [
            field_name
            for field_name, field_info in cls.model_fields.items()
            if _has_metadata_instance(field_info.metadata, AbstractAnnotation)
        ]

        if unimplemented_abstract_fields:
            raise UnimplementedAbstractField(
                f"Invalid schema because the following abstract fields need to be concretely "
                f"defined: {', '.join(unimplemented_abstract_fields)}"
            )
        invalid_extra_metadata_fields = [
            metadata_key
            for metadata_key, metadata_value in cls.schema_extra_metadata.items()
            if metadata_value is NotImplemented
        ]
        if len(invalid_extra_metadata_fields) > 0:
            raise InvalidSchemaMetadata(
                f"Invalid schema because the following schema metadata fields are not "
                f"implemented: {', '.join(invalid_extra_metadata_fields)}. Set their values using "
                f"the `schema_extra_metadata` class variable."
            )

        return model_json_schema(
            cls,
            by_alias=by_alias,
            ref_template=DEFAULT_REF_TEMPLATE,
            schema_generator=schema_generator,
            mode=mode,
        )

    @classmethod
    def schema_json(
        cls,
        *,
        by_alias: bool = True,
        ref_template: str = DEFAULT_REF_TEMPLATE,
        **dumps_kwargs: Any,
    ) -> str:
        """
        Dump schema to json string. This method preserves Pydantic's v1 BaseModel.schema_json functionality.

        :param by_alias:
            Whether to use field aliases in the JSON Schema. Defaults to `True`.
        :param ref_template:
            The ``$ref`` template. Defaults to '#/definitions/{model}', where ``model`` is replaced
            with the :class:`ts_ids_core.base.ids_element.IdsElement`'s class name.
        :param dumps_kwargs:
            Key word arguments passed to IdsElement.model_json_schema

        :return:
            IdsElement schema as string
        """
        return json.dumps(
            cls.model_json_schema(by_alias=by_alias, ref_template=ref_template),
            **dumps_kwargs,
        )

    @classmethod
    def schema(
        cls, by_alias: bool = True, ref_template: str = DEFAULT_REF_TEMPLATE
    ) -> "DictStrAny":
        """
        Return the JSON Schema as a Python object.

        This is an alias of the `model_json_schema` method which is Pydantic's
        default name for this functionality.
        """
        return cls.model_json_schema(
            by_alias=True,
            ref_template=DEFAULT_REF_TEMPLATE,
            schema_generator=IdsSchemaGenerator,
            mode="validation",
        )

    def model_dump(
        self,
        *,
        mode: Union[Literal["json", "python"], str] = "python",
        include: IncEx = None,
        exclude: IncEx = None,
        by_alias: bool = True,
        exclude_unset: bool = True,
        exclude_defaults: bool = False,
        exclude_none: bool = False,
        round_trip: bool = False,
        warnings: bool = True,
    ) -> "DictStrAny":
        """
        Export to a Python dictionary, excluding any fields whose values are not defined.

        For the other parameters, see :meth:`pydantic.main.BaseModel.model_dump`.

        :param exclude_unset:
            This parameter is not used but is maintained in order to preserve the parent
            class' API.
        :raise NotImplementedError:
            If any value other than the default is passed to ``exclude_unset``. The
            ``exclude_unset`` parameter is only to keep the API consistent with
            the parent class' method, :meth:`pydantic.BaseModel.model_dump`.
        """
        self._raise_if_not_value(
            True,
            exclude_unset,
            NotImplementedError,
            "`exclude_unset` may only be set to `True` for IDS models.",
        )
        return super().model_dump(
            mode=mode,
            include=include,
            exclude=exclude,
            by_alias=by_alias,
            exclude_unset=exclude_unset,
            exclude_defaults=exclude_defaults,
            exclude_none=exclude_none,
            round_trip=round_trip,
            warnings=warnings,
        )

    def dict(
        self,
        *,
        include: IncEx = None,
        exclude: IncEx = None,
        by_alias: bool = True,
        exclude_unset: bool = True,
        exclude_defaults: bool = False,
        exclude_none: bool = False,
    ) -> "DictStrAny":
        """
        Return the model instance as a dictionary.

        This is an alias of the `model_dump` method which is Pydantic's
        default name for this functionality.
        """
        return self.model_dump(
            mode="python",
            include=include,
            exclude=exclude,
            by_alias=by_alias,
            exclude_unset=exclude_unset,
            exclude_defaults=exclude_defaults,
            exclude_none=exclude_none,
        )

    def model_dump_json(
        self,
        *,
        indent: Union[int, None] = None,
        include: IncEx = None,
        exclude: IncEx = None,
        by_alias: bool = True,
        exclude_unset: bool = True,
        exclude_defaults: bool = False,
        exclude_none: bool = False,
        round_trip: bool = False,
        warnings: bool = True,
    ) -> str:
        """
        Export to JSON.

        For the other parameters, see :meth:`pydantic.main.BaseModel.model_dump_json`.

        Note `exclude_unset` may not be used, IDS models always have to exclude unset
        values so that `IDS_UNDEFINED` is handled correctly.

        :param exclude_unset:
            This parameter is not used but is maintained in order to preserve the parent
            class' API.
        :raise NotImplementedError:
            If any value other than the default is passed to ``exclude_unset``. The
            ``exclude_unset`` parameter is only to keep the API consistent with
            the parent class' method, :meth:`pydantic.BaseModel.model_dump_json`.
        """
        self._raise_if_not_value(
            True,
            exclude_unset,
            NotImplementedError,
            "`exclude_unset` may only be set to `True` for IDS models.",
        )
        return super().model_dump_json(
            indent=indent,
            include=include,
            exclude=exclude,
            by_alias=by_alias,
            exclude_unset=exclude_unset,
            exclude_defaults=exclude_defaults,
            exclude_none=exclude_none,
            round_trip=round_trip,
            warnings=warnings,
        )

    @staticmethod
    def _raise_if_not_value(
        expected_value: Any,
        actual_value: Any,
        error_type: Type[Exception],
        message: Optional[str],
    ) -> None:
        """Raise the desired error if `expected_value` does not equal `actual_value`."""
        if actual_value != expected_value:
            raise error_type(message)
