from __future__ import annotations

from ts_ids_core.annotations import Nullable
from ts_ids_core.base.ids_element import IdsElement
from ts_ids_core.base.ids_field import IdsField
from ts_ids_core.schema.sample import ValueDataType


class Parameter(IdsElement):
    """A structure for capturing individual values with varying datatypes."""

    key: str = IdsField(description="This is the property name.")
    value: str = IdsField(
        description="The original string value of the parameter from the raw file."
    )
    value_data_type: ValueDataType = IdsField(
        description="This is the true type of the original value."
    )
    string_value: Nullable[str] = IdsField(
        description=(
            "If string_value has a value, then numerical_value, numerical_value_unit "
            "and boolean_value have to be null."
        )
    )
    numerical_value: Nullable[float] = IdsField(
        description=(
            "If numerical_value has a value, then string_value and boolean_value "
            "have to be null."
        )
    )
    numerical_value_unit: Nullable[str] = IdsField(
        description="Unit for the numerical value."
    )
    boolean_value: Nullable[bool] = IdsField(
        description=(
            "If boolean_value has a value, then numerical_value, "
            "numerical_value_unit and string_value have to be null."
        )
    )
