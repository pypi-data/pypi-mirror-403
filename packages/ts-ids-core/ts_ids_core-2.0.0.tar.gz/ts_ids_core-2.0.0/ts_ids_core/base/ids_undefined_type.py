from __future__ import annotations

from pydantic_core import PydanticUndefined as _PydanticUndefinedInstance


class IdsUndefinedType:
    """
    Placeholder indicating that the the value of the :class:`ts_ids_core.base.ids_element.IdsElement`
    field is unknown or non-existent.

    This is distinct from the :class:`ts_ids_core.base.ids_element.IdsElement`'s field
    being ``None``.

    This was partially copied from :class:`pydantic.fields.UndefinedType`. It intentionally
    does not inherit from :class:`pydantic.fields.UndefinedType` so that it fails
    :func:`isinstance` and :func:`issubclass` checks.
    """

    #: An instance's 'type' in JSON Schema.
    JSON_SCHEMA_TYPE = "Undefined"

    def __repr__(self) -> str:
        return "IdsUndefined"

    def __reduce__(self) -> str:
        """Enable pickling this instance."""
        return self.JSON_SCHEMA_TYPE


#: Sentinel indicating that a field's value is unknown or irrelevant. This is distinct
#: from a field being NULL (`None`).
IDS_UNDEFINED = IdsUndefinedType()
#: By default, `pydantic` passes `default=PYDANTIC_UNDEFINED` to the `Field` function
#: and the `FieldInfo` constructor.
PYDANTIC_UNDEFINED = _PydanticUndefinedInstance
