# SPDX-FileCopyrightText: 2025 Helio Chissini de Castro <heliocastro@gmail.com>
# SPDX-License-Identifier: MIT


from pydantic import BaseModel, ConfigDict, Field

from ort.models.issue import Issue
from ort.models.package_linkage import PackageLinkage


class DependencyGraphNode(BaseModel):
    """
    A data class representing a node in the dependency graph.

    A node corresponds to a package, which is referenced by a numeric index. A package may, however, occur multiple
    times in the dependency graph with different transitive dependencies. In this case, different fragment indices are
    used to distinguish between these occurrences.
    """

    model_config = ConfigDict(
        extra="forbid",
    )

    pkg: int | None = Field(
        default=None,
        description="Stores the numeric index of the package dependency referenced by this object. The package behind "
        "this index can be resolved by evaluating the list of identifiers stored in DependencyGraph at "
        "this index.",
    )
    fragment: int = Field(
        0,
        description="Stores the index of the fragment in the dependency graph where the referenced dependency is "
        "contained. This is needed to uniquely identify the target if the dependency occurs multiple times "
        "in the graph.",
    )
    linkage: PackageLinkage = Field(
        default=PackageLinkage.DYNAMIC,
        description="The type of linkage used for the referred package from its dependent package. As most of ORT's "
        "supported package managers / languages only support dynamic linking or at least default to it, "
        "also use that as the default value here to not blow up ORT result files.",
    )
    issues: list[Issue] = Field(
        default_factory=list, description="A list of Issue objects that occurred handling this dependency."
    )
