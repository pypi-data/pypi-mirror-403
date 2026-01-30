"""
Exceptions used throughout `ts_ids_core`.
"""


class MultipleTypesError(TypeError):
    """Field which should have one type has multiple types."""


class InvalidTypeError(TypeError):
    """Field has an invalid type."""


class NullableReferenceError(ValueError):
    """fields that contain a reference cannot be nullable."""


class WrongConstantError(ValueError):
    """Raised when the user passes a value to an abstract 'const' field."""


class InvalidSchemaMetadata(ValueError):
    """Raised when the IDS' JSON Schema contains an invalid top-level metadata value."""


class InvalidField(Exception):
    """
    Invalid definition for the IDS field.

    Note that this error should only be raised during class creation. Raise a
    ``ValueError`` for invalid field values, e.g. in the body of a
    ``@field_validator`` method.
    """


class InvalidNonMandatoryField(InvalidField):
    """The Non-Mandatory Field of an IDS class is invalid."""


class UnimplementedAbstractField(InvalidField):
    """An abstract field is being used when instead a subclass should implement it in order to use it."""


class SchemaValidationError(ValueError):
    """Raised when a value is not consistent with the schema."""


class InvalidPrimaryKeyField(InvalidField):
    """Invalid primary key field definition."""


class InvalidForeignKeyField(InvalidField):
    """Invalid foreign key field definition."""


class InvalidForeignKeySchema(ValueError):
    """Invalid foreign key schema when creating JSON schema."""


class InvalidArrayShape(ValueError):
    """A multidimensional array has an invalid shape."""

    def __init__(self):
        self.message = (
            "An array with a non-uniform shape was found where a multidimensional "
            "array was expected. It must have the same length in every element of "
            "every dimension to be a valid multidimensional array."
        )
        super().__init__(self.message)
