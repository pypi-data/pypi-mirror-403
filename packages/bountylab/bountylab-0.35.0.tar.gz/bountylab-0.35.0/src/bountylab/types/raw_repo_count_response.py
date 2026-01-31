# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from typing import Optional

from .._models import BaseModel

__all__ = ["RawRepoCountResponse"]


class RawRepoCountResponse(BaseModel):
    count: int
    """Number of matching records (may be capped or floored)"""

    truncated: Optional[bool] = None
    """True if count was capped at maximum or floored at minimum"""
