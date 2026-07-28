from fastapi import APIRouter, Query

from app.dependencies import CurrentUser, DbSession
from app.users import service
from app.users.schemas import UserProfile, UserPublic, UserUpdate
from app.videos.schemas import PaginatedVideos

router = APIRouter()


@router.patch("/me", response_model=UserPublic, summary="Update the current user's profile")
def update_me(data: UserUpdate, db: DbSession, current_user: CurrentUser) -> UserPublic:
    return service.update_profile(db, current_user, data)


@router.get("/{username}", response_model=UserProfile, summary="Get a public channel profile")
def get_profile(username: str, db: DbSession) -> UserProfile:
    return service.get_profile(db, username)


@router.get("/{username}/videos", response_model=PaginatedVideos, summary="List a channel's videos")
def list_user_videos(
    username: str,
    db: DbSession,
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=20, ge=1, le=100),
) -> PaginatedVideos:
    return service.list_videos(db, username, page, limit)
