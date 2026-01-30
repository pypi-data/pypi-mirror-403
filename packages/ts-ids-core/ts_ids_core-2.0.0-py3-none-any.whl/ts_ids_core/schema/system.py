from __future__ import annotations

from typing import List

from ts_ids_core.annotations import Nullable, Required
from ts_ids_core.base.ids_element import IdsElement
from ts_ids_core.base.ids_field import IdsField
from ts_ids_core.schema import system


class Firmware(IdsElement):
    """System firmware metadata."""

    name: Required[Nullable[str]] = IdsField(
        description="Firmware name.",
    )
    version: Required[Nullable[str]] = IdsField(
        description="Firmware version.",
    )


class Software(IdsElement):
    """
    Software application that most recently handled the data (file) or the application
    the data (file) is intended for. For example, applications can include Electronic
    Lab Notebooks (ELN), Instrument Control Software (ICS), Chromatography Data Systems
    (CDS), or instrument-specific analysis software.
    """

    name: Required[Nullable[str]] = IdsField(
        description="Software name.",
    )
    version: Required[Nullable[str]] = IdsField(
        description="Software version.",
    )


# One instance of this class is an item in the `systems` array.
#
# There are globally shared `systems` fields which are not mandatory to use in all
# `System` IDS models. These are defined within nested classes inside `System`.
# To create a custom System model which uses one of these `systems` fields, inherit
# from the `System` class and each of the desired nested classes.
#
# For example, the model below has all the fields from System, Id, and Software:
# `vendor`, `model`, `type_`, `id_` and `software`.
#
# ```python
# class MySystem(System, System.Id, System.Software):
#     pass
# ```
#
# This approach of using multiple inheritance reduces the opportunities
# for making mistakes compared with manually defining an "id" field in
# a custom System object, where the field name or type are open to
# mistakes.
class System(IdsElement):
    """
    Metadata regarding the equipment, software, and firmware used in a run of an
    instrument or experiment.
    """

    # This globally shared `systems` field is not mandatory to use in all `System` IDS
    # models, see the comment above the `System` class for a general usage example
    class Id(IdsElement):
        """System ID."""

        id_: Nullable[str] = IdsField(
            alias="id",
            description=(
                "Identifier for the system. This is usually defined by the system "
                "owner or user, for example this may be created with a laboratory "
                "information management system or asset management software. "
                "Typically, an ID will not change over time, so that it can be used "
                "to track a particular system, unlike the system name which may change."
            ),
        )

    # This globally shared `systems` field is not mandatory to use in all `System` IDS
    # models, see the comment above the `System` class for a general usage example
    class Name(IdsElement):
        """System name."""

        name: Nullable[str] = IdsField(
            description=(
                "Name for the system. This is usually a human-readable name defined "
                "by the system owner or user. It may be changed over time as "
                "the system is used for different purposes, unlike the ID which "
                "typically doesn't change."
            )
        )

    # This globally shared `systems` field is not mandatory to use in all `System` IDS
    # models, see the comment above the `System` class for a general usage example
    class SerialNumber(IdsElement):
        """System serial number."""

        serial_number: Nullable[str] = IdsField(
            description=(
                "System serial number. "
                # This definition is from Recommended Labels (in TetraConnect Hub):
                "Indicates a unique instrument identifier within the same model line "
                "from a specific vendor. "
                # This is additional clarification:
                "This is provided by the system vendor, unlike an ID or name which "
                "are usually created by the system owner or user."
            )
        )

    # This globally shared `systems` field is not mandatory to use in all `System` IDS
    # models, see the comment above the `System` class for a general usage example
    class Firmware(IdsElement):
        """System firmware."""

        # This annotation must refer to `system.Firmware` explicitly, not `Firmware`,
        # which resolves to `System.Firmware` (this class), which leads to a recursive
        # definition because of `from __future__ import annotations`
        firmware: List[system.Firmware] = IdsField(
            description="System firmware metadata."
        )

    # This globally shared `systems` field is not mandatory to use in all `System` IDS
    # models, see the comment above the `System` class for a general usage example
    class Software(IdsElement):
        """System software."""

        # This annotation must refer to `system.Software` explicitly, not `Software`,
        # which resolves to `System.Software` (this class), which leads to a recursive
        # definition because of `from __future__ import annotations`
        software: List[system.Software] = IdsField(
            description=(
                "Software applications that most recently handled the data (file) or "
                "the applications the data (file) is intended for. "
                "For example, applications can include Electronic Lab Notebooks (ELN), "
                "Instrument Control Software (ICS), Chromatography Data Systems (CDS), "
                "or instrument-specific analysis software."
            )
        )

    # Vendor value must come from Tetra Lab entry
    vendor: Required[Nullable[str]] = IdsField(
        description="The instrument vendor or manufacturer, like 'PerkinElmer' or 'Agilent'."
    )
    model: Required[Nullable[str]] = IdsField(
        description="A specific model instrument type from a vendor."
    )
    # Type value must come from a Tetra Lab entry
    type_: Required[Nullable[str]] = IdsField(
        alias="type",
        description="Indicates the type of instrument that's generating data.",
    )
