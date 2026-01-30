# SPDX-FileCopyrightText: 2025 Helio Chissini de Castro <heliocastro@gmail.com>
# SPDX-License-Identifier: MIT

from enum import Enum, auto


class Severity(Enum):
    """
    A generic class describing a severity, e.g. of issues, sorted from least severe to most severe.

    Members:
        HINT: A hint is something that is provided for information only.
        WARNING: A warning is something that should be addressed.
        ERROR: An error is something that has to be addressed.
    """

    HINT = auto()
    WARNING = auto()
    ERROR = auto()
