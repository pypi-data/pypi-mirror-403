# SPDX-FileCopyrightText: 2025 Helio Chissini de Castro <heliocastro@gmail.com>
# SPDX-License-Identifier: MIT


from enum import Enum, auto


class PackageLinkage(Enum):
    """
    A class to denote the linkage type between two packages.

    Members:
        DYNAMIC:
            A dynamically linked package whose source code is not directly defined in the project itself,
            but which is retrieved as an external artifact.

        STATIC:
            A statically linked package whose source code is not directly defined in the project itself,
            but which is retrieved as an external artifact.

        PROJECT_DYNAMIC:
            A dynamically linked package whose source code is part of the project itself,
            e.g. a subproject of a multi-project.

        PROJECT_STATIC:
            A statically linked package whose source code is part of the project itself,
            e.g. a subproject of a multi-project.
    """

    DYNAMIC = auto()
    STATIC = auto()
    PROJECT_DYNAMIC = auto()
    PROJECT_STATIC = auto()
