# Budget App — Claude Code Master Instructions

> This file is read automatically at the start of every Claude Code session.
> Follow ALL rules here without exception. When in doubt, ask before writing code.

---

## 1. Project overview

Personal finance platform with multi-user support.
- Web SPA (React 18 + Vite) + Telegram Mini App (same codebase)
- REST API backend (FastAPI, Python 3.12)
- PostgreSQL 16 database (Railway managed)
- Deployed on Railway, CI/CD via GitHub Actions

Full documentation: see `/docs/` folder.

---

## 2. Current phase & active work

**→ Read `/docs/backlog.md` to see what is IN PROGRESS and TODO.**

Before starting any task:
1. Check backlog.md for the story ID and acceptance criteria
2. Check if the story has dependencies (see `/docs/dependencies.md`)
3. Ask me if anything is unclear before writing code

---

## 3. Folder structure — strict, do not deviate

```
budget-app/
├── CLAUDE.md                  ← you are here
├── docs/
│   ├── backlog.md             ← story status (update after each story)
│   ├── schema.md              ← database schema reference
│   ├── api-spec.md            ← all API endpoints
│   ├── devsecops.md           ← security rules
│   ├── dependencies.md        ← story dependencies
│   └── done-criteria.md       ← definition of done
├── backend/
│   ├── app/
│   │   ├── main.py            ← FastAPI app factory
│   │   ├── config.py          ← settings via pydantic-settings
│   │   ├── database.py        ← async engine + session factory
│   │   ├── dependencies.py    ← get_current_user, get_db
│   │   ├── models/            ← SQLAlchemy ORM models (one file per table)
│   │   ├── routers/           ← FastAPI routers (one file per domain)
│   │   ├── schemas/           ← Pydantic v2 request/response schemas
│   │   ├── services/          ← business logic (routers call services, not DB directly)
│   │   ├── middleware/        ← security headers, rate limiting
│   │   └── tests/             ← pytest tests (mirror app/ structure)
│   ├── alembic/               ← DB migrations
│   ├── requirements.txt
│   ├── requirements-dev.txt
│   └── Dockerfile
├── frontend/
│   └── src/
│       ├── api/               ← axios functions (one file per domain)
│       ├── pages/             ← route-level components
│       ├── components/        ← reusable UI components
│       ├── store/             ← Zustand stores
│       └── hooks/             ← custom React hooks
└── .github/
    └── workflows/
        └── ci.yml
```

---

## 4. Architecture rules — NEVER violate

### Money
- ALL monetary values stored as INTEGER cents (`amount_cents`)
- Example: 10.50 BYN = 1050 (integer)
- NEVER use float or Decimal for money storage
- Display formatting (÷ 100) happens only in the frontend

### Security — access control
- EVERY database query that returns user data MUST filter by `current_user.id`
- NEVER trust `user_id` from the request body — always take from JWT
- Pattern: `db.query(Transaction).filter(Transaction.user_id == current_user.id)`
- Violation of this rule = broken access control (OWASP A01) — critical severity

### Security — authentication
- JWT access token: signed HS256, expires in 15 minutes
- Refresh token: stored as SHA-256 hash in DB, delivered in `httpOnly; Secure; SameSite=Strict` cookie
- Access token stored in FRONTEND MEMORY ONLY — never localStorage, never sessionStorage
- Telegram `initData`: verify HMAC-SHA256 with `BOT_TOKEN`; reject if `auth_date` is older than 86400 seconds

### Database
- NEVER write raw SQL strings — use SQLAlchemy ORM exclusively
- NEVER use `text()` with user input — use bound parameters
- All models use UUID primary keys (`gen_random_uuid()`)
- Soft delete: set `deleted_at = now()`, never `DELETE FROM`
- Pagination: cursor-based (last seen ID), never OFFSET

### Code quality
- No `print()` — use `import logging; logger = logging.getLogger(__name__)`
- No hardcoded secrets — all config via `app/config.py` reading from environment
- No `.env` files committed — `.env` is in `.gitignore`
- Pydantic v2 validation on ALL request bodies, no exceptions
- Max line length: 100 characters

### Tests
- Every new endpoint needs minimum: 1 happy path test + 1 unauthorized (401) test
- Coverage must stay ≥ 70%
- Test file mirrors source: `app/routers/auth.py` → `app/tests/test_auth.py`

---

## 5. Tech stack — exact versions

### Backend
```
fastapi==0.115.0
uvicorn[standard]==0.30.0
sqlalchemy==2.0.36
asyncpg==0.30.0
alembic==1.13.0
pydantic==2.9.0
pydantic-settings==2.5.0
python-jose[cryptography]==3.3.0
passlib[bcrypt]==1.7.4
httpx==0.27.0          # for tests
pytest==8.3.0
pytest-asyncio==0.24.0
pytest-cov==5.0.0
slowapi==0.1.9          # rate limiting
sentry-sdk[fastapi]==2.15.0
```

### Frontend
```
react 18, vite 5, react-router-dom 6
zustand 4, @tanstack/react-query 5
axios 1, tailwindcss 3
recharts 2
```

---

## 6. Security checklist — run before every commit

Ask yourself these questions. If any answer is NO — fix before committing.

- [ ] Every DB query filters by `current_user.id`?
- [ ] All inputs validated via Pydantic schema?
- [ ] No secrets or tokens in code?
- [ ] No raw SQL strings?
- [ ] New auth endpoints have rate limiting applied?
- [ ] Tests cover the happy path and 401 unauthorized case?
- [ ] No `print()` statements left in?

---

## 7. CI pipeline — what runs on every PR

1. Ruff lint (must pass)
2. Bandit SAST — HIGH severity blocks merge
3. pytest with coverage ≥ 70%
4. ESLint (frontend)
5. Vite build (frontend)
6. Docker build (must succeed)
7. Trivy image scan — CRITICAL CVE blocks merge

**If CI is red, do not merge. Fix the issue first.**

---

## 8. How to run locally

```bash
# Backend
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt -r requirements-dev.txt
cp .env.example .env   # fill in values
alembic upgrade head
uvicorn app.main:app --reload

# Frontend
cd frontend
npm install
npm run dev

# Tests
cd backend
pytest --cov=app --cov-report=term-missing

# Security scan
bandit -r app -ll
```

---

## 9. Environment variables

| Variable | Where used | Example |
|---|---|---|
| `DATABASE_URL` | backend | `postgresql+asyncpg://user:pass@host/db?ssl=require` |
| `JWT_SECRET` | backend | 64-char hex string (`openssl rand -hex 32`) |
| `JWT_ALGORITHM` | backend | `HS256` |
| `BOT_TOKEN` | backend | from BotFather |
| `FRONTEND_URL` | backend CORS | `https://budget-app.up.railway.app` |
| `SENTRY_DSN` | backend + frontend | from sentry.io |
| `VITE_API_URL` | frontend | `https://api.budget-app.up.railway.app` |

**Never put real values in code. Use Railway dashboard for production secrets.**

---

## 10. Session workflow

When I start a session with you, I will say which story I'm working on.
Your job:
1. Read the story AC from `/docs/backlog.md`
2. Check dependencies in `/docs/dependencies.md`
3. Propose a short implementation plan (3-5 bullet points) and wait for my approval
4. Implement only what the story requires — do not touch other files
5. Write tests
6. Run the security checklist mentally
7. Tell me exactly which files you created or modified

Do NOT refactor unrelated code. Do NOT add features not in the story. Do NOT create files outside the defined structure without asking.
