from fastapi import HTTPException, status
from sqlalchemy.orm import Session, joinedload

from app.comments.models import Comment
from app.comments.schemas import CommentCreate, CommentOut, PaginatedComments
from app.users.models import User
from app.videos.models import Video


def _to_out(comment: Comment) -> CommentOut:
    return CommentOut.model_validate(comment)


def create(
    db: Session,
    video_id: str,
    user: User,
    data: CommentCreate,
) -> CommentOut:
    """
    Creates a comment on a video.
    Raises 404 if the video does not exist.
    """
    video = db.get(Video, video_id)
    if not video:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Video not found.",
        )
    comment = Comment(
        video_id=video_id,
        user_id=user.id,
        content=data.content,
    )
    db.add(comment)
    db.commit()
    db.refresh(comment)

    # Re-fetch with author relationship loaded
    return get_single(db, comment.id)


def get_single(db: Session, comment_id: str) -> CommentOut:
    """Fetches a single comment with its author, raises 404 if not found."""
    comment = (
        db.query(Comment)
        .options(joinedload(Comment.author))
        .filter(Comment.id == comment_id)
        .first()
    )
    if not comment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Comment not found.",
        )
    return _to_out(comment)


def list_comments(
    db: Session,
    video_id: str,
    page: int,
    limit: int,
) -> PaginatedComments:
    """
    Returns paginated comments for a video, ordered oldest-first
    (chronological order makes sense for discussions).
    Raises 404 if the video does not exist.
    """
    video = db.get(Video, video_id)
    if not video:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Video not found.",
        )
    offset = (page - 1) * limit
    query = (
        db.query(Comment)
        .options(joinedload(Comment.author))
        .filter(Comment.video_id == video_id)
        .order_by(Comment.created_at.asc())
    )
    total = query.count()
    comments = query.offset(offset).limit(limit).all()
    return PaginatedComments(
        total=total,
        page=page,
        limit=limit,
        items=[_to_out(c) for c in comments],
    )


def delete(db: Session, comment_id: str, user: User) -> None:
    """
    Deletes a comment.
    Only the comment author may delete. Returns 403 otherwise.
    """
    comment = db.get(Comment, comment_id)
    if not comment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Comment not found.",
        )
    if comment.user_id != user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only delete your own comments.",
        )
    db.delete(comment)
    db.commit()
