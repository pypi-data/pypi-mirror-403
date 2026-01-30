from __future__ import annotations

from ts_ids_core.annotations import Nullable
from ts_ids_core.base.ids_element import IdsElement
from ts_ids_core.base.ids_field import IdsField


# One instance of this class is an item in the `users` array.
class User(IdsElement):
    """Metadata of the user executing a run."""

    id_: Nullable[str] = IdsField(
        alias="id", description="Unique identifier assigned to a user."
    )
    name: Nullable[str] = IdsField(
        description="User name.",
    )
    type_: Nullable[str] = IdsField(
        alias="type",
        description="User type like 'admin', 'manager', 'power user', 'standard user'. "
        "This information is usually from the instrument software",
    )
