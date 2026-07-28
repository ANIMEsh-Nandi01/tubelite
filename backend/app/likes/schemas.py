from pydantic import BaseModel


class LikeStatus(BaseModel):
    """The caller's resulting like state and the video's total likes."""

    liked: bool
    like_count: int
