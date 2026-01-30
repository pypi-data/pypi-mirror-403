# SPDX-FileCopyrightText: 2025 Helio Chissini de Castro <heliocastro@gmail.com>
# SPDX-License-Identifier: MIT


from pydantic import BaseModel, ConfigDict, Field

from ort.models.package_reference import PackageReference


class Scope(BaseModel):
    """
    The scope class puts package dependencies into context.
    """

    model_config = ConfigDict(
        extra="forbid",
    )

    name: str = Field(
        description='The respective package manager\'s native name for the scope, e.g. "compile", "provided" etc. '
        'for Maven, or "dependencies", "devDependencies" etc. for NPM.',
    )
    dependencies: set[PackageReference] = Field(
        description="The set of references to packages in this scope. Note that only the first-order packages in this "
        "set actually belong to the scope of 'name'. Transitive dependency packages usually belong to the "
        "scope that describes the packages required to compile the product. As an example, if this was the "
        "Maven \"test\" scope, all first-order items in 'dependencies' would be packages required for "
        "testing the product. But transitive dependencies would not be test dependencies of the test "
        "dependencies, but compile dependencies of test dependencies.",
    )
