from __future__ import annotations

from ts_ids_core.annotations import Nullable
from ts_ids_core.base.ids_element import IdsElement
from ts_ids_core.base.ids_field import IdsField


class Assay(IdsElement):
    """
    An Assay is an analytical measurement procedure that produces a detectable signal, allowing a process to be qualified and quantified.
    """

    id: Nullable[str] = IdsField(description="Unique identifier assigned to an assay.")
    name: Nullable[str] = IdsField(
        description="A human-readable name given to the assay."
    )
    description: Nullable[str] = IdsField(
        description="A human-readable description given to the assay"
    )


# This may optionally be used as a top-level field in an IDS
class Experiment(IdsElement):
    """
    An Experiment is a scientific procedure to investigate a specific hypothesis or a research question. The primary and derived scientific data is used to test the hypothesis, or to provide insight into a particular process. An Experimental entry typically contains additional context, such as purpose, materials, method, and conclusions.
    """

    id: Nullable[str] = IdsField(
        description=(
            "Unique identifier assigned to a specific experiment conducted within a "
            "project. Most often generated within an electronic laboratory notebook "
            "(ELN)."
        )
    )
    name: Nullable[str] = IdsField(
        description="A human-readable name given to the experiment."
    )
    description: Nullable[str] = IdsField(
        description="A human-readable description given to the experiment."
    )


class Project(IdsElement):
    """
    A Project is a scientific or business program or initiative. A Project ID can be used to associate with the entire set of primary and derived scientific data from every experiment performed to advance a particular initiative, such as the development of an assay or a drug product.
    """

    id: Nullable[str] = IdsField(description="Unique identifier assigned to a project.")
    name: Nullable[str] = IdsField(
        description="A human-readable name given to the project."
    )
    description: Nullable[str] = IdsField(
        description="A human-readable description given to the project."
    )


class ProjectAttributes(IdsElement):
    """
    A set of fields which uniquely identify and describe a particular initiative and methodologies used to produce the data in a given IDS. These attributes are commonly found in ELN and LIMS applications and allow users to organize data to associate related datasets.
    """

    project: Project = IdsField(description="Project metadata.")
    experiment: Experiment = IdsField(description="Experiment metadata.")
    assay: Assay = IdsField(description="Assay metadata.")
