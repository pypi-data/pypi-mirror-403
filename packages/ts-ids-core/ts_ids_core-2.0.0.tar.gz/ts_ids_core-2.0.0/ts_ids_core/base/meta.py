# Disabled because this error is incorrectly raised for all ``from pydantic`` imports.
# pylint: disable=no-name-in-module
from __future__ import annotations

import typing
from dataclasses import dataclass
from decimal import Decimal
from typing import Any, Callable, Dict, Generator, List, Sequence, Set, Type, Union

from jsonref import replace_refs
from pydantic import BaseModel
from pydantic.fields import FieldInfo
from pydantic_core import PydanticUndefined
from typing_extensions import Annotated, Optional, Tuple, get_args, get_origin

from ts_ids_core._internal import is_literal
from ts_ids_core.annotations import (
    ForeignKey,
    PrimaryKey,
    RequiredAnnotation,
    UUIDValidator,
    _DecimalNumber,
    _DecimalString,
)
from ts_ids_core.base.ids_undefined_type import IDS_UNDEFINED, IdsUndefinedType
from ts_ids_core.errors import (
    InvalidField,
    InvalidForeignKeyField,
    InvalidPrimaryKeyField,
    InvalidSchemaMetadata,
    InvalidTypeError,
    MultipleTypesError,
    UnimplementedAbstractField,
)

if typing.TYPE_CHECKING:
    # We need `IdsElement` to type annotate `IdsModel` but that would make a recursive
    # import, so put it in a `TYPE_CHECKING` block.
    from ts_ids_core.base.ids_element import IdsElement

__all__ = ["ids_model_init"]


@dataclass(frozen=True)
class ForeignKeyRelation:
    target: str


@dataclass(frozen=True)
class ForeignKeyField:
    """
    Represents a foreign key: the model it's contained in, the field's name, and its
    relation to a primary key.
    """

    model: Type[IdsElement]
    field_name: str
    foreign_key_relation: ForeignKeyRelation

    def __str__(self):
        return (
            f"{self.model}, field '{self.field_name}', with primary key reference: "
            f"'{self.foreign_key_relation.target}'"
        )

    @staticmethod
    def _raise(field_name: str):
        raise InvalidForeignKeyField(
            f"The field '{field_name}' of type UUIDForeignKey must have "
            "`primary_key` defined in the IdsField definition, such as "
            '`fk_samples: UUIDForeignKey = IdsField(primary_key="/properties/samples/items/properties/pk")`'
        )

    @classmethod
    def from_model_field(cls, model: Type[IdsElement], field_name: str):
        field = model.model_fields.get(field_name)
        schema_extra = field.json_schema_extra

        if schema_extra is None:
            cls._raise(field_name)

        pk_reference = schema_extra.get(ForeignKey.pk_reference_field)
        if pk_reference is None:
            cls._raise(field_name)

        return cls(model, field_name, ForeignKeyRelation(pk_reference))


def _separate_type_hint_arguments(field_type_hint: Type) -> Generator[Type, None, None]:
    """
    Separate all type arguments in a type hint including nested arguments in container
    types and the container types themselves.

    Examples:
        Tuple[int, str, float] -> (tuple, int, str, float)
        Sequence[Tuple[int, Tuple[str, str]]] -> (tuple, int, tuple, str, str)

    :param field_type_hint: raw type hint of field defined in IdsElement subclass

    :return:
        A generator containing the type hint's individual arguments
    """
    origin = get_origin(field_type_hint)
    if origin is None:
        yield field_type_hint
        return

    yield origin
    for arg in get_args(field_type_hint):
        yield from _separate_type_hint_arguments(arg)


def get_foreign_keys_from_type_hint(field_type_hint: Type[Any]) -> Set[ForeignKeyField]:
    """
    Access the `_foreign_keys` attribute of an IdsElement from its type hint, including
    when it is nested in container types like List.


    :param field_type_hint: raw type hint of field defined in IdsElement subclass

    :return: IdsElement._foreign_keys for the nested type hint
    """
    foreign_keys: Set[ForeignKeyField] = set()
    for arg in _separate_type_hint_arguments(field_type_hint):
        if hasattr(arg, "_foreign_keys"):
            foreign_keys.update(arg._foreign_keys)  # pylint: disable=protected-access
    return foreign_keys


