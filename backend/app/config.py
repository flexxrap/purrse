from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    DATABASE_URL: str
    JWT_SECRET: str
    JWT_ALGORITHM: str = "HS256"
    BOT_TOKEN: str
    FRONTEND_URL: str
    SENTRY_DSN: str = ""

    @property
    def ALLOWED_ORIGINS(self) -> list[str]:
        return [self.FRONTEND_URL]


settings = Settings()
