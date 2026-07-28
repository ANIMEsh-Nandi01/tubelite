from datetime import datetime

from pydantic import BaseModel, ConfigDict


class UserPublic(BaseModel):
    """
    The shape of a user object returned to any API consumer.
    Deliberately excludes password_hash and any other internal fields.
    """

    id: str
    username: str
    email: str
    avatar_url: str | None
    bio: str | None
    created_at: datetime

    # Allow constructing this schema directly from a SQLAlchemy ORM object
    model_config = ConfigDict(from_attributes=True)


class UserUpdate(BaseModel):
    """Fields a user is allowed to update on their own profile."""

    username: str | None = None
    bio: str | None = None
