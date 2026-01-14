from datetime import date, datetime
from pydantic import BaseModel


class UserResponse(BaseModel):
    user_id: str
    date_of_birth: date
    is_private: bool
    is_active: bool
    created_at: datetime
    is_online: bool
