# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from typing import Optional
from datetime import datetime
from typing_extensions import Literal

from .._models import BaseModel
from .shared.identity import Identity

__all__ = ["BuildRetrieveResponse"]


class BuildRetrieveResponse(BaseModel):
    account_id: str

    build_id: str

    created_at: datetime

    created_by: Identity
    """The identity that created the entity."""

    image_name: str

    image_tag: str

    image_url: str

    status: str
    """The current build status from the cloud provider"""

    build_end_time: Optional[datetime] = None
    """When the cloud provider finished the build"""

    build_start_time: Optional[datetime] = None
    """When the cloud provider started the build"""

    object: Optional[Literal["agentex_cloud_build"]] = None
