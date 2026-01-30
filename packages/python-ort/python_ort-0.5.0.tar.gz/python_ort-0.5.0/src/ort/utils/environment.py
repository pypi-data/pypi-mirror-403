# SPDX-FileCopyrightText: 2025 Helio Chissini de Castro <heliocastro@gmail.com>
# SPDX-License-Identifier: MIT


from pydantic import BaseModel, ConfigDict, Field


class Environment(BaseModel):
    """
    A description of the environment that ORT was executed in.
    """

    model_config = ConfigDict(
        extra="allow",
    )

    ort_version: str = Field(
        description="The version of the OSS Review Toolkit as a string.",
    )
    build_jdk: str = Field(
        description="The version of Java used to build ORT.",
    )
    java_version: str = Field(
        description="The version of Java used to run ORT.",
    )
    os: str = Field(
        description="Name of the operating system, defaults to [Os.Name].",
    )
    processors: int = Field(
        description="The number of logical processors available.",
    )
    max_memory: int = Field(
        description="The maximum amount of memory available.",
    )
    variables: dict[str, str] = Field(
        default_factory=dict,
        description="Map of selected environment variables that might be relevant for debugging.",
    )
