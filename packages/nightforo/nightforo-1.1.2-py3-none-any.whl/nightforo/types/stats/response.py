from pydantic import BaseModel

from .stats import LatestUser, Online, Totals

__all__ = ("StatsResponse",)


class StatsResponse(BaseModel):
    totals: Totals
    latest_user: LatestUser
    online: Online