PROPERTIES_KEYWORD = "properties"
ITEMS_KEYWORD = "items"


def _get_primary_key_json_pointers(
    schema: Dict[str, Any], pointer: str = ""
) -> Set[str]:
    """Find all JSON pointers to primary keys in a JSON schema."""
    primary_keys: Set[str] = set()

    if PrimaryKey.pk_metadata_field in schema:
        primary_keys.add(pointer)

    # Recursively visit objects (containing properties) and arrays (containing items)
    if PROPERTIES_KEYWORD in schema:
        for property_name, property_schema in schema[PROPERTIES_KEYWORD].items():
            primary_keys.update(
                _get_primary_key_json_pointers(
                    schema=property_schema,
                    pointer=f"{pointer}/{PROPERTIES_KEYWORD}/{property_name}",
                )
            )
    elif ITEMS_KEYWORD in schema:
        primary_keys.update(
            _get_primary_key_json_pointers(
                schema[ITEMS_KEYWORD], pointer=f"{pointer}/{ITEMS_KEYWORD}"
            )
        )

    return primary_keys


def _validate_foreign_keys(schema: Dict[str, Any], foreign_keys: Set[ForeignKeyField]):
    """
    Validate that the JSON pointers defined in all foreign keys are pointers to primary
    keys in the JSON schema.
    """
    dereferenced_schema = replace_refs(schema)
    primary_key_paths = _get_primary_key_json_pointers(dereferenced_schema)  # type: ignore
    missing_targets = tuple(
        foreign_key
        for foreign_key in foreign_keys
        if foreign_key.foreign_key_relation.target not in primary_key_paths
    )

    if not missing_targets:
        # All foreign keys point to primary keys which exist
        return

    separator = "\n  "

    if primary_key_paths:
        primary_key_hint = (
            "The following are all of the primary key paths in this JSON "
            f"schema:{separator}{separator.join(primary_key_paths)}"
        )
    else:
        primary_key_hint = (
            "There are no `UUIDPrimaryKey` fields defined in this schema."
        )

    raise InvalidForeignKeyField(
        "The following foreign key fields point to primary keys which were "
        f"not found in the JSON schema: {separator}"
        f"{separator.join([str(key) for key in missing_targets])}."
        "\n"
        f"{primary_key_hint}"
    )


def _has_metadata_instance(metadata: List[Any], metadata_class: Any) -> bool:
    """
    Check that a field has an instance of a class in it field.metadata array.

    :param metadata: A field's FieldInfo.metadata value
    :param metadata_class: class of expected instance to find in metadata array

    :return:
        True if field contains the instance, otherwise False
    """

    return any([isinstance(value, metadata_class) for value in metadata])


def _strip_annotated(
    annotation: Union[Type[Any], None], annotation_metadata: Optional[List] = None
) -> Tuple[Union[Type[Any], None], List]:
    """
    Remove `Annotated` from a field's annotation and return the inner most type
    with concatenated annotation metadata. Examples:

    1. `Annotated[X, "foo"]`, return X, ["foo"]
    2. `Annotated[Annotated[X, "foo"], "bar"]`, return X, ["foo", ]

    Also recurse to handle nested `Annotated`.
    """
    if annotation_metadata is None:
        annotation_metadata = []

    if get_origin(annotation) is Annotated:
        annotation_args = get_args(annotation)
        if annotation_args is not None:
            annotation_metadata += annotation_args[1:]
        return _strip_annotated(annotation_args[0], annotation_metadata)
    return annotation, annotation_metadata


