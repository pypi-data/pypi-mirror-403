# SPDX-FileCopyrightText: 2025 Helio Chissini de Castro <heliocastro@gmail.com>
# SPDX-License-Identifier: MIT


from pydantic import BaseModel, ConfigDict, Field


class ProcessedDeclaredLicense(BaseModel):
    """
    The resulting SPDX expression, or null if no license could be mapped.
    """

    model_config = ConfigDict(
        extra="forbid",
    )

    spdx_expression: str | None = Field(
        default=None,
        description="The resulting SPDX expression, or null if no license could be mapped.",
    )
    mapped: dict[str, str] = Field(
        default_factory=dict,
        description="A map from the original declared license strings to the SPDX expressions they were mapped to. "
        "If the original declared license string and the processed declared license are identical they "
        "are not contained in this map.",
    )
    unmapped: set[str] = Field(
        default_factory=set,
        description="Declared licenses that could not be mapped to an SPDX expression.",
    )
