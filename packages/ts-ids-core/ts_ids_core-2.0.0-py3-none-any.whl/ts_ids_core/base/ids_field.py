from __future__ import annotations

from typing import Any, Optional

from pydantic.fields import Field as PydanticField

from ts_ids_core.annotations import ForeignKey
from ts_ids_core.base.ids_undefined_type import IDS_UNDEFINED

JSON_SCHEMA_EXTRA = "json_schema_extra"


# PascalCase used in function name in order to imitate ``pydantic.Field``, which is
# wrapped by ``IdsField``.
# pylint: disable=invalid-name
def IdsField(
    default: Any = IDS_UNDEFINED, primary_key: Optional[str] = None, **kwargs: Any
) -> Any:
    """
    Wrap the :func:`pydantic.Field` function such that, fields default to a sentinel value for
    undefined (a.k.a. unknown or missing) values. As such, the field definition is
    compatible with schema defined using :class:`ts_ids_core.base.ids_element.IdsElement`.

    :param default:
        The default value to use for the field. Default set to a global instance of
        :class:`ts_ids_core.base.ids_undefined_type.IdsUndefinedType` that's intended
        to be used as a singleton.
    :param primary_key:
        A JSON pointer to the primary key which this foreign key links to. For example,
        `IdsField(primary_key="/properties/samples/items/properties/pk")` would be used
        to define a foreign key which points to `samples[*].pk`. This pointer is
        validated when the `IdsElement.schema` method is called, validation fails if the
        target primary key field is not in the schema.
    :param kwargs:
        All other keyword arguments are passed to :func:`pydantic.Field`.
    :return:
        The resulting :class:`pydantic.fields.FieldInfo` produced by
        :func:`pydantic.Field`.
    """
    if "default_factory" in kwargs and default is not IDS_UNDEFINED:
        raise ValueError("Cannot specify both `default` and `default_factory`.")

    schema_extra = kwargs.get(JSON_SCHEMA_EXTRA)
    if isinstance(schema_extra, dict) and ForeignKey.pk_reference_field in schema_extra:
        raise ValueError(
            f"The '{JSON_SCHEMA_EXTRA}' field {ForeignKey.pk_reference_field} should not be set when defining"
            f" IdsField. Instead define the primary_key reference with"
            f" 'IdsField(primary_key=<primary key reference>'."
        )

    if primary_key is not None:
        if not isinstance(schema_extra, dict):
            if schema_extra is None:
                kwargs[JSON_SCHEMA_EXTRA] = {}
            else:
                raise ValueError(
                    f"The `json_schema_extra` argument for IdsField must be None or of type {type(dict)} when"
                    f" passing a value for `primary_key`."
                )

        kwargs[JSON_SCHEMA_EXTRA].update({ForeignKey.pk_reference_field: primary_key})

    if "default_factory" in kwargs:
        # If the default value is set via default_factory, use `pydantic` behavior.
        return PydanticField(**kwargs)
    return PydanticField(default=default, **kwargs)
