from pydantic import BaseModel, Field


class UserTypeStatsResponse(BaseModel):
    total_users: int = Field(...)
    total_prime: int = Field(...)
    total_organizational: int = Field(...)
    total_private: int = Field(...)
    total_public: int = Field(...)
