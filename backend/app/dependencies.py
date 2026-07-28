from collections.abc import Generator
from typing import Annotated

from fastapi import Depends, HTTPException, status, Cookie
from sqlalchemy.orm import Session

from app.database import SessionLocal
from app.auth.utils import decode_jwt


# ---------------------------------------------------------------------------
# Database dependency
# ---------------------------------------------------------------------------
def get_db() -> Generator[Session, None, None]:
    """
    Yields a SQLAlchemy session and guarantees it is closed after the request,
    whether the request succeeds or raises an exception.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


DbSession = Annotated[Session, Depends(get_db)]


# ---------------------------------------------------------------------------
# Authentication dependency
# ---------------------------------------------------------------------------
def get_current_user(
    db: DbSession,
    access_token: str | None = Cookie(default=None),
):
    """
    Reads the JWT from the httpOnly cookie, decodes it, and returns the User.
    Raises HTTP 401 if the token is missing, expired, or invalid.
    """
    # Import here to avoid circular imports (users.models imports database)
    from app.users.models import User

    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Not authenticated",
    )

    if access_token is None:
        raise credentials_exception

    payload = decode_jwt(access_token)
    if payload is None:
        raise credentials_exception

    user_id: str | None = payload.get("sub")
    if user_id is None:
        raise credentials_exception

    user = db.get(User, user_id)
    if user is None:
        raise credentials_exception

    return user


CurrentUser = Annotated[object, Depends(get_current_user)]
