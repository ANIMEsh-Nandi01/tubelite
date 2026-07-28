from fastapi import APIRouter, Depends, Response, status

from app.auth import service
from app.auth.schemas import LoginRequest, MessageResponse, SignupRequest
from app.config import get_settings
from app.dependencies import CurrentUser, DbSession
from app.users.schemas import UserPublic

router = APIRouter()

settings = get_settings()

# ---------------------------------------------------------------------------
# Cookie configuration
# ---------------------------------------------------------------------------
_COOKIE_NAME = "access_token"
_COOKIE_MAX_AGE = settings.jwt_expire_minutes * 60  # seconds


def _set_auth_cookie(response: Response, token: str) -> None:
    """
    Writes the JWT into an httpOnly cookie on the response.

    httponly=True  — JavaScript cannot read this cookie (XSS protection).
    samesite="lax" — Sent on same-site requests + top-level cross-site navigations.
                     Prevents most CSRF attacks without breaking normal browser use.
    secure=False   — Must be True in production (HTTPS only). Set via env in Phase 7.
    """
    response.set_cookie(
        key=_COOKIE_NAME,
        value=token,
        httponly=True,
        samesite="lax",
        secure=False,  # TODO: set to True in production
        max_age=_COOKIE_MAX_AGE,
        path="/",
    )


def _clear_auth_cookie(response: Response) -> None:
    """Clears the auth cookie by setting it with max_age=0."""
    response.delete_cookie(key=_COOKIE_NAME, path="/", samesite="lax")


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------


@router.post(
    "/signup",
    response_model=UserPublic,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new account",
)
def signup(
    data: SignupRequest,
    response: Response,
    db: DbSession,
) -> UserPublic:
    """
    Registers a new user.

    - Validates username (alphanumeric, 3–50 chars) and password (min 8 chars).
    - Returns 409 if the email or username is already taken.
    - On success: sets an httpOnly auth cookie and returns the new user's public profile.
    """
    from app.auth.utils import create_jwt

    user = service.signup(db, data)
    token = create_jwt(user.id)
    _set_auth_cookie(response, token)
    return user


@router.post(
    "/login",
    response_model=UserPublic,
    status_code=status.HTTP_200_OK,
    summary="Login with email and password",
)
def login(
    data: LoginRequest,
    response: Response,
    db: DbSession,
) -> UserPublic:
    """
    Authenticates a user by email and password.

    - Returns 401 if credentials are invalid (same message for both bad email and bad password).
    - On success: sets an httpOnly auth cookie and returns the user's public profile.
    """
    from app.auth.utils import create_jwt

    user = service.login(db, data)
    token = create_jwt(user.id)
    _set_auth_cookie(response, token)
    return user


@router.post(
    "/logout",
    response_model=MessageResponse,
    status_code=status.HTTP_200_OK,
    summary="Logout (clear auth cookie)",
)
def logout(response: Response) -> MessageResponse:
    """
    Logs out the current user by deleting the auth cookie.

    This endpoint does not require authentication — if there's no cookie,
    clearing it is a no-op, which is the correct behavior.
    """
    _clear_auth_cookie(response)
    return MessageResponse(message="Logged out successfully.")


@router.get(
    "/me",
    response_model=UserPublic,
    status_code=status.HTTP_200_OK,
    summary="Get the currently authenticated user",
)
def get_me(current_user: CurrentUser) -> UserPublic:
    """
    Returns the profile of the currently logged-in user.

    - Requires a valid auth cookie.
    - Returns 401 if the cookie is missing or the JWT is invalid/expired.
    """
    return current_user
