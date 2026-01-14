from datetime import date
from pydantic import BaseModel, Field, field_validator
import re
from core.exceptions import ValidationError


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
        from core.security import is_password_strong

        if not is_password_strong(v):
            raise ValidationError(
                "Password must be at least 8 characters with uppercase, lowercase, digit, and special character"
            )
        return v
