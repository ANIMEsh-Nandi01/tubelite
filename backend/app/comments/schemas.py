from datetime import datetime

from pydantic import BaseModel, ConfigDict, field_validator

from app.users.schemas import UserPublic


class CommentCreate(BaseModel):
    content: str

    @field_validator("content")
    @classmethod
    def content_not_blank(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("Comment cannot be blank.")
        if len(v) > 2000:
            raise ValueError("Comment cannot exceed 2000 characters.")
        return v


class CommentOut(BaseModel):
    id: str
    content: str
    created_at: datetime
    author: UserPublic

    model_config = ConfigDict(from_attributes=True)


class PaginatedComments(BaseModel):
    total: int
    page: int
    limit: int
    items: list[CommentOut]
