# SPDX-FileCopyrightText: 2025 Helio Chissini de Castro <heliocastro@gmail.com>
# SPDX-License-Identifier: MIT


from pydantic import BaseModel, ConfigDict, Field


class DependencyGraphEdge(BaseModel):
    """
    A data class representing an edge in the dependency graph.

    An edge corresponds to a directed depends-on relationship between two packages. The packages are identified by the
    numeric indices into the list of nodes.
    """

    model_config = ConfigDict(
        extra="forbid",
        frozen=True,
    )

    from_: int = Field(
        ...,
        alias="from",
        description="The index of the source node of this edge.",
    )
    to_: int = Field(
        ...,
        alias="to",
        description="The index of the destination node of this edge.",
    )
