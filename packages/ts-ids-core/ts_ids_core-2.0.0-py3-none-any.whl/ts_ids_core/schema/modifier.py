from __future__ import annotations

import enum

from ts_ids_core.base.ids_element import IdsElement
from ts_ids_core.base.ids_field import IdsField


# For Modifier Pattern
class ModifierType(enum.Enum):
    """An enumeration of observed modifiers in the primary data."""

    LESS_THAN = "<"
    GREATER_THAN = ">"
    LESS_THAN_OR_EQUAL = "<="
    GREATER_THAN_OR_EQUAL = ">="
    NULL = None


class Modifier(IdsElement):
    """A model to capture the numeric value and prefix (modifier) for a prefixed numeric string (e.g. '>1.0')."""

    value: float = IdsField(description="Modifier value.")
    modifier: ModifierType = IdsField(description="Modifier type.")
