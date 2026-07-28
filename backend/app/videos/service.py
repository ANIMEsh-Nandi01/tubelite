import uuid
from typing import BinaryIO

from fastapi import HTTPException, UploadFile, status
from sqlalchemy import func, or_
from sqlalchemy.orm import Session, joinedload

from app.storage import r2
from app.users.models import User
from app.videos.models import Video, VideoStatus
from app.videos.schemas import VideoOut, VideoUpdate

# ---------------------------------------------------------------------------
# File validation constants
# ---------------------------------------------------------------------------
ALLOWED_VIDEO_TYPES = {"video/mp4", "video/webm"}
ALLOWED_IMAGE_TYPES = {"image/jpeg", "image/png", "image/webp"}
MAX_VIDEO_SIZE = 500 * 1024 * 1024   # 500 MB
MAX_IMAGE_SIZE = 5 * 1024 * 1024     # 5 MB


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _make_video_key(user_id: str, video_id: str, content_type: str) -> str:
    ext = "webm" if content_type == "video/webm" else "mp4"
    return f"videos/{user_id}/{video_id}.{ext}"


def _make_thumbnail_key(user_id: str, video_id: str, content_type: str) -> str:
    ext_map = {"image/png": "png", "image/webp": "webp"}
    ext = ext_map.get(content_type, "jpg")
    return f"thumbnails/{user_id}/{video_id}.{ext}"


def _validate_file(file: UploadFile, allowed_types: set[str], max_size: int, label: str) -> None:
    """Raises 400 if the uploaded file fails content-type or size checks."""
    if file.content_type not in allowed_types:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"{label} must be one of: {', '.join(sorted(allowed_types))}. "
                   f"Got '{file.content_type}'.",
        )
    if file.size is not None and file.size > max_size:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"{label} exceeds the {max_size // (1024 * 1024)} MB limit.",
        )


def _enrich(video: Video) -> dict:
    """
    Converts a Video ORM object into a dict with presigned thumbnail_url injected.
    This dict is then passed to VideoOut.model_validate() for serialisation.
    """
    thumbnail_url: str | None = None
    if video.thumbnail_key:
        try:
            thumbnail_url = r2.get_presigned_url(video.thumbnail_key, expires_in=3600)
        except Exception:
            thumbnail_url = None

    data = {
        "id": video.id,
        "title": video.title,
        "description": video.description,
        "thumbnail_url": thumbnail_url,
        "duration": video.duration,
        "view_count": video.view_count,
        "status": video.status.value,
        "created_at": video.created_at,
        "updated_at": video.updated_at,
        "author": video.author,
    }
    return data


def _to_out(video: Video) -> VideoOut:
    return VideoOut.model_validate(_enrich(video))


# ---------------------------------------------------------------------------
# Service functions
# ---------------------------------------------------------------------------

def create(
    db: Session,
    user: User,
    title: str,
    description: str | None,
    video_file: UploadFile,
    thumbnail_file: UploadFile | None,
) -> VideoOut:
    """
    Validates, uploads to R2, and saves metadata to the database.
    Status is set to 'ready' immediately (no transcoding in v1).
    """
    # -- Validate files --
    _validate_file(video_file, ALLOWED_VIDEO_TYPES, MAX_VIDEO_SIZE, "Video file")
    if thumbnail_file and thumbnail_file.filename:
        _validate_file(thumbnail_file, ALLOWED_IMAGE_TYPES, MAX_IMAGE_SIZE, "Thumbnail")

    video_id = str(uuid.uuid4())

    # -- Upload video to R2 --
    video_key = _make_video_key(user.id, video_id, video_file.content_type)
    r2.upload_file(video_file.file, video_key, video_file.content_type)

    # -- Upload thumbnail to R2 (optional) --
    thumbnail_key: str | None = None
    if thumbnail_file and thumbnail_file.filename:
        thumbnail_key = _make_thumbnail_key(user.id, video_id, thumbnail_file.content_type)
        r2.upload_file(thumbnail_file.file, thumbnail_key, thumbnail_file.content_type)

    # -- Save to DB --
    video = Video(
        id=video_id,
        user_id=user.id,
        title=title.strip(),
        description=description.strip() if description else None,
        video_key=video_key,
        thumbnail_key=thumbnail_key,
        status=VideoStatus.ready,
    )
    db.add(video)
    db.commit()
    db.refresh(video)

    # Re-query to get the author relationship populated
    return get_by_id_internal(db, video_id)


def get_by_id_internal(db: Session, video_id: str) -> VideoOut:
    """Fetches a video with its author, raises 404 if not found."""
    video = (
        db.query(Video)
        .options(joinedload(Video.author))
        .filter(Video.id == video_id)
        .first()
    )
    if not video:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Video not found.")
    return _to_out(video)


def get_by_id(db: Session, video_id: str) -> VideoOut:
    """
    Returns video metadata AND increments the view count.
    Called by the watch page on load.
    """
    video = (
        db.query(Video)
        .options(joinedload(Video.author))
        .filter(Video.id == video_id)
        .first()
    )
    if not video:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Video not found.")

    # Increment view count atomically
    db.query(Video).filter(Video.id == video_id).update(
        {Video.view_count: Video.view_count + 1}
    )
    db.commit()
    db.refresh(video)
    return _to_out(video)


def get_stream_url(db: Session, video_id: str) -> str:
    """Returns a presigned R2 URL for video playback (1 hour expiry)."""
    video = db.get(Video, video_id)
    if not video:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Video not found.")
    return r2.get_presigned_url(video.video_key, expires_in=3600)


def list_videos(db: Session, page: int, limit: int):
    """Returns paginated list of all ready videos, newest first."""
    offset = (page - 1) * limit
    query = (
        db.query(Video)
        .options(joinedload(Video.author))
        .filter(Video.status == VideoStatus.ready)
        .order_by(Video.created_at.desc())
    )
    total = query.count()
    videos = query.offset(offset).limit(limit).all()
    return total, [_to_out(v) for v in videos]


def search_videos(db: Session, q: str, page: int, limit: int):
    """
    Searches videos by title using a case-insensitive ILIKE query.
    Returns paginated results ordered by newest first.
    """
    if not q.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Search query cannot be empty.",
        )
    offset = (page - 1) * limit
    pattern = f"%{q.strip()}%"
    query = (
        db.query(Video)
        .options(joinedload(Video.author))
        .filter(
            Video.status == VideoStatus.ready,
            Video.title.ilike(pattern),
        )
        .order_by(Video.created_at.desc())
    )
    total = query.count()
    videos = query.offset(offset).limit(limit).all()
    return total, [_to_out(v) for v in videos]


def update(db: Session, video_id: str, user: User, data: VideoUpdate) -> VideoOut:
    """
    Updates title and/or description.
    Only the video owner may update.
    """
    video = db.get(Video, video_id)
    if not video:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Video not found.")
    if video.user_id != user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not own this video.",
        )
    if data.title is not None:
        video.title = data.title.strip()
    if data.description is not None:
        video.description = data.description.strip() or None
    db.commit()
    return get_by_id_internal(db, video_id)


def delete(db: Session, video_id: str, user: User) -> None:
    """
    Deletes the video from R2 (video + thumbnail) and from the database.
    All related comments and likes are removed via CASCADE.
    Only the video owner may delete.
    """
    video = db.get(Video, video_id)
    if not video:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Video not found.")
    if video.user_id != user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not own this video.",
        )
    # Delete from R2 (silent if already gone)
    r2.delete_file(video.video_key)
    if video.thumbnail_key:
        r2.delete_file(video.thumbnail_key)

    db.delete(video)
    db.commit()
