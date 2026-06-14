from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    DATABASE_URL: str
    JWT_SECRET: str
    JWT_ALGORITHM: str = "HS256"
    BOT_TOKEN: str
    FRONTEND_URL: str
    EXTRA_ORIGINS: str = ""  # comma-separated extra allowed origins (e.g. localhost for dev)
    SENTRY_DSN: str = ""
    BACKEND_URL: str = ""  # e.g. https://api.example.railway.app — for webhook auto-registration

    @property
    def ALLOWED_ORIGINS(self) -> list[str]:
        origins = [self.FRONTEND_URL]
        if self.EXTRA_ORIGINS:
            origins.extend(o.strip() for o in self.EXTRA_ORIGINS.split(",") if o.strip())
        return origins


settings = Settings()
