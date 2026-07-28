from fastapi import HTTPException, status
from sqlalchemy.orm import Session, joinedload

from app.users.models import User
from app.users.schemas import UserProfile, UserUpdate
from app.videos import service as video_service
from app.videos.models import Video, VideoStatus
from app.videos.schemas import PaginatedVideos


def get_profile(db: Session, username: str) -> UserProfile:
    user = db.query(User).filter(User.username == username).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found.")
    return UserProfile.model_validate(user)


def update_profile(db: Session, user: User, data: UserUpdate) -> User:
    if data.username is not None:
        username = data.username.strip()
        if not username:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Username cannot be blank.",
            )
        existing = db.query(User).filter(User.username == username, User.id != user.id).first()
        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="This username is already taken.",
            )
        user.username = username
    if data.bio is not None:
        user.bio = data.bio.strip() or None
    db.commit()
    db.refresh(user)
    return user


def list_videos(db: Session, username: str, page: int, limit: int) -> PaginatedVideos:
    user = db.query(User).filter(User.username == username).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found.")

    offset = (page - 1) * limit
    query = (
        db.query(Video)
        .options(joinedload(Video.author))
        .filter(Video.user_id == user.id, Video.status == VideoStatus.ready)
        .order_by(Video.created_at.desc())
    )
    total = query.count()
    videos = query.offset(offset).limit(limit).all()
    return PaginatedVideos(
        total=total,
        page=page,
        limit=limit,
        items=[video_service._to_out(video) for video in videos],
    )
