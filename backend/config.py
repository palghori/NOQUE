from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    # Database — Render provides postgres:// but SQLAlchemy needs postgresql+asyncpg://
    DATABASE_URL: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/codeoracle"

    @property
    def async_database_url(self) -> str:
        """Convert postgres:// to postgresql+asyncpg:// for SQLAlchemy async."""
        url = self.DATABASE_URL
        if url.startswith("postgres://"):
            url = url.replace("postgres://", "postgresql+asyncpg://", 1)
        elif url.startswith("postgresql://"):
            url = url.replace("postgresql://", "postgresql+asyncpg://", 1)
        return url

    # Google Gemini
    GEMINI_API_KEY: str = ""
    GEMINI_MODEL: str = "gemini-2.5-pro"

    # Processing
    MAX_FILE_SIZE_MB: int = 25
    COVERAGE_THRESHOLD: int = 60
    MAX_TEST_RETRIES: int = 3
    TEMP_DIR: str = "/tmp/codeoracle"

    # Supported extensions
    SUPPORTED_EXTENSIONS: list[str] = [".py", ".js"]

    class Config:
        env_file = ".env"


@lru_cache()
def get_settings() -> Settings:
    return Settings()
