from fastapi import HTTPException, status
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.likes.models import Like
from app.likes.schemas import LikeStatus
from app.users.models import User
from app.videos.models import Video


def toggle(db: Session, video_id: str, user: User) -> LikeStatus:
    """Adds a like when absent and removes the caller's existing like otherwise."""
    if not db.get(Video, video_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Video not found.")

    like = db.query(Like).filter(Like.video_id == video_id, Like.user_id == user.id).first()
    if like:
        db.delete(like)
        liked = False
    else:
        db.add(Like(video_id=video_id, user_id=user.id))
        liked = True

    db.commit()
    like_count = db.query(func.count(Like.id)).filter(Like.video_id == video_id).scalar()
    return LikeStatus(liked=liked, like_count=like_count or 0)


def get_count(db: Session, video_id: str) -> LikeStatus:
    """Returns a video's public like count without requiring authentication."""
    if not db.get(Video, video_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Video not found.")
    like_count = db.query(func.count(Like.id)).filter(Like.video_id == video_id).scalar()
    return LikeStatus(liked=False, like_count=like_count or 0)
