from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Қосымшаның барлық баптауы — .env файлынан немесе орта айнымалыларынан.

    Міндетті айнымалы жетіспесе, қосымша іске қосылмай қате береді —
    бұл әдейі: жартылай конфигпен жұмыс істегеннен гөрі бірден құлаған дұрыс.
    """

    model_config = SettingsConfigDict(
        # Алдымен backend/.env, таппаса репо түбіріндегі .env
        env_file=(".env", "../.env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    environment: str = "development"

    database_url: str
    redis_url: str = "redis://localhost:6379/0"

    secret_key: str
    access_token_expire_minutes: int = 30

    s3_endpoint_url: str = ""
    s3_region: str = "auto"
    s3_bucket: str = ""
    s3_access_key_id: str = ""
    s3_secret_access_key: str = ""

    # local: dev/тест (дискіге жазады); s3: прод (жоғарыдағы S3-конфиг керек)
    storage_backend: str = "local"
    upload_dir: str = "var/uploads"
    max_upload_mb: int = 10

    # Компания-реестр API (бос болса lookup өшірулі, каталог қолмен толады)
    registry_api_url: str = ""
    registry_api_key: str = ""


@lru_cache
def get_settings() -> Settings:
    return Settings()
