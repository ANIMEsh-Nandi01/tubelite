from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings

settings = get_settings()

# Register all SQLAlchemy models so relationship() strings resolve correctly.
# This must run before the first DB query — importing here guarantees that.
import app  # noqa: F401, E402

# ---------------------------------------------------------------------------
# App factory
# ---------------------------------------------------------------------------
app = FastAPI(
    title="TubeLite API",
    version="1.0.0",
    description="Backend API for TubeLite — a full-stack YouTube clone.",
    docs_url="/docs",       # Swagger UI
    redoc_url="/redoc",     # ReDoc
    openapi_url="/openapi.json",
)

# ---------------------------------------------------------------------------
# CORS middleware
# Must be registered BEFORE any routers.
# allow_credentials=True is required for httpOnly cookie auth.
# ---------------------------------------------------------------------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins_list,
    allow_credentials=True,   # Required: allows cookies to be sent cross-origin
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------------------------------------------------------------
# Routers
# Uncommented one phase at a time as each module is built.
# ---------------------------------------------------------------------------
from app.auth.router import router as auth_router    # Phase 3 ✅
from app.videos.router import router as videos_router  # Phase 4 ✅
# from app.users.router import router as users_router     # Phase 5
# from app.comments.router import router as comments_router  # Phase 6
# from app.likes.router import router as likes_router        # Phase 6

app.include_router(auth_router,   prefix="/api/auth",   tags=["Auth"])
app.include_router(videos_router, prefix="/api/videos", tags=["Videos"])
# app.include_router(users_router,    prefix="/api/users",  tags=["Users"])
# app.include_router(comments_router, prefix="/api",        tags=["Comments"])
# app.include_router(likes_router,    prefix="/api/videos", tags=["Likes"])


# ---------------------------------------------------------------------------
# Health check
# ---------------------------------------------------------------------------
@app.get("/health", tags=["Health"])
def health_check():
    """
    Returns a 200 OK with a simple status payload.
    Used by deployment platforms (Railway, Docker health checks) to verify
    the service is alive.
    """
    return {"status": "ok", "version": "1.0.0"}
