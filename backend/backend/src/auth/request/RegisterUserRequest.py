from pydantic import BaseModel, Field, field_validator
from datetime import date
import re
from core.exceptions import ValidationError


class RegisterRequest(BaseModel):
    user_id: str = Field(
        ...,
        min_length=7,
        max_length=7,
        description="7-character user ID in format: 2 uppercase letters + 5 digits",
    )
    password: str = Field(..., min_length=8, description="Strong password")
    name: str = Field(
        ..., min_length=1, max_length=100, description="User's display name"
    )
    date_of_birth: date = Field(..., description="User's date of birth")
    command_id: int = Field(..., description="Command ID to assign to the user")

    @field_validator("user_id")
    @classmethod
    def validate_user_id(cls, v: str) -> str:
        if not re.match(r"^[A-Z]{2}[0-9]{5}$", v):
            raise ValidationError(
                "User ID must be in format: 2 uppercase letters followed by 5 digits (e.g., AB12345)"
            )
        return v

    @field_validator("password")
    @classmethod
    def validate_password(cls, v: str) -> str:
        from core.security import is_password_strong

        if not is_password_strong(v):
            raise ValidationError(
                "Password must be at least 8 characters with uppercase, lowercase, digit, and special character"
            )
        return v

    class Config:
        json_schema_extra = {
            "example": {
                "user_id": "AB12345",
                "password": "StrongPass123!",
                "name": "John Doe",
                "date_of_birth": "1990-01-01",
                "command_id": 1,
            }
        }
