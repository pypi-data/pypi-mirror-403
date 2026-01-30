from __future__ import annotations

from typing import Any, List, Type

from pydantic import model_validator
from pydantic.fields import FieldInfo
from typing_extensions import Annotated, TypedDict, get_args

from ts_ids_core.annotations import (
    Nullable,
    Required,
    fixed_length,
    resolve_length_annotation_metadata,
)
from ts_ids_core.base.ids_element import IdsElement
from ts_ids_core.base.ids_field import IdsField
from ts_ids_core.schema.dimension import Dimension, DimensionMetadata
from ts_ids_core.schema.measure import Measure, MeasureMetadata

__all__ = ["DataCube", "DataCubeMetadata"]


class DataCubeDict(TypedDict):
    """Type hint for the dictionary form of `DataCube`."""

    name: Nullable[str]
    measures: List[Measure]
    dimensions: List[Dimension]


def datacube_model_init(
    model: "Type[DataCube]",
    **kwargs: Any,
) -> None:
    """
    Initialize DataCube classes, enabling compile-time validation of IDS conventions.

    The following IDS conventions are included:

        1. the `measures` and `dimensions` fields are constrained lists
        2. ...whose ``min_length`` == ``max_length``.
        3. The number of dimensions implied by the ``type`` of the ``measures`` field is
        consistent with that implied by ``dimensions``' field's ``type``.
    """
    name = model.__name__
    fields = model.model_fields
    missing_required_fields = {"measures", "dimensions"}.difference(fields)
    if len(missing_required_fields) > 0:
        raise ValueError(
            f"DataCube class missing the following required fields: "
            f"{', '.join(missing_required_fields)}."
        )
    # fmt: off
    validate_conlist_min_max_length_equal(fields["measures"], "measures", class_name=name)
    num_dimensions = validate_conlist_min_max_length_equal(fields["dimensions"], "dimensions", class_name=name)
    # fmt: on
    validate_consistent_measures_dimensions(num_dimensions, fields["measures"])


def validate_conlist_min_max_length_equal(
    field: FieldInfo, field_name: str, *, class_name: str = "DataCube"
) -> int:
    """
    Validate that a field is a constrained list and its ``min_length`` equals
    its ``max_length``, and return the validated number of items.
    """
    # Get min_length and max_length from one of the possible Annotated metadata types
    constraint = resolve_length_annotation_metadata(field.metadata)

    # Both min and max lengths have to be defined
    if (
        constraint is None
        or constraint.min_length is None
        or constraint.max_length is None
    ):
        raise TypeError(
            f"{class_name}.{field_name} field is not a constrained list as expected. "
            "To annotate the type as having a fixed length, use "
            "`Annotated[..., fixed_length(...)]`, or for other length constraints "
            "refer to Pydantic documentation."
        )

    min_length = constraint.min_length
    max_length = constraint.max_length

    # Min and max lengths have to be equal
    if min_length != max_length:
        raise ValueError(
            f"{class_name}.{field_name} field has min_length={min_length} and "
            f"max_length={max_length}, but expected min_length and max_length "
            f"to be equal."
        )

    # The constrained length can't be 0
    if min_length == 0:
        raise ValueError(
            f"{class_name}.{field_name} field got invalid values for min_length and "
            f"max_length. Expected nonzero values."
        )

    # Return the validated length
    return min_length


def validate_consistent_measures_dimensions(
    num_dimensions: int, measures: FieldInfo
) -> None:
    """
    Validate that the number of dimensions implied by the type hint of
    ``measures[*].value`` is consistent with that implied by ``dimensions``'
    length.
    """
    # TODO we have no validation that `measures` has the expected type.
    # i.e. it must be of type `List[X]` where X is a subclass of Measure.
    measure_cls: Type[Measure] = get_args(measures.annotation)[0]
    measures_actual_dimensions_count = measure_cls.num_dimensions

    if measures_actual_dimensions_count != num_dimensions:
        raise ValueError(
            f"The length of `dimensions[*].scale` implies that `measures[*].value` "
            f"will be {num_dimensions}-dimensional, but `measures[*].value` "
            f"is actually {measures_actual_dimensions_count}-dimensional. To fix, "
            f"update either the `fixed_length` of the `DataCube.dimensions` "
            f"field or update the type hint of the `measures[*].value` field."
        )


