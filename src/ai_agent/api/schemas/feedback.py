from typing import Optional

from pydantic import BaseModel, field_validator


class FeedbackCreate(BaseModel):
    rating: int
    comment: Optional[str] = None

    @field_validator("rating")
    @classmethod
    def validate_rating(cls, v: int) -> int:
        if v not in (1, -1):
            raise ValueError("rating must be 1 (positive) or -1 (negative)")
        return v
