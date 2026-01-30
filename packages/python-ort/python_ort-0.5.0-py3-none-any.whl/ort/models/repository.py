# SPDX-FileCopyrightText: 2025 Helio Chissini de Castro <heliocastro@gmail.com>
# SPDX-License-Identifier: MIT


from pydantic import BaseModel, ConfigDict, Field

from ort.models.repository_configuration import OrtRepositoryConfiguration
from ort.models.vcsinfo import VcsInfo


class Repository(BaseModel):
    """
    A description of the source code repository that was used as input for ORT.

    Attributes:
        vcs(VcsInfo): Original VCS-related information from the working tree containing the analyzer root.
        vcs_processed(VcsInfo): Processed VCS-related information from the working tree containing the analyzer root
            that has e.g. common mistakes corrected.
        nested_repositories(dict[str, VcsInfo]): A map of nested repositories, for example Git submodules or Git-Repo
            modules. The key is the path to the nested repository relative to the root of the main repository.
        config(OrtRepositoryConfiguration): The configuration of the repository, parsed from [ORT_REPO_CONFIG_FILENAME].

    """

    model_config = ConfigDict(
        extra="forbid",
    )
    vcs: VcsInfo = Field(
        description="Original VCS-related information from the working tree containing the analyzer root."
    )
    vcs_processed: VcsInfo = Field(
        description="Processed VCS-related information from the working tree containing the analyzer root"
        " that has e.g. common mistakes corrected."
    )
    nested_repositories: dict[str, VcsInfo] = Field(
        default_factory=dict,
        description="A map of nested repositories, for example Git submodules or Git-Repo"
        "modules. The key is the path to the nested repository relative to the root of the main repository.",
    )
    config: OrtRepositoryConfiguration = Field(
        description="The configuration of the repository, parsed from [ORT_REPO_CONFIG_FILENAME]."
    )
