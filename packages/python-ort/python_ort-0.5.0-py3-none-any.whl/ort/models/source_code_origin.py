# SPDX-FileCopyrightText: 2025 Helio Chissini de Castro <heliocastro@gmail.com>
# SPDX-License-Identifier: MIT

from enum import Enum


class SourceCodeOrigin(Enum):
    """
    An enumeration of supported source code origins.
    """

    vcs = "VCS"
    artifact = "ARTIFACT"
