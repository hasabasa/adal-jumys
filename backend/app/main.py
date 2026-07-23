from fastapi import FastAPI
from fastapi.responses import RedirectResponse

from app.api.routes import auth, companies, complaints, evidence, moderation, reviews

app = FastAPI(
    title="Adal Jumys API",
    description="Қазақстан еңбек нарығының ашықтық платформасы — ашық API",
    version="0.1.0",
)

app.include_router(auth.router)
app.include_router(companies.router)
app.include_router(reviews.router)
app.include_router(complaints.router)
app.include_router(moderation.router)
app.include_router(evidence.router)


@app.get("/", include_in_schema=False)
async def root() -> RedirectResponse:
    return RedirectResponse(url="/docs")


@app.get("/health", tags=["service"])
async def health() -> dict[str, str]:
    """Қызметтің тірі екенін тексеру нүктесі (деплой/мониторинг үшін)."""
    return {"status": "ok"}
