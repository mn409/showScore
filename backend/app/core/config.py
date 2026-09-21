from functools import lru_cache
from typing import List

from pydantic_settings import BaseSettings, SettingsConfigDict
from dotenv import load_dotenv
from pathlib import Path

env_path = Path(__file__).resolve().parents[2] / ".env"
load_dotenv(dotenv_path=env_path)

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # Database
    DATABASE_URL: str = "postgresql+asyncpg://showscore:showscore@127.0.0.1:5432/showscore"
    SYNC_DATABASE_URL: str = "postgresql+psycopg2://showscore:showscore@127.0.0.1:5432/showscore"

    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"

    # JWT
    JWT_SECRET_KEY: str = "insecure-dev-secret-change-me"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 15
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # App
    ENVIRONMENT: str = "development"
    CORS_ORIGINS: str = "http://localhost:3000"
    COOKIE_SECURE: bool = False
    COOKIE_DOMAIN: str = "localhost"

    # Score rules: higher_only | always_overwrite | sum
    SCORE_UPDATE_RULE: str = "higher_only"

    # Rate limiting
    SCORE_SUBMIT_RATE_LIMIT: str = "10/minute"

    # Admin bootstrap
    FIRST_ADMIN_EMAIL: str = "admin@showscore.dev"
    FIRST_ADMIN_PASSWORD: str = "ChangeMe123!"

    @property
    def cors_origins_list(self) -> List[str]:
        return [o.strip() for o in self.CORS_ORIGINS.split(",") if o.strip()]

    @property
    def is_production(self) -> bool:
        return self.ENVIRONMENT.lower() == "production"


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
