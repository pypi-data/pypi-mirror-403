# SPDX-FileCopyrightText: 2025 Helio Chissini de Castro <heliocastro@gmail.com>
# SPDX-License-Identifier: MIT


from pydantic import BaseModel, ConfigDict, Field

from ort.models.identifier import Identifier
from ort.models.remote_artifact import RemoteArtifact
from ort.models.source_code_origin import SourceCodeOrigin
from ort.models.vcsinfo import VcsInfo
from ort.utils.processed_declared_license import ProcessedDeclaredLicense


class Package(BaseModel):
    """
    A generic descriptor for a software package. It contains all relevant metadata about a package like the name,
    version, and how to retrieve the package and its source code. It does not contain information about the package's
    dependencies, however. This is because at this stage ORT would only be able to get the declared dependencies,
    whereas the resolved dependencies are of interest. Resolved dependencies might differ from declared dependencies
    due to specified version ranges, or change depending on how the package is used in a project due to the build
    system's dependency resolution process. For example, if multiple versions of the same package are used in a
    project, the build system might decide to align on a single version of that package.
    """

    model_config = ConfigDict(
        extra="forbid",
    )

    id: Identifier = Field(
        description="The unique identifier of this package. The id's type is the name of the package type or protocol "
        "(e.g. 'Maven' for a file from a Maven repository).",
    )

    purl: str = Field(
        ...,
        description="An additional identifier in package URL syntax (https://github.com/package-url/purl-spec).",
    )

    cpe: str | None = Field(
        default=None,
        description="An optional additional identifier in CPE syntax (https://cpe.mitre.org/specification/).",
    )

    authors: set[str] = Field(
        default_factory=set,
        description="The set of authors declared for this package.",
    )

    declared_licenses: set[str] = Field(
        ...,
        description="The set of licenses declared for this package. This does not necessarily correspond to"
        "the licenses as detected by a scanner. Both need to be taken into account for any conclusions.",
    )

    declared_licenses_processed: ProcessedDeclaredLicense = Field(
        ...,
        description="The declared licenses as SpdxExpression. If declared_licenses contains multiple licenses they are "
        "concatenated with SpdxOperator.AND.",
    )

    concluded_license: str | None = Field(
        default=None,
        description="The concluded license as an SpdxExpression. It can be used to override the declared/detected "
        "licenses of a package. ORT itself does not set this field, it needs to be set by the user using a "
        "PackageCuration.",
    )

    description: str = Field(
        ...,
        description="The description of the package, as provided by the package manager.",
    )

    homepage_url: str = Field(
        ...,
        description="The homepage of the package.",
    )

    binary_artifact: RemoteArtifact = Field(
        ...,
        description="The remote artifact where the binary package can be downloaded.",
    )

    source_artifact: RemoteArtifact = Field(
        ...,
        description="The remote artifact where the source package can be downloaded.",
    )

    vcs: VcsInfo = Field(
        ...,
        description="Original VCS-related information as defined in the package's metadata.",
    )

    vcs_processed: VcsInfo = Field(
        ...,
        description="Processed VCS-related information about the package in normalized form. The information is either "
        "derived from vcs, guessed from additional data as a fallback, or empty. On top of that PackageCurations may "
        "have been applied.",
    )

    is_metadata_only: bool = Field(
        default=False,
        description="Indicates whether the package is just metadata, like e.g. Maven BOM artifacts which only define "
        "constraints for dependency versions.",
    )

    is_modified: bool = Field(
        default=False,
        description="Indicates whether the source code of the package has been modified compared to the original source"
        "code, e.g., in case of a fork of an upstream Open Source project.",
    )

    source_code_origins: list[SourceCodeOrigin] | None = Field(
        default=None,
        description="The considered source code origins and their priority order to use for this package. If null, the "
        "configured default is used. If not null, this must not be empty and not contain any duplicates.",
    )

    labels: dict[str, str] = Field(
        default_factory=dict,
        description="User defined labels associated with this package. The labels are not interpreted by the core of"
        "ORT itself, but can be used in parts of ORT such as plugins, in evaluator rules, or in reporter templates.",
    )

    def __hash__(self) -> int:
        return hash(self.id)

    def __eq__(self, other) -> bool:
        if not isinstance(other, Package):
            return NotImplemented
        return self.id == other.id