def _validate_annotation(
    field: str,
    field_annotation: Union[Type[Any], None],
    field_metadata: List[Any] = None,
) -> None:
    """
    Validate that a field's annotation is a primitive, a nullable primitive,
    or a non-primitive (e.g. an IdsElement).
    """
    message = (
        f"Found `{field}` with type `{field_annotation}`. "
        "In IDS models, properties may only have a single type, they cannot be "
        "a union of types, except for making primitive types nullable. For "
        "example, `Nullable[str]` is allowed, but `Nullable[MyModel]` is not "
        "(where `MyModel` is a non-primitive type like another IDS model), "
        "and `Union[str, float]` is not allowed because it contains 2 "
        "primitive types."
    )
    # Only interested in the underlying types, not `Annotated`
    field_annotation, annotation_metadata = _strip_annotated(field_annotation, [])

    # If an Annotated type is defined within a subscriptable type such as Nullable[Annotated[str, 'foo']]
    # Then the metadata will live within the annotated type's metadata and not the field defined with Nullable.
    # So, we update field_metadata to include the annotation's metadata.
    if field_metadata is not None:
        field_metadata += annotation_metadata
    else:
        field_metadata = annotation_metadata

    separated_type_hint = list(_separate_type_hint_arguments(field_annotation))
    if IdsUndefinedType in separated_type_hint:
        raise InvalidTypeError(
            f"Field `{field}` has an `IdsUndefinedType` outside of a `Union`. "
            "`IdsUndefinedType` may only be used as part of a union with other types, "
            "it cannot be used in isolation like `foo: IdsUndefinedType` because it is "
            "equivalent to not having a type."
        )

    if field_annotation is Decimal:
        if field_metadata is None or not (
            _has_metadata_instance(field_metadata, _DecimalString)
            or _has_metadata_instance(field_metadata, _DecimalNumber)
        ):
            raise InvalidTypeError(
                f"Python's {Decimal.__name__} type is not allowed as an annotation in `ts-ids-core`."
                f" This is due to Pydantic producing a JSON schema which is incompatible with the TetraScience platform."
                f" Please use one of the provided decimal annotations: {_DecimalString.location} or {_DecimalNumber.location}"
            )

    origin = get_origin(field_annotation)

    if origin is Union:
        field_subtypes = set(get_args(field_annotation))
    elif is_literal(origin):
        # Literal is similar to Union, e.g. `Literal["a", 1, None]` is not allowed
        # because it's like `Union[str, int, None]`
        field_subtypes = set(
            [type(literal_value) for literal_value in get_args(field_annotation)]
        )
    else:
        return
    if len(field_subtypes) > 2:
        raise MultipleTypesError(message)
    if len(field_subtypes) == 2:
        if type(None) not in field_subtypes:
            raise MultipleTypesError(message)

        # The other type must be primitive
        non_null_type = (field_subtypes - {type(None)}).pop()
        if isinstance(non_null_type, type) and issubclass(non_null_type, BaseModel):
            raise MultipleTypesError(message)

    # Continue validation for any non-null subtype, in case it is a union.
    # In practice, Pydantic flattens all unions before the annotation is passed
    # to this function so this subtype shouldn't be a union in practice.
    field_subtypes.discard(type(None))
    subtype = field_subtypes.pop()
    _validate_annotation(field, subtype)


def _get_metadata_from_union(
    annotation: Union[Type[Any], None], target_metadata: Sequence[Any]
) -> List[Any]:
    """Extract `Annotated` metadata from the args of a `Union` type.

    The type `Union[Annotated[str, X], None]` does not count as having the annotation
    metadata `X` by default in Pydantic. We want to be able to find this metadata
    in unions for annotations like `Required`, where `Nullable[Required[str]]` should
    be considered as having `Required` annotation metadata.

    This function traverses `Union` args, finding the target metadata, e.g.
    `get_metadata_from_union(Nullable[Required[str]], (RequiredAnnotation,))`
    returns `[RequiredAnnotation()]`, i.e. the metadata from `Required[]`
    """
    metadata = []
    origin = get_origin(annotation)
    if origin is Annotated:
        subtype, *annotation_metadata = get_args(annotation)
        metadata.extend(_get_metadata_from_union(subtype, target_metadata))
        metadata.extend(
            [
                item
                for item in annotation_metadata
                if isinstance(item, tuple(target_metadata))
            ]
        )

    if origin is Union:
        for subtype in get_args(annotation):
            metadata.extend(_get_metadata_from_union(subtype, target_metadata))
    return metadata


