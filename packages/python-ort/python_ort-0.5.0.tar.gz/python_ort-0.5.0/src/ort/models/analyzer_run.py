# SPDX-FileCopyrightText: 2025 Helio Chissini de Castro <heliocastro@gmail.com>
# SPDX-License-Identifier: MIT

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from ort.models.analyzer_result import AnalyzerResult
from ort.models.config.analyzer_configuration import AnalyzerConfiguration
from ort.utils.environment import Environment


class AnalyzerRun(BaseModel):
    """
    The summary of a single run of the analyzer.

    """

    model_config = ConfigDict(
        extra="forbid",
    )
    start_time: datetime = Field(
        description="The time the analyzer was started.",
    )
    end_time: datetime = Field(
        description="The time the analyzer has finished.",
    )
    environment: Environment = Field(
        description="The [Environment] in which the analyzer was executed.",
    )
    config: AnalyzerConfiguration = Field(
        description="The [AnalyzerConfiguration] used for this run.",
    )
    result: AnalyzerResult | None = Field(
        default=None,
        description="The result of this run.",
    )
