from __future__ import annotations

from typing import List

from ts_ids_core.annotations import Nullable, Required
from ts_ids_core.base.ids_element import IdsElement


class DimensionMetadata(IdsElement):
    """Metadata for a dimension of a DataCube"""

    name: Required[Nullable[str]]
    unit: Required[Nullable[str]]


class Dimension(DimensionMetadata):
    """A dimension of a DataCube"""

    scale: Required[List[Nullable[float]]]
