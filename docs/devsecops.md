# DevSecOps Rules & Security Reference

> Claude Code: read this when implementing anything related to auth, middleware, CI, or deploy.
> These are non-negotiable. Raise a flag if any story asks you to violate them.

---

## Security layers — what exists and where

### Layer 1: Code (SAST)
- **Tool**: Bandit (`bandit -r app -ll`)
- **Run**: every PR in CI; also run locally before commit
- **Blocks**: HIGH severity issues block merge
- **Common findings to avoid**:
  - `B106` hardcoded password
  - `B608` SQL injection via string formatting
  - `B501/B502` weak SSL
  - `B105` hardcoded password string

### Layer 2: Dependencies
- **Tool**: Dependabot (`.github/dependabot.yml`)
- **Schedule**: weekly PRs for pip + npm
- **Rule**: never ignore CRITICAL CVE PRs

### Layer 3: Container
- **Tool**: Trivy (`trivy image budget-app:latest`)
- **Run**: every CI build
- **Blocks**: CRITICAL severity CVEs block merge
- **Dockerfile rules**:
  ```dockerfile
  # Always: non-root user
  RUN adduser --disabled-password --gecos "" appuser
  USER appuser

  # Always: multi-stage to keep image small
  FROM python:3.12-slim AS builder
  # ... install deps
  FROM python:3.12-slim AS runtime
  # ... copy only what's needed
  ```

### Layer 4: Network
- **TLS**: Railway provides automatic TLS — never expose HTTP in prod
- **HSTS**: `Strict-Transport-Security: max-age=31536000; includeSubDomains`
- **CORS**: whitelist only — never `allow_origins=["*"]` in production

### Layer 5: Application — FastAPI middleware stack

Implement in this order in `app/main.py`:

```python
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from slowapi import Limiter
from slowapi.util import get_remote_address

# 1. Trusted hosts (prevents host header injection)
app.add_middleware(TrustedHostMiddleware, allowed_hosts=settings.ALLOWED_HOSTS)

# 2. CORS (whitelist only)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,  # from env var, not hardcoded
    allow_credentials=True,
    allow_methods=["GET", "POST", "PATCH", "DELETE"],
    allow_headers=["Authorization", "Content-Type"],
)

# 3. Security headers (custom middleware)
@app.middleware("http")
async def security_headers(request, call_next):
    response = await call_next(request)
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    response.headers["Content-Security-Policy"] = (
        "default-src 'self'; "
        "script-src 'self' https://telegram.org; "
        "style-src 'self' 'unsafe-inline'; "
        "img-src 'self' data: https:; "
        "connect-src 'self'"
    )
    return response
```

### Layer 6: Rate limiting

```python
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter

# On auth routes (register, login, telegram)
@router.post("/login")
@limiter.limit("60/minute")
async def login(request: Request, ...):
    ...

# On data routes (default)
@router.get("/transactions")
@limiter.limit("300/minute")
async def list_transactions(request: Request, ...):
    ...
```

### Layer 7: Database
- App DB user: `SELECT, INSERT, UPDATE, DELETE` only — no `CREATE`, `DROP`, `ALTER`
- Connection string must include `?sslmode=require`
- Connection pool: `pool_size=10, max_overflow=20, pool_timeout=30`
- Never log full SQL queries in production (contains user data)

### Layer 8: Monitoring & Audit
- Sentry: all 5xx errors + transactions > 2s
- Audit log table: record every auth event (login, logout, failed_login, telegram_login)
- Audit log retention: 90 days (cron DELETE)

---

## Auth implementation reference

### JWT tokens

```python
from jose import JWTError, jwt
from datetime import datetime, timedelta, timezone

SECRET_KEY = settings.JWT_SECRET  # from env
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 15
REFRESH_TOKEN_EXPIRE_DAYS = 30

def create_access_token(user_id: str) -> str:
    expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    return jwt.encode({"sub": user_id, "exp": expire}, SECRET_KEY, algorithm=ALGORITHM)

async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db)
) -> User:
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = payload.get("sub")
        if not user_id:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    user = await db.get(User, user_id)
    if not user:
        raise credentials_exception
    return user
```

### Refresh token rotation

```python
import hashlib, secrets

def generate_refresh_token() -> tuple[str, str]:
    """Returns (raw_token, hash_to_store)"""
    raw = secrets.token_hex(64)
    hashed = hashlib.sha256(raw.encode()).hexdigest()
    return raw, hashed

def set_refresh_cookie(response: Response, raw_token: str):
    response.set_cookie(
        key="refresh_token",
        value=raw_token,
        httponly=True,
        secure=True,          # HTTPS only
        samesite="strict",
        max_age=60 * 60 * 24 * 30,  # 30 days
        path="/auth/refresh"  # cookie only sent to this path
    )
```

### Telegram initData verification

