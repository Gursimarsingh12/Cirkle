from typing import List, Dict, Any
from pydantic import BaseModel, Field


class InterestsResponse(BaseModel):
    interests: List[Dict[str, Any]] = Field(...)