# One instance of this class is an item in the `datacubes` array.
class DataCube(IdsElement):
    """TetraScience designed model for multi-dimensional data."""

    name: Required[Nullable[str]]
    # Override `fixed_length` with the required number of measures
    measures: Required[Annotated[List[Measure], fixed_length(1)]]
    # Override `fixed_length` with the required number of dimensions
    dimensions: Required[Annotated[List[Dimension], fixed_length(2)]]

    @classmethod
    def __pydantic_init_subclass__(cls, **kwargs: Any) -> None:
        """IDS-specific datacubes class initialization."""
        super().__pydantic_init_subclass__()
        datacube_model_init(cls, **kwargs)

    # `skip_on_failure=True` means this validator will be run after field validation.
    # Thus, the `values` arg (dict) is guaranteed to contain all field names and values.
    @model_validator(mode="after")
    def consistent_number_of_dimensions(self: DataCube) -> DataCube:
        """
        Assert that the dimensionality of all `DataCube.measures[*].value` is consistent
        with `DataCube.dimensions[*].scale`.

        For example, consider the following ``DataCube`` class that describes
        one-dimensional data:

        .. code::

            from typing import List

            from pydantic import conlist

            from ts_ids_core.annotations import Required
            from ts_ids_core.schema import DataCube, Dimension, Measure

            class ExampleMeasure(Measure):
                # note that `value` is one-dimensional to be consistent with the
                # `fixed_length` in the definition of `ExampleDataCube.dimensions`.
                value: List[float]

            class ExampleDataCube(DataCube):
                measures: Required[Annotated[List[Measure], fixed_length(1)]]
                dimensions: Required[Annotated[List[Dimension], fixed_length(1)]]

        The following would be a valid ``ExampleDataCube`` instance:

        .. code::

            example = DataCube(
                dimensions=[
                    Dimension(
                        name="time",
                        unit="second",
                        scale=[0, 1, 2, 3, 4, 5],
                    ),
                ],
                measures=[
                    ExampleMeasure(
                        name="electrical_current",
                        unit="MilliAmp",
                        value=[0, 10, 20, 30, 40, 50],
                    ),
                ]
            )

        It's valid because ``len(example.measures[0].value) == len(example.dimensions[0].scale)``.
        """

        # Only validate non-empty measures[*].value
        measures = [measure for measure in self.measures if measure.size > 0]

        expected_shape = tuple((len(dimension.scale) for dimension in self.dimensions))
        # Don't fail array shape validation if all `measures` are empty arrays.
        if len(measures) == 0 and set(expected_shape) == {0}:
            return self

        shape_of_measures = {measure.shape for measure in measures}
        if len(shape_of_measures) > 1:
            raise ValueError(
                f"All items in the measures[*].value lists are expected to have the same shape. "
                f"Got shapes '{', '.join(map(str, shape_of_measures))}'."
            )

        if shape_of_measures != {
            expected_shape,
        }:
            raise ValueError(
                f"Items in the measures[*].value lists are expected to have shape '{expected_shape}'. "
                f"Got {shape_of_measures}"
            )

        return self


class DataCubeMetadata(IdsElement):
    """
    DataCube metadata, with a file ID referencing a file in the data lake which contains
    DataCube dimension and measure values.
    """

    index: Required[int] = IdsField(
        description=(
            "Index which relates dimension and measure values in the external data "
            "file with the metadata stored in this model."
        )
    )
    name: Required[Nullable[str]]

    # Override `fixed_length` with the required number of measures
    measures: Required[Annotated[List[MeasureMetadata], fixed_length(1)]]
    # Override `fixed_length` with the required number of dimensions
    dimensions: Required[Annotated[List[DimensionMetadata], fixed_length(2)]]

    file_id: Required[str] = IdsField(
        description="The `fileId` of the file in the data lake containing DataCube data"
    )
