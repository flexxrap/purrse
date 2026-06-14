from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    DATABASE_URL: str
    JWT_SECRET: str
    JWT_ALGORITHM: str = "HS256"
    BOT_TOKEN: str
    FRONTEND_URL: str
    SENTRY_DSN: str = ""

    # Derived from FRONTEND_URL; override via env if needed
    @property
    def ALLOWED_ORIGINS(self) -> list[str]:
        return [self.FRONTEND_URL]

    @property
    def ALLOWED_HOSTS(self) -> list[str]:
        host = self.FRONTEND_URL.removeprefix("https://").removeprefix("http://")
        return [host, f"*.{host}", "localhost", "127.0.0.1"]


settings = Settings()
