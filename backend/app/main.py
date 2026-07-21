from fastapi import FastAPI

app = FastAPI(
    title="Adal Jumys API",
    description="Қазақстан еңбек нарығының ашықтық платформасы — ашық API",
    version="0.1.0",
)


@app.get("/health", tags=["service"])
async def health() -> dict[str, str]:
    """Қызметтің тірі екенін тексеру нүктесі (деплой/мониторинг үшін)."""
    return {"status": "ok"}
