from fastapi import APIRouter, Query, status

from app.auth.schemas import MessageResponse
from app.comments import service
from app.comments.schemas import CommentCreate, CommentOut, PaginatedComments
from app.dependencies import CurrentUser, DbSession

router = APIRouter()


# ---------------------------------------------------------------------------
# Routes nested under /videos/{video_id}
# Registered with prefix="/api" so the full path becomes /api/videos/{...}
# ---------------------------------------------------------------------------

@router.get(
    "/videos/{video_id}/comments",
    response_model=PaginatedComments,
    summary="List comments for a video",
)
def list_comments(
    video_id: str,
    db: DbSession,
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=50, ge=1, le=200),
) -> PaginatedComments:
    """
    Returns comments for a video ordered oldest-first (chronological).
    No authentication required.
    """
    return service.list_comments(db, video_id, page, limit)


@router.post(
    "/videos/{video_id}/comments",
    response_model=CommentOut,
    status_code=status.HTTP_201_CREATED,
    summary="Post a comment on a video",
)
def create_comment(
    video_id: str,
    data: CommentCreate,
    db: DbSession,
    current_user: CurrentUser,
) -> CommentOut:
    """
    Adds a comment to a video.
    Requires authentication.
    """
    return service.create(db, video_id, current_user, data)


# ---------------------------------------------------------------------------
# Routes at /comments/{comment_id}
# ---------------------------------------------------------------------------

@router.delete(
    "/comments/{comment_id}",
    response_model=MessageResponse,
    status_code=status.HTTP_200_OK,
    summary="Delete your own comment",
)
def delete_comment(
    comment_id: str,
    db: DbSession,
    current_user: CurrentUser,
) -> MessageResponse:
    """
    Permanently deletes a comment.
    Only the comment author may delete. Returns 403 otherwise.
    Requires authentication.
    """
    service.delete(db, comment_id, current_user)
    return MessageResponse(message="Comment deleted.")
