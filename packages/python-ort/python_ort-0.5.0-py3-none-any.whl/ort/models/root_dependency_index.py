# SPDX-FileCopyrightText: 2025 Helio Chissini de Castro <heliocastro@gmail.com>
# SPDX-License-Identifier: MIT


from pydantic import BaseModel, Field


class RootDependencyIndex(BaseModel):
    """
    A data class representing the index of a root dependency of a scope.

    Instances of this class are used to reference the direct dependencies of scopes in the shared dependency graph.
    These dependencies form the roots of the dependency trees spawned by scopes.
    """

    root: int = Field(
        ...,
        description="The index of the root dependency referenced by this object. Each package acting as a dependency "
        "is assigned a unique index. Storing an index rather than an identifier reduces the amount of "
        "memory consumed by this representation.",
    )
    fragment: int = Field(
        default=0,
        description="The index of the fragment of the dependency graph this reference points to. This is used to "
        "distinguish between packages that occur multiple times in the dependency graph with different "
        "dependencies.",
    )
