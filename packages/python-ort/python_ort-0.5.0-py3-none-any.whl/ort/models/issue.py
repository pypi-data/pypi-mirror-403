# SPDX-FileCopyrightText: 2025 Helio Chissini de Castro <heliocastro@gmail.com>
# SPDX-License-Identifier: MIT


from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from ort.severity import Severity


class Issue(BaseModel):
    """
    An issue that occurred while executing ORT.
    """

    model_config = ConfigDict(
        extra="forbid",
    )

    timestamp: datetime = Field(
        description="The timestamp of the issue.",
    )
    source: str = Field(
        description="A description of the issue source, e.g. the tool that caused the issue.",
    )
    message: str = Field(
        description="The issue's message.",
    )
    severity: Severity = Field(
        description="The issue's severity.",
    )
    affected_path: str | None = Field(
        default=None,
        description="The affected file or directory the issue is limited to, if any.",
    )
