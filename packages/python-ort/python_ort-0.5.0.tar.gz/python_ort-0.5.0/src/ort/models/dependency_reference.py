# SPDX-FileCopyrightText: 2025 Helio Chissini de Castro <heliocastro@gmail.com>
# SPDX-License-Identifier: MIT


from pydantic import BaseModel, ConfigDict, Field

from ort.models.issue import Issue
from ort.models.package_linkage import PackageLinkage


class DependencyReference(BaseModel):
    """
    A class to model a tree-like structure to represent the dependencies of a project.

    Instances of this class are used to store the relations between dependencies in fragments of dependency trees in an
    Analyzer result. The main purpose of this class is to define an efficient serialization format, which avoids
    redundancy as far as possible. Therefore, dependencies are represented by numeric indices into an external table.
    As a dependency can occur multiple times in the dependency graph with different transitive dependencies, the class
    defines another index to distinguish these cases.

    Note: This is by intention no data class. Equality is tested via references and not via the values contained.
    """

    model_config = ConfigDict(
        extra="forbid",
    )

    pkg: int = Field(
        ...,
        description="Stores the numeric index of the package dependency referenced by this object. The package behind "
        "this index can be resolved by evaluating the list of identifiers stored in DependencyGraph at "
        "this index.",
    )
    fragment: int = Field(
        default=0,
        description="Stores the index of the fragment in the dependency graph where the referenced dependency is "
        "contained. This is needed to uniquely identify the target if the dependency occurs multiple times "
        "in the graph.",
    )
    dependencies: set["DependencyReference"] = Field(
        default_factory=set,
        description="A set with the references to the dependencies of this dependency. That way a tree-like structure "
        "is established.",
    )
    linkage: PackageLinkage = Field(
        default=PackageLinkage.DYNAMIC,
        description="The type of linkage used for the referred package from its dependent package. As most of ORT's "
        "supported package managers / languages only support dynamic linking or at least default to it, "
        "also use that as the default value here to not blow up ORT result files.",
    )
    issues: list[Issue] = Field(..., description="A list of Issue objects that occurred handling this dependency.")
