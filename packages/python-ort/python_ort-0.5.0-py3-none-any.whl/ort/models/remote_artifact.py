# SPDX-FileCopyrightText: 2025 Helio Chissini de Castro <heliocastro@gmail.com>
# SPDX-License-Identifier: MIT


from pydantic import BaseModel, Field

from ort.models.hash import Hash


class RemoteArtifact(BaseModel):
    """
    Bundles information about a remote artifact.
    """

    url: str = Field(
        description="The URL of the remote artifact.",
    )
    hash: Hash = Field(
        description="The hash of the remote artifact.",
    )
