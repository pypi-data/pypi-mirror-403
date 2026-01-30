# SPDX-FileCopyrightText: 2025 Helio Chissini de Castro <heliocastro@gmail.com>
# SPDX-License-Identifier: MIT


from pydantic import BaseModel, ConfigDict, Field

from ort.models.identifier import Identifier
from ort.models.scope import Scope
from ort.models.vcsinfo import VcsInfo
from ort.utils.processed_declared_license import ProcessedDeclaredLicense


class Project(BaseModel):
    """
    A class describing a software project. A Project is very similar to a Package but contains some additional
    metadata like e.g. the homepage_url. Most importantly, it defines the dependency scopes that refer to the actual
    packages.
    """

    model_config = ConfigDict(
        extra="forbid",
    )

    id: Identifier = Field(
        ...,
        description="The unique identifier of this project. The id's type is the name of the package manager that"
        "manages this project (e.g. 'Gradle' for a Gradle project).",
    )
    cpe: str | None = Field(
        None, description="An optional additional identifier in CPE syntax (https://cpe.mitre.org/specification/)."
    )
    definition_file_path: str = Field(
        ...,
        description="The path to the definition file of this project, relative to the root of the repository described"
        "in vcs and vcs_processed.",
    )
    authors: set[str] = Field(default_factory=set, description="The set of authors declared for this project.")
    declared_licenses: set[str] = Field(
        ...,
        description="The set of licenses declared for this project. This does not necessarily correspond to the"
        "licenses as detected by a scanner. Both need to be taken into account for any conclusions.",
    )
    declared_licenses_processed: ProcessedDeclaredLicense = Field(
        ...,
        description="The declared licenses as SpdxExpression. If declared_licenses contains multiple licenses they are"
        "concatenated with SpdxOperator.AND.",
    )
    vcs: VcsInfo = Field(
        ...,
        description="Original VCS-related information as defined in the Project's metadata.",
    )
    vcs_processed: VcsInfo = Field(
        ...,
        description="Processed VCS-related information about the Project that has e.g. common mistakes corrected.",
    )
    description: str = Field(
        default_factory=str,
        description="The description of project.",
    )
    homepage_url: str = Field(..., description="The URL to the project's homepage.")
    scope_dependencies: set[Scope] | None = Field(
        None,
        description="Holds information about the scopes and their dependencies of this project if no DependencyGraph"
        "is available. NOTE: Do not use this property to access scope information. Use scopes instead, which is"
        "correctly initialized in all cases.",
    )
    scope_names: set[str] | None = Field(
        None,
        description="Contains dependency information as a set of scope names in case a shared DependencyGraph is used."
        "The scopes of this project and their dependencies can then be constructed as the corresponding sub graph of"
        "the shared graph.",
    )

    def __hash__(self) -> int:
        return hash(self.id)

    def __eq__(self, other) -> bool:
        if not isinstance(other, Project):
            return NotImplemented
        return self.id == other.id
