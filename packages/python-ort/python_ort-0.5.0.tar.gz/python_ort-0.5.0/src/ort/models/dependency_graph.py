# SPDX-FileCopyrightText: 2025 Helio Chissini de Castro <heliocastro@gmail.com>
# SPDX-License-Identifier: MIT


from pydantic import BaseModel, ConfigDict, Field, field_validator

from ort.models.dependency_graph_edge import DependencyGraphEdge
from ort.models.dependency_graph_node import DependencyGraphNode
from ort.models.dependency_reference import DependencyReference
from ort.models.identifier import Identifier
from ort.models.root_dependency_index import RootDependencyIndex


class DependencyGraph(BaseModel):
    """
    Represents the graph of dependencies of a project.

    This class holds information about a project's scopes and their dependencies in a format that minimizes the
    consumption of memory. In projects with many scopes there is often a high degree of duplication in the dependencies
    of the scopes. To avoid this, this class aims to share as many parts of the dependency graph as possible between
    the different scopes. Ideally, there is only a single dependency graph containing the dependencies used by all
    scopes. This is not always possible due to inconsistencies in dependency relations, like a package using different
    dependencies in different scopes. Then the dependency graph is split into multiple fragments, and each fragment has
    a consistent view on the dependencies it contains.

    When constructing a dependency graph the dependencies are organized as a connected structure of DependencyReference
    objects in memory. Originally, the serialization format of a graph was based on this structure, but that turned out
    to be not ideal: During serialization, sub graphs referenced from multiple nodes (e.g. libraries with transitive
    dependencies referenced from multiple projects) get duplicated, which can cause a significant amount of redundancy.
    Therefore, the data representation has been changed again to a form, which can be serialized without introducing
    redundancy. It consists of the following elements:

    - packages: A list with the coordinates of all the packages (free of duplication) that are referenced by the graph.
      This allows extracting the packages directly, but also has the advantage that the package coordinates do not have
      to be repeated over and over: All the references to packages are expressed by indices into this list.
    - nodes: An ordered list with the nodes of the dependency graph. A single node represents a package, and therefore
      has a reference into the list with package coordinates. It can, however, happen that packages occur multiple
      times in the graph if they are in different subtrees with different sets of transitive dependencies. Then there
      are multiple nodes for the packages affected, and a fragment_index is used to identify them uniquely. Nodes also
      store information about issues of a package and their linkage.
    - edges: Here the structure of the graph comes in. Each edge connects two nodes and represents a directed
      depends-on relationship. The nodes are referenced by numeric indices into the list of nodes.
    - scopes: This is a map that associates the scopes used by projects with their direct dependencies. A single
      dependency graph contains the dependencies of all the projects processed by a specific package manager.
      Therefore, the keys of this map are scope names qualified by the coordinates of a project; which makes them
      unique. The values are references to the nodes in the graph that correspond to the packages the scopes depend on
      directly.

    To navigate this structure, start with a scope and gather the references to its direct dependency nodes. Then, by
    following the edges starting from these nodes, the set of transitive dependencies can be determined. The numeric
    indices can be resolved via the packages list.
    """

    model_config = ConfigDict(
        extra="forbid",
    )

    packages: list[Identifier] = Field(
        default_factory=list,
        description="A list with the identifiers of the packages that appear in the dependency graph. This list is "
        "used to resolve the numeric indices contained in the dependency_graph_node objects.",
    )

    scope_roots: set[DependencyReference] = Field(
        default_factory=set,
        description="Stores the dependency graph as a list of root nodes for the direct dependencies referenced by "
        "scopes. Starting with these nodes, the whole graph can be traversed. The nodes are constructed "
        "from the direct dependencies declared by scopes that cannot be reached via other paths in the "
        "dependency graph. Note that this property exists for backwards compatibility only; it is replaced "
        "by the lists of nodes and edges.",
    )

    scopes: dict[str, list[RootDependencyIndex]] = Field(
        default_factory=dict,
        description="A mapping from scope names to the direct dependencies of the scopes. Based on this information, "
        "the set of scopes of a project can be constructed from the serialized form.",
    )

    nodes: list[DependencyGraphNode] = Field(
        default_factory=list,
        description="A list with the nodes of this dependency graph. Nodes correspond to packages, but in contrast to "
        "the packages list, there can be multiple nodes for a single package. The order of nodes in this "
        "list is relevant; the edges of the graph reference their nodes by numeric indices.",
    )

    edges: set[DependencyGraphEdge] = Field(
        default_factory=set,
        description="A set with the edges of this dependency graph. By traversing the edges, the dependencies of "
        "packages can be determined.",
    )

    @field_validator("edges", mode="before")
    @classmethod
    def sort_and_set_edges(cls, v):
        if v is None:
            return set()

        return {DependencyGraphEdge.model_validate(e) for e in v}
