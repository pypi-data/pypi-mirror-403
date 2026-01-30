from __future__ import annotations

import enum
from typing import List

from ts_ids_core.annotations import Nullable, Required
from ts_ids_core.base.ids_element import IdsElement
from ts_ids_core.base.ids_field import IdsField
from ts_ids_core.schema.time_ import SampleTime


class Compound(IdsElement):
    """
    A Compound is a specific chemical or biochemical structure or substance that is being investigated. A Compound may be any drug substance, drug product intermediate, or drug product across small molecules, and cell and gene therapy (CGT).
    """

    id_: Nullable[str] = IdsField(
        alias="id",
        description="Unique identifier assigned to a compound.",
    )
    name: Nullable[str] = IdsField(
        description="Compound name.",
    )


class Batch(IdsElement):
    """
    A Batch is the result of a single manufacturing run for a drug product that is made as specified groups or amounts,  within a specific time frame from the same raw materials that is intended to have uniform character and quality, within specified limits.
    """

    id_: Nullable[str] = IdsField(
        alias="id",
        description="Unique identifier assigned to a batch.",
    )
    name: Nullable[str] = IdsField(
        description="Batch name",
    )
    barcode: Nullable[str] = IdsField(
        description="Barcode assigned to a batch",
    )


class Set(IdsElement):
    """A group of Samples."""

    id_: Nullable[str] = IdsField(
        alias="id",
        description="Unique identifier assigned to a set.",
    )
    name: Nullable[str] = IdsField(
        description="Set name.",
    )


class Holder(IdsElement):
    """
    A sample container such as a microplate or a vial.
    """

    name: Nullable[str] = IdsField(
        description="Holder name.",
    )
    type_: Nullable[str] = IdsField(
        alias="type",
        description="Holder type.",
    )
    barcode: Nullable[str] = IdsField(
        description="Barcode assigned to a holder.",
    )


class Location(IdsElement):
    """
    The Location of the sample within the holder, such as the location of a well in a microplate.
    """

    position: Nullable[str] = IdsField(description="Raw position string.")
    row: Nullable[float] = IdsField(
        description="Row index of sample location in a plate or holder."
    )
    column: Nullable[float] = IdsField(
        description="Column index of sample location in a plate or holder."
    )
    index: Nullable[float] = IdsField(
        description="Index of sample location flattened to a single dimension."
    )
    holder: Holder = IdsField(description="Sample holder information")


class ValueDataType(str, enum.Enum):
    """Allowed data type values."""

    STRING = "string"
    NUMBER = "number"
    BOOLEAN = "boolean"


class Source(IdsElement):
    """
    The Source of information, such as a data file or a sample database.
    """

    name: Required[Nullable[str]] = IdsField(
        description="Source name.",
    )
    type_: Required[Nullable[str]] = IdsField(
        alias="type",
        description="Source type.",
    )


class Property(IdsElement):
    """
    A property has a name and a value of any type, with metadata about the
    property including the source of the property and times associated with it
    such as when the property was created or looked up.
    """

    source: Required[Source] = IdsField(
        description="Sample property data source information."
    )
    name: Required[str] = IdsField(description="Sample Property name.")
    value: Required[str] = IdsField(
        description="The original string value of the property."
    )
    value_data_type: Required[ValueDataType] = IdsField(
        description="This is the type of the original value."
    )
    string_value: Required[Nullable[str]] = IdsField(
        description=(
            "If string_value has a value, then numerical_value, "
            "numerical_value_unit, and boolean_value all have to be null."
        )
    )
    numerical_value: Required[Nullable[float]] = IdsField(
        description=(
            "If numerical_value has a value, then string_value and "
            "boolean_value both have to be null."
        )
    )
    numerical_value_unit: Required[Nullable[str]] = IdsField(
        description="Unit for the numerical value."
    )
    boolean_value: Required[Nullable[bool]] = IdsField(
        description=(
            "If boolean_value has a value, then numerical_value, numerical_value_unit, "
            "and string_value all have to be null."
        )
    )
    time: Required[SampleTime] = IdsField(
        description="Time associated with the sample property."
    )


class Label(IdsElement):
    """
    A Label associated with a sample, along with metadata about the label including
    the source of the label and times associated with the label such as when it was
    created or looked up.
    """

    source: Required[Source] = IdsField(
        description="Sample label data source information."
    )
    name: Required[str] = IdsField(
        description="Sample label name.",
    )
    value: Required[str] = IdsField(description="Sample label value.")
    time: Required[SampleTime] = IdsField(
        description="Time associated with the sample label."
    )


# One instance of this class is an item in the `samples` array.
class Sample(IdsElement):
    """
    A Sample is a discrete entity being observed in an experiment. For example, Samples may be characterized for product quality and stability, or be measured for research purposes.
    """

    id_: Nullable[str] = IdsField(
        alias="id",
        description=("Unique identifier assigned to a sample."),
    )
    name: Nullable[str] = IdsField(
        description="Sample name.",
    )
    barcode: Nullable[str] = IdsField(
        description="Barcode assigned to a sample.",
    )
    batch: Batch
    set_: Set = IdsField(alias="set", description="Sample set.")
    location: Location = IdsField(description="Sample location information.")
    compound: Compound = IdsField(description="Sample compound information.")
    properties: List[Property] = IdsField(description="Sample properties.")
    labels: List[Label] = IdsField(description="Sample labels.")
