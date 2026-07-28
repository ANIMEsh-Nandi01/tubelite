import uuid
from datetime import datetime, timezone

from sqlalchemy import String, DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


def _now() -> datetime:
    return datetime.now(timezone.utc)


class Like(Base):
    __tablename__ = "likes"

    # Enforce one like per user per video at the database level
    __table_args__ = (
        UniqueConstraint("video_id", "user_id", name="uq_likes_video_user"),
    )

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    video_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("videos.id", ondelete="CASCADE"), nullable=False
    )
    user_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=_now, nullable=False
    )

    # Relationships
    video: Mapped["Video"] = relationship("Video", back_populates="likes")  # noqa: F821
    user: Mapped["User"] = relationship("User", back_populates="likes")  # noqa: F821

    def __repr__(self) -> str:
        return f"<Like video_id={self.video_id} user_id={self.user_id}>"
