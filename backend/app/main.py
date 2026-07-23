from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse

from app.api.routes import (
    auth,
    comments,
    companies,
    complaints,
    evidence,
    feed,
    moderation,
    reports,
    reviews,
    votes,
)
from app.core.config import get_settings

app = FastAPI(
    title="Adal Jumys API",
    description="Қазақстан еңбек нарығының ашықтық платформасы — ашық API",
    version="0.1.0",
)

# Таза ASGI middleware (BaseHTTPMiddleware ЕМЕС - ол CORS-ты жұтады)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[o.strip() for o in get_settings().cors_origins.split(",")],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(companies.router)
app.include_router(reviews.router)
app.include_router(complaints.router)
app.include_router(moderation.router)
app.include_router(evidence.router)
app.include_router(feed.router)
app.include_router(comments.router)
app.include_router(votes.router)
app.include_router(reports.router)


@app.get("/", include_in_schema=False)
async def root() -> RedirectResponse:
    return RedirectResponse(url="/docs")


@app.get("/health", tags=["service"])
async def health() -> dict[str, str]:
    """Қызметтің тірі екенін тексеру нүктесі (деплой/мониторинг үшін)."""
    return {"status": "ok"}
