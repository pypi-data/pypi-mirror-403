from __future__ import annotations

from math import prod
from typing import Any, ClassVar, Collection, List, Set, Tuple, Type, Union

from pydantic import field_validator
from pydantic.fields import FieldInfo
from typing_extensions import get_args, get_origin

from ts_ids_core.annotations import Abstract, Nullable, Required
from ts_ids_core.base.ids_element import IdsElement
from ts_ids_core.base.ids_undefined_type import IdsUndefinedType
from ts_ids_core.errors import InvalidArrayShape

__all__ = ["Measure", "MeasureMetadata", "NDArray"]


class MeasureMetadata(IdsElement):
    """Metadata for a measure of a DataCube"""

    name: Required[Nullable[str]]
    unit: Required[Nullable[str]]


def count_dimensions(field: FieldInfo) -> int:
    """
    Return the number of dimensions implied by a type hint.

    For example,

    .. code::

        from typing import List, Tuple

        from ts_ids_core.annotations import Nullable
        from ts_ids_core.base.ids_element import IdsElement
        from ts_ids_core.schema.measure import count_dimensions

        class Example(IdsElement):
            foo: List[List[int]]
            bar: Tuple[Nullable[float]]

        assert count_dimensions(Example.model_fields["foo"]) == 2
        assert count_dimensions(Example.model_fields["bar"]) == 1

    :param field:
        The field whose dimensions to count.
    :return:
        The number of dimensions in the field's type hint.
    """

    def _count_dimensions(type_hint: Type[Any]) -> int:
        origin = get_origin(type_hint)
        # Base case: we got to the last level of nesting, e.g.
        # ``type_hint`` is ``Union[None, float]``.
        if origin is Union:
            args: Set[Union[Type[Any], None]] = set(get_args(type_hint))
            if IdsUndefinedType in args:
                args.remove(IdsUndefinedType)
            if type(None) in args:
                args.remove(type(None))
                if any(
                    get_origin(type_) is not None
                    and issubclass(get_origin(type_), Collection)
                    for type_ in args
                ):
                    raise ValueError("Cannot have nullable container types.")
            assert len(args) != 1 or args != {
                int,
                float,
            }, "Fields cannot have multiple types."
            return _count_dimensions(args.pop())
        # Base case: we got to the last level of nesting, e.g.
        # ``type_hint`` is ``float``.
        if origin is None or not issubclass(origin, Collection):
            return 0
        child_args = get_args(type_hint)
        # Container element's type is unknown.
        if not child_args:
            return 1
        return _count_dimensions(child_args[0]) + 1

    return _count_dimensions(field.annotation) if field.annotation is not None else 0


NDArray = Union[List[Union[float, None]], List["NDArray"]]


def multidimensional_shape(value: NDArray) -> Tuple[int, ...]:
    """
    Return the shape of a multidimensional array, raising an error if it is ragged.

    For example, ``[[[0], [1]]]`` has a shape of ``(1, 2, 1)``: it is 3 layers of nested
    lists (3 elements in the output tuple), and each element of the tuple is the number
    of elements at that nesting level.

    A ragged list like ``[[1], [2, 2]]`` will raise a ``InvalidArrayShape`` error. This
    list contains lists of lengths 1 and 2 at the same level, meaning it is not a
    multi-dimensional array.
    """
    if len(value) == 0:
        return (0,)

    child_is_primitive = tuple(
        (not isinstance(sub_value, (list, tuple))) for sub_value in value
    )
    if any(child_is_primitive):
        if not all(child_is_primitive):
            # `value` is a mix of `List[primitive]` AND `List[List[...]]` which is invalid
            raise InvalidArrayShape()

        # Base case: this is a sequence of primitives, no further recursion needed
        return (len(value),)

    # `value` is now of type `List[List[...]]`
    sub_shapes = set(multidimensional_shape(x) for x in value)  # type: ignore

    if len(sub_shapes) > 1:
        # The sub-shapes at this level are not all identical, i.e. it is a ragged list
        # somewhere in the nested shape
        raise InvalidArrayShape()

    return (len(value), *sub_shapes.pop())


class MeasureBase(MeasureMetadata):
    """
    Base class for all DataCube Measure models.

    ``Measure`` classes must contain a field named ``value``. The
    ``num_dimensions`` attribute is set based on the dimensionality implied
    by the ``value`` field.
    For example, the dimensionality of ``List[List[str]]`` is 2.
    """

    num_dimensions: ClassVar[int]
    # Override this list nesting level to match the number of dimensions
    value: Abstract[Required[List[Nullable[float]]]]

    @classmethod
    def __pydantic_init_subclass__(cls, **kwargs: Any) -> None:
        """IDS-specific measure class initialization."""
        super().__pydantic_init_subclass__()
        fields = cls.model_fields
        if "value" not in fields:
            raise ValueError("Measure class missing 'value' field.")
        num_dimensions = count_dimensions(fields["value"])
        cls.num_dimensions = num_dimensions

    @property
    def shape(self) -> Tuple[int, ...]:
        """Return shape of the (possibly multidimensional) Measure.value"""
        return multidimensional_shape(self.value)

    @property
    def size(self) -> int:
        """Return the number of elements in ``self.value``."""
        return prod(self.shape)

    @field_validator("value")
    @classmethod
    def validate_value_shape(cls, value: NDArray) -> NDArray:
        """Validate that all lists along any one dimension have the same length."""
        try:
            multidimensional_shape(value)
        except InvalidArrayShape as error:
            raise ValueError(
                "Measure values could not be converted to a valid multidimensional array. "
                "Nested sequences may have inconsistent length or shape, resulting in "
                "a ragged array."
            ) from error

        return value


class Measure(MeasureBase):
    """
    A measure of a DataCube
    """

    # Inherits `name` and `unit` from MeasureMetadata, and adds `value`.

    # Override this list nesting level to match the number of dimensions
    value: Required[List[List[Nullable[float]]]]
