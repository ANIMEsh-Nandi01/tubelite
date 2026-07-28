# This file ensures all SQLAlchemy models are imported and registered
# with the shared metadata/mapper registry before any query runs.
# Without this, relationship() string references fail to resolve.

from app.users.models import User  # noqa: F401
from app.videos.models import Video  # noqa: F401
from app.comments.models import Comment  # noqa: F401
from app.likes.models import Like  # noqa: F401
