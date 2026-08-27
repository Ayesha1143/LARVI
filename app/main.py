from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse

from app.api.auth import router as auth_router
from app.api.chat import router as chat_router
from app.config.settings import settings


BASE_DIR = Path(__file__).resolve().parent.parent
FRONTEND_DIR = BASE_DIR / "frontend"


app = FastAPI(
    title="Larvi — AI Email & Calendar Assistant",
    description=(
        "Autonomous AI agent for managing Gmail "
        "and Google Calendar using natural-language instructions."
    ),
    version="1.0.0",
    debug=settings.debug,
)


# ==========================================
# CORS
# ==========================================

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        settings.frontend_url,
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ==========================================
# API ROUTERS
# ==========================================

app.include_router(
    auth_router,
)

app.include_router(
    chat_router,
)


# ==========================================
# HEALTH CHECK
# ==========================================

@app.get(
    "/health",
    tags=["System"],
)
async def health_check():
    """
    Check whether Larvi backend is running.
    """

    return {
        "status": "healthy",
        "application": "Larvi",
        "environment": settings.app_env,
    }


# ==========================================
# FRONTEND
# ==========================================

@app.get(
    "/",
    include_in_schema=False,
)
async def serve_frontend():
    """
    Serve Larvi frontend.
    """

    index_file = FRONTEND_DIR / "index.html"

    if not index_file.exists():
        return {
            "message": "Larvi API is running.",
            "docs": "/docs",
        }

    return FileResponse(
        index_file
    )


@app.get(
    "/css/{file_name}",
    include_in_schema=False,
)
async def serve_css(
    file_name: str,
):
    """
    Serve frontend CSS files.
    """

    css_file = (
        FRONTEND_DIR
        / "css"
        / file_name
    )

    if not css_file.exists():
        return {
            "error": "CSS file not found."
        }

    return FileResponse(
        css_file,
        media_type="text/css",
    )


@app.get(
    "/js/{file_name}",
    include_in_schema=False,
)
async def serve_javascript(
    file_name: str,
):
    """
    Serve frontend JavaScript files.
    """

    js_file = (
        FRONTEND_DIR
        / "js"
        / file_name
    )

    if not js_file.exists():
        return {
            "error": "JavaScript file not found."
        }

    return FileResponse(
        js_file,
        media_type="application/javascript",
    )