from fastapi import APIRouter, File, Form, Query, UploadFile, status

from app.auth.schemas import MessageResponse
from app.dependencies import CurrentUser, DbSession
from app.videos import service
from app.videos.schemas import PaginatedVideos, StreamResponse, VideoOut, VideoUpdate

router = APIRouter()

# ---------------------------------------------------------------------------
# IMPORTANT: routes with literal path segments (/search, /stream) MUST be
# declared before /{id} routes, otherwise FastAPI matches the literal as an ID.
# ---------------------------------------------------------------------------


@router.get(
    "/search",
    response_model=PaginatedVideos,
    summary="Search videos by title",
)
def search_videos(
    db: DbSession,
    q: str = Query(..., min_length=1, description="Search query string"),
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=20, ge=1, le=100),
) -> PaginatedVideos:
    """
    Returns videos whose title contains the query string (case-insensitive).
    Results are paginated and ordered newest-first.
    """
    total, items = service.search_videos(db, q, page, limit)
    return PaginatedVideos(total=total, page=page, limit=limit, items=items)


@router.get(
    "",
    response_model=PaginatedVideos,
    summary="List all videos (homepage feed)",
)
def list_videos(
    db: DbSession,
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=20, ge=1, le=100),
) -> PaginatedVideos:
    """
    Returns all ready videos ordered by newest-first.
    Used for the homepage grid.
    """
    total, items = service.list_videos(db, page, limit)
    return PaginatedVideos(total=total, page=page, limit=limit, items=items)


@router.post(
    "",
    response_model=VideoOut,
    status_code=status.HTTP_201_CREATED,
    summary="Upload a new video",
)
def upload_video(
    db: DbSession,
    current_user: CurrentUser,
    title: str = Form(..., min_length=1, max_length=255),
    description: str | None = Form(default=None),
    video_file: UploadFile = File(..., description="Video file (mp4 or webm, max 500 MB)"),
    thumbnail_file: UploadFile | None = File(default=None, description="Thumbnail image (optional, max 5 MB)"),
) -> VideoOut:
    """
    Uploads a video (and optional thumbnail) to Cloudflare R2, then saves
    metadata to the database. Status is set to 'ready' immediately.

    Requires authentication.
    """
    return service.create(
        db=db,
        user=current_user,
        title=title,
        description=description,
        video_file=video_file,
        thumbnail_file=thumbnail_file,
    )


@router.get(
    "/{video_id}",
    response_model=VideoOut,
    summary="Get video metadata (increments view count)",
)
def get_video(video_id: str, db: DbSession) -> VideoOut:
    """
    Returns metadata for a single video and increments its view count.
    Called by the watch page on initial load. No auth required.
    """
    return service.get_by_id(db, video_id)


@router.get(
    "/{video_id}/stream",
    response_model=StreamResponse,
    summary="Get a presigned URL for video playback",
)
def stream_video(video_id: str, db: DbSession) -> StreamResponse:
    """
    Returns a time-limited presigned URL pointing directly to the video file
    in Cloudflare R2. The frontend sets this as the `<video src>`.

    The URL expires in 1 hour. No auth required (public videos).
    """
    url = service.get_stream_url(db, video_id)
    return StreamResponse(url=url, expires_in=3600)


@router.patch(
    "/{video_id}",
    response_model=VideoOut,
    summary="Edit video title or description",
)
def update_video(
    video_id: str,
    data: VideoUpdate,
    db: DbSession,
    current_user: CurrentUser,
) -> VideoOut:
    """
    Updates the title and/or description of a video.
    Only the video owner may call this. Returns 403 otherwise.
    """
    return service.update(db, video_id, current_user, data)


@router.delete(
    "/{video_id}",
    response_model=MessageResponse,
    status_code=status.HTTP_200_OK,
    summary="Delete a video",
)
def delete_video(
    video_id: str,
    db: DbSession,
    current_user: CurrentUser,
) -> MessageResponse:
    """
    Permanently deletes the video file and thumbnail from R2, and removes
    all database records (video, comments, likes) via CASCADE.
    Only the video owner may call this. Returns 403 otherwise.
    """
    service.delete(db, video_id, current_user)
    return MessageResponse(message="Video deleted successfully.")
