from fastapi import FastAPI

from app.api.routes import auth

app = FastAPI(
    title="Adal Jumys API",
    description="Қазақстан еңбек нарығының ашықтық платформасы — ашық API",
    version="0.1.0",
)

app.include_router(auth.router)


@app.get("/health", tags=["service"])
async def health() -> dict[str, str]:
    """Қызметтің тірі екенін тексеру нүктесі (деплой/мониторинг үшін)."""
    return {"status": "ok"}
