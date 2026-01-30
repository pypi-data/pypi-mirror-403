# SPDX-FileCopyrightText: 2025 Helio Chissini de Castro <heliocastro@gmail.com>
# SPDX-License-Identifier: MIT


from pydantic import BaseModel, ConfigDict, Field

from ort.models.dependency_graph import DependencyGraph
from ort.models.identifier import Identifier
from ort.models.issue import Issue
from ort.models.package import Package
from ort.models.project import Project


class AnalyzerResult(BaseModel):
    """
    A class that merges all information from individual [ProjectAnalyzerResult]s created for each found definition file.
    """

    model_config = ConfigDict(
        extra="forbid",
    )

    projects: set[Project] = Field(
        description="Sorted set of the projects, as they appear in the individual analyzer results.",
    )

    packages: set[Package] = Field(
        description="The set of identified packages for all projects.",
    )

    issues: dict[Identifier, list[Issue]] = Field(
        default_factory=dict,
        description="The lists of Issue objects that occurred within the analyzed projects themselves. Issues related"
        "to project dependencies are contained in the dependencies of the project's scopes. This property is not"
        "serialized if the map is empty to reduce the size of the result file.",
    )

    dependency_graphs: dict[str, DependencyGraph] = Field(
        default_factory=dict,
        description="A map with DependencyGraph objects keyed by the name of the package manager that created this"
        "graph. Package managers supporting this feature can construct a shared DependencyGraph over all projects and"
        "store it in this map.",
    )
