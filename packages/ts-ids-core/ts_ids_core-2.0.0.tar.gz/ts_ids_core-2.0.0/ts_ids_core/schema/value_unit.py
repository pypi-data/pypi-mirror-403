from __future__ import annotations

from ts_ids_core.annotations import Nullable, Required
from ts_ids_core.base.ids_element import IdsElement
from ts_ids_core.base.ids_field import IdsField


class ValueUnit(IdsElement):
    """A quantity, represented by a value with a unit."""

    value: Required[Nullable[float]] = IdsField(description="A numerical value.")
    unit: Required[Nullable[str]] = IdsField(
        description="Unit for the numerical value."
    )


class RawValueUnit(ValueUnit):
    """A value with a unit, including the raw representation of the value from the primary data."""

    raw_value: Required[Nullable[str]] = IdsField(
        description="The raw, untransformed value from the primary data."
    )