def _validate_reserved_json_schema_extra_fields(
    field_name: str, field_info: FieldInfo
) -> None:
    """
    Validate that the json_schema_extra fields `primary-key`, which is replaced by `@foreign_key`, and
    @primary_key are not contained in types other than UUIDForeignKey or UUIDPrimaryKey.

    :param field_name: Name of field whose FieldInfo.json_schema_extra to inspect
    :param field_info: The field's FieldInfo instance containing the json_schema_extra attribute
    :return: None if the field is valid, otherwise raise and error
    """
    is_foreign_key = (
        _has_metadata_instance(field_info.metadata, ForeignKey)
        and UUIDValidator in field_info.metadata
    )
    is_primary_key = (
        _has_metadata_instance(field_info.metadata, PrimaryKey)
        and UUIDValidator in field_info.metadata
    )

    schema_extra = field_info.json_schema_extra

    if not isinstance(schema_extra, dict):
        return

    if PrimaryKey.pk_metadata_field in schema_extra and not is_primary_key:
        raise InvalidPrimaryKeyField(
            f"The `json_schema_extra['{PrimaryKey.pk_metadata_field}']` argument of IdsField' is reserved for"
            f"fields of type 'UUIDPrimaryKey' and should not be set using IdsField. It is being used with the field "
            f"'{field_name}' of type {field_info.annotation}. If you want to define a primary key field, define"
            f" the field as '<field_name>: UUIDPrimaryKey'."
        )

    if ForeignKey.pk_reference_field in schema_extra and not is_foreign_key:
        raise InvalidForeignKeyField(
            "The `primary_key` argument of IdsField must only be used for a "
            f"field of type `UUIDForeignKey`. It is being used with the field "
            f"'{field_name}' of type {field_info.annotation}."
        )


@dataclass
class DefaultAnnotation:
    """Annotation metadata for defining a default value or default factory.

    This takes precedence over any default value defined using `IdsField`, but
    it is only intended for internal use.

    This is an alternative to the standard way of defining defaults in Pydantic, which
    enables defining defaults in a way which doesn't interfere with Pydantic's tight
    coupling between "is required" and "has no default".
    """

    default: Any = PydanticUndefined
    default_factory: Union[Callable[[], Any], None] = None


def _get_field_default(
    field_info: FieldInfo, call_default_factory: bool = False
) -> Any:
    """
    ts-ids-core has to move defaults into annotation metadata in some cases.
    This function retrieves the default value whether it's stored in the
    `default` and `default_factory` fields of `FieldInfo`, or whether it's
    been moved to annotation metadata.
    """

    annotated_default = next(
        (
            metadata
            # Use `reversed` because the latest metadata is at the back
            for metadata in reversed(field_info.metadata)
            if isinstance(metadata, DefaultAnnotation)
        ),
        None,
    )
    if annotated_default is not None:
        # There is annotation metadata for the default, so temporarily put it
        # back into the relevant `field_info` fields to use the `get_default` method
        # without having to reimplement it. e.g. it handles copying mutable defaults.

        # Get the existing default values
        previous_default = field_info.default
        previous_default_factory = field_info.default_factory
        # Temporarily set the field_info values from annotation metadata
        field_info.default = annotated_default.default
        field_info.default_factory = annotated_default.default_factory
        found_default = field_info.get_default(
            call_default_factory=call_default_factory
        )
        # Restore field_info's existing values
        field_info.default = previous_default
        field_info.default_factory = previous_default_factory

        return found_default

    # No annotation, so use `field_info.get_default` as-is
    return field_info.get_default(call_default_factory=call_default_factory)


