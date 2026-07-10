from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator


class CreateFeedbackRequest(BaseModel):
    rating: int = Field(ge=1, le=5)
    is_helpful: bool
    comment: str | None = Field(default=None, max_length=2000)

    @field_validator("comment")
    @classmethod
    def normalize_comment(cls, value: str | None) -> str | None:
        if value is None:
            return None
        normalized = " ".join(value.strip().split())
        return normalized or None


class FeedbackResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    query_log_id: int
    user_id: int
    rating: int
    is_helpful: bool
    comment: str | None
    created_at: datetime
