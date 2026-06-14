from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    DATABASE_URL: str
    JWT_SECRET: str
    JWT_ALGORITHM: str = "HS256"
    BOT_TOKEN: str
    FRONTEND_URL: str
    SENTRY_DSN: str = ""
    # Comma-separated extra hosts to allow (e.g. Railway backend domain)
    EXTRA_ALLOWED_HOSTS: str = ""

    @property
    def ALLOWED_ORIGINS(self) -> list[str]:
        return [self.FRONTEND_URL]

    @property
    def ALLOWED_HOSTS(self) -> list[str]:
        host = self.FRONTEND_URL.removeprefix("https://").removeprefix("http://")
        hosts = [host, f"*.{host}", "localhost", "127.0.0.1"]
        if self.EXTRA_ALLOWED_HOSTS:
            hosts += [h.strip() for h in self.EXTRA_ALLOWED_HOSTS.split(",") if h.strip()]
        return hosts


settings = Settings()