def ids_model_init(
    model: Type[IdsElement],
    **kwargs: Any,
) -> None:
    """
    IdsElement subclass initializer to call from __pydantic_init_subclass__
    to enforce correctly defined IdsElement classes.

    :param model:
        The BaseModel class
    :param **kwargs:
        Unused keyword arguments for compatibility with `__pydantic_subclass_init__`
    """
    foreign_keys: Set[ForeignKeyField] = set()
    for field, field_info in model.model_fields.items():
        # Capture metadata like `Required` when it's part of a union, like
        # `Union[Required[str], None]`
        _validate_annotation(field, field_info.annotation, field_info.metadata)
        targeted_metadata_from_unions = _get_metadata_from_union(
            field_info.annotation, (RequiredAnnotation, ForeignKey, PrimaryKey)
        )
        field_info.metadata.extend(targeted_metadata_from_unions)

        _validate_reserved_json_schema_extra_fields(field, field_info)

        # Update model._foreign_keys to include all foreign keys contained in the model's
        # fields which are are IdsElement types that define or have nested foregin keys
        foreign_keys.update(get_foreign_keys_from_type_hint(field_info.annotation))

        # Whether the field is required according to the IDS-specific annotation
        # (This is an extension of Pydantic's functionality)
        is_required = _has_metadata_instance(field_info.metadata, RequiredAnnotation)

        if is_required:
            if field_info.default == IDS_UNDEFINED:
                # IDS_UNDEFINED is the placeholder default value for non-required fields
                # Replace it with Pydantic's "no default" value
                field_info.default = PydanticUndefined

            if (
                field_info.default != PydanticUndefined
                or field_info.default_factory is not None
            ):
                # A default value is defined for a required field
                # The `default` for a required field must be `PydanticUndefined`
                # for Pydantic's JSON Schema generator to work, so we store the
                # default in custom annotation metadata instead.
                # Same for `default_factory`, which must be `None`.
                field_info.metadata.append(
                    DefaultAnnotation(field_info.default, field_info.default_factory)
                )
                field_info.default = PydanticUndefined
                field_info.default_factory = None

            if _has_metadata_instance(field_info.metadata, ForeignKey):
                foreign_keys.add(ForeignKeyField.from_model_field(model, field))

            continue
        # For all non-required fields with no default value defined, change the
        # default value to our own "no default" placeholder
        if (
            field_info.default is PydanticUndefined
            and field_info.default_factory is None
        ):
            field_info.default = IDS_UNDEFINED

    model._foreign_keys = model._foreign_keys.union(  # pylint: disable=protected-access
        foreign_keys
    )

    if model._validate_foreign_keys:  # pylint: disable=protected-access
        try:
            schema = model.model_json_schema()
            _validate_foreign_keys(
                schema,
                model._foreign_keys,  # pylint: disable=protected-access
            )
        except UnimplementedAbstractField:
            # Don't continue for schemas containing NotImplemented fields
            pass

    model.model_rebuild(force=True)

    # Assert that the `schema_extra_metadata` field is not an IDS field because
    # `schema_extra_metadata` is a reserved name.
    if "schema_extra_metadata" in model.model_fields:
        raise InvalidField(
            "`schema_extra_metadata` is reserved for JSON Schema metadata and thus "
            "cannot be an IDS field name."
        )
    if "json_schema_extra" not in model.model_config:
        model.model_config["json_schema_extra"] = {}
    if not isinstance(model.model_config["json_schema_extra"], dict):
        raise InvalidSchemaMetadata(
            "In `model_config` for IDS models, only dictionaries of metadata "
            "are supported. Define `json_schema_extra` in the model's `model_config` "
            "as a dictionary."
        )
    # User defined `json_schema_extra` is entirely defined by `schema_extra_metadata`, the model
    # config cannot be used directly
    model.model_config["json_schema_extra"] = (
        model.schema_extra_metadata
    )  #  type: ignore
