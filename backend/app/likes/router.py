from fastapi import APIRouter

from app.dependencies import CurrentUser, DbSession
from app.likes import service
from app.likes.schemas import LikeStatus

router = APIRouter()


@router.get("/{video_id}/like", response_model=LikeStatus, summary="Get a video's like count")
def get_like_count(video_id: str, db: DbSession) -> LikeStatus:
    return service.get_count(db, video_id)


@router.post("/{video_id}/like", response_model=LikeStatus, summary="Like or unlike a video")
def toggle_like(video_id: str, db: DbSession, current_user: CurrentUser) -> LikeStatus:
    return service.toggle(db, video_id, current_user)
