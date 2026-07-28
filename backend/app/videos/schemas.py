from datetime import datetime

from pydantic import BaseModel, ConfigDict, field_validator

from app.users.schemas import UserProfile


# ---------------------------------------------------------------------------
# Request schemas
# ---------------------------------------------------------------------------


class VideoUpdate(BaseModel):
    """Fields the owner is allowed to update."""

    title: str | None = None
    description: str | None = None

    @field_validator("title")
    @classmethod
    def title_not_blank(cls, v: str | None) -> str | None:
        if v is not None and not v.strip():
            raise ValueError("Title cannot be blank.")
        return v


# ---------------------------------------------------------------------------
# Response schemas
# ---------------------------------------------------------------------------


class VideoOut(BaseModel):
    """
    Full video metadata returned by GET /videos/{id} and POST /videos.
    thumbnail_url is a pre-generated presigned URL (valid 1 hour).
    The actual video stream URL is fetched separately via GET /videos/{id}/stream.
    """

    id: str
    title: str
    description: str | None
    thumbnail_url: str | None  # Presigned URL, injected by service layer
    duration: int | None
    view_count: int
    status: str
    created_at: datetime
    updated_at: datetime
    author: UserProfile

    model_config = ConfigDict(from_attributes=True)


class PaginatedVideos(BaseModel):
    """Paginated list of videos returned by GET /videos and GET /videos/search."""

    total: int
    page: int
    limit: int
    items: list[VideoOut]


class StreamResponse(BaseModel):
    """Presigned R2 URL returned by GET /videos/{id}/stream."""

    url: str
    expires_in: int  # seconds