```python
import hashlib, hmac, time
from urllib.parse import parse_qs, unquote

def verify_telegram_init_data(init_data: str, bot_token: str) -> dict:
    parsed = dict(parse_qs(init_data, keep_blank_values=True))
    received_hash = parsed.pop("hash", [None])[0]
    if not received_hash:
        raise ValueError("No hash in initData")

    # Check timestamp
    auth_date = int(parsed.get("auth_date", [0])[0])
    if time.time() - auth_date > 86400:
        raise ValueError("initData expired")

    # Verify HMAC
    data_check_string = "\n".join(
        f"{k}={unquote(v[0])}"
        for k, v in sorted(parsed.items())
    )
    secret_key = hmac.new(b"WebAppData", bot_token.encode(), hashlib.sha256).digest()
    expected = hmac.new(secret_key, data_check_string.encode(), hashlib.sha256).hexdigest()

    if not hmac.compare_digest(expected, received_hash):
        raise ValueError("Invalid hash")

    import json
    user_data = json.loads(unquote(parsed["user"][0]))
    return user_data  # { id, first_name, username, ... }
```

### Password hashing

```python
from passlib.context import CryptContext
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto", bcrypt__rounds=12)

def hash_password(plain: str) -> str:
    return pwd_context.hash(plain)

def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)
```

---

## CI/CD pipeline — full `.github/workflows/ci.yml`

```yaml
name: CI

on:
  push:
    branches: [main, dev]
  pull_request:
    branches: [main]

jobs:
  backend:
    runs-on: ubuntu-latest
    services:
      postgres:
        image: postgres:16
        env:
          POSTGRES_PASSWORD: test
          POSTGRES_DB: budget_test
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
        ports:
          - 5432:5432
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with: { python-version: "3.12" }
      - run: pip install -r backend/requirements.txt -r backend/requirements-dev.txt
      - run: cd backend && ruff check app/
      - run: cd backend && bandit -r app/ -ll -x app/tests/
      - run: cd backend && pytest --cov=app --cov-report=xml --cov-fail-under=70
        env:
          DATABASE_URL: postgresql+asyncpg://postgres:test@localhost/budget_test
          JWT_SECRET: test-secret-do-not-use-in-prod
          BOT_TOKEN: test-bot-token

  frontend:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with: { node-version: "20" }
      - run: cd frontend && npm ci
      - run: cd frontend && npx eslint src/
      - run: cd frontend && npm run build

  docker:
    runs-on: ubuntu-latest
    needs: [backend, frontend]
    steps:
      - uses: actions/checkout@v4
      - run: docker build -t budget-app:ci ./backend
      - uses: aquasecurity/trivy-action@master
        with:
          image-ref: budget-app:ci
          exit-code: "1"
          severity: CRITICAL

  deploy:
    runs-on: ubuntu-latest
    needs: [docker]
    if: github.ref == 'refs/heads/main' && github.event_name == 'push'
    steps:
      - uses: actions/checkout@v4
      - uses: railwayapp/railway-cli-action@v1
        with:
          railway_token: ${{ secrets.RAILWAY_TOKEN }}
          command: up --detach
```

---

## Dockerfile — multi-stage

```dockerfile
FROM python:3.12-slim AS builder
WORKDIR /build
COPY requirements.txt .
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt

FROM python:3.12-slim AS runtime
WORKDIR /app

# Security: non-root user
RUN adduser --disabled-password --gecos "" appuser

# Copy installed deps from builder
COPY --from=builder /install /usr/local

# Copy app code
COPY app/ ./app/
COPY alembic/ ./alembic/
COPY alembic.ini .

# Security: non-root
USER appuser

EXPOSE 8000

# Run migrations then start (for Railway, migrations via separate command or start script)
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

---

## OWASP Top 10 checklist for this project

Run through this before public launch (story S-13).

| # | Risk | Our control | Verified? |
|---|------|-------------|-----------|
| A01 | Broken Access Control | All queries filter by user_id from JWT | `[x]` |
| A02 | Cryptographic Failures | bcrypt for passwords; HTTPS; httpOnly cookies | `[x]` |
| A03 | Injection | SQLAlchemy ORM; Pydantic validation; no raw SQL | `[x]` |
| A04 | Insecure Design | Cursor pagination; soft delete; rate limiting | `[x]` |
| A05 | Security Misconfiguration | Security headers middleware; CORS whitelist | `[x]` |
| A06 | Vulnerable Components | Dependabot + Trivy | `[x]` |
| A07 | Auth Failures | JWT rotation; rate limit on auth; audit log | `[x]` |
| A08 | Data Integrity | Pydantic on all inputs; Telegram HMAC verify | `[x]` |
| A09 | Logging Failures | Sentry + audit_log table + structured logging | `[x]` |
| A10 | SSRF | No outbound HTTP from user input; whitelist external calls | `[x]` |
