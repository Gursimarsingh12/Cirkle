from pydantic import BaseModel, Field


class UserActivityStatsResponse(BaseModel):
    total_users: int = Field(...)
    active_users: int = Field(...)
    online_users: int = Field(...)
