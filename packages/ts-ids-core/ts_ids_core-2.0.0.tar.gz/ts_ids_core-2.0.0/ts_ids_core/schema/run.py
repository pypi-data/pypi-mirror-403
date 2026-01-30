from __future__ import annotations

from typing import List

from ts_ids_core.annotations import Nullable
from ts_ids_core.base.ids_element import IdsElement
from ts_ids_core.base.ids_field import IdsField


class RunStatus(IdsElement):
    """Status for a run."""

    # If there is an unnamed general instrument status, use the name "general"
    name: str = IdsField(description="Name of the status.")
    value: str = IdsField(
        description="Text-based status like 'completed', 'failed', 'aborted', 'error'."
    )


# One instance of this class is an item in the `runs` array.
class Run(IdsElement):
    """
    A Run refers to a discrete period of time in which a performed process generates one or more data points for either a single or several related samples or generates a physical product. A Run typically refers to a particular execution of an instrument.
    """

    id_: Nullable[str] = IdsField(
        description="Unique identifier assigned to a specific run (execution) of an experiment.",
        alias="id",
    )
    name: Nullable[str] = IdsField(
        description="Name assigned to a specific run (execution) of an experiment.",
    )
    logs: List[str] = IdsField(
        description="Log messages recorded during a specific run (execution) of an experiment.",
    )
