from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.auth.schemas import SignupRequest, LoginRequest
from app.auth.utils import hash_password, verify_password
from app.users.models import User


def signup(db: Session, data: SignupRequest) -> User:
    """
    Creates a new user account.

    Raises:
        409 Conflict — if the email or username is already taken.
    """
    # Check for duplicate email
    if db.query(User).filter(User.email == data.email).first():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="An account with this email already exists.",
        )

    # Check for duplicate username
    if db.query(User).filter(User.username == data.username).first():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="This username is already taken.",
        )

    user = User(
        username=data.username,
        email=data.email,
        password_hash=hash_password(data.password),
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def login(db: Session, data: LoginRequest) -> User:
    """
    Verifies credentials and returns the User on success.

    Always raises the same 401 error whether the email doesn't exist
    or the password is wrong — prevents email enumeration attacks.

    Raises:
        401 Unauthorized — if credentials are invalid.
    """
    _invalid = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid email or password.",
    )

    user = db.query(User).filter(User.email == data.email).first()
    if not user:
        raise _invalid

    if not verify_password(data.password, user.password_hash):
        raise _invalid

    return user
