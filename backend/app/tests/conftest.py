import os

# Set required env vars before any app module is imported.
# These are test-only values — never used in production.
os.environ.setdefault("DATABASE_URL", "postgresql+asyncpg://postgres:test@localhost/budget_test")
os.environ.setdefault("JWT_SECRET", "test-secret-do-not-use-in-prod-aaaaaaaaaaaaaaaaaaaaaaaaaaaa")
os.environ.setdefault("JWT_ALGORITHM", "HS256")
os.environ.setdefault("BOT_TOKEN", "test-bot-token")
os.environ.setdefault("FRONTEND_URL", "http://localhost:5173")
