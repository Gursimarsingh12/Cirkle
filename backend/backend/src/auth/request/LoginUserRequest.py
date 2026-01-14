from datetime import date
from pydantic import BaseModel, Field, field_validator
import re
from core.security import is_password_strong
from core.exceptions import ValidationError


class LoginRequest(BaseModel):
    user_id: str = Field(..., min_length=7, max_length=7)
    password: str = Field(..., min_length=1)

    @field_validator("user_id")
    @classmethod
    def validate_user_id(cls, v: str) -> str:
        if not re.match(r"^[A-Z]{2}[0-9]{5}$", v):
            raise ValidationError(
                "User ID must be in format: 2 uppercase letters followed by 5 digits (e.g., AB12345)"
            )
        return v
    class Config:
        json_schema_extra = {
            "example": {
                "user_id": "TU12345",
                "password": "Test@123"
            }
        }

class ForgotPasswordRequest(BaseModel):
    user_id: str = Field(..., min_length=7, max_length=7)
    date_of_birth: date
    new_password: str = Field(..., min_length=8)

    @field_validator("user_id")
    @classmethod
    def validate_user_id(cls, v: str) -> str:
        if not re.match(r"^[A-Z]{2}[0-9]{5}$", v):
            raise ValidationError(
                "User ID must be in format: 2 uppercase letters followed by 5 digits (e.g., AB12345)"
            )
        return v

    @field_validator("new_password")
    @classmethod
    def validate_password(cls, v: str) -> str:
        if not is_password_strong(v):
            raise ValidationError(
                "Password must be at least 8 characters with uppercase, lowercase, digit, and special character"
            )
        return v
