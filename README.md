# 🐱 purrse — personal finance tracker

> Track income and expenses by category, set savings goals, and plan monthly budgets.
> Available as a web app and Telegram Mini App.

**Live:** [purrse.up.railway.app](https://purrse.up.railway.app) · **Bot:** [@purrse_bot](https://t.me/purrse_bot)

---

## Features

- **Transactions** — add income/expense with category, date, and note; soft delete; full-text search
- **Categories** — custom categories with colors; up to 50 per user
- **Analytics** — monthly totals, category breakdown pie chart, 6-month income/expense trend
- **Budget planning** — set monthly limits per category; alert at 80% via Telegram
- **Savings goals** — track progress with estimated months to completion
- **Recurring transactions** — weekly / monthly / yearly auto-entries
- **CSV import / export** — column mapping preview before import; export with date filters
- **Telegram bot** — `/stats` for instant monthly summary; monthly digest on the 1st; budget alerts
- **GDPR** — full data export as JSON; account deletion with cascade

---

## Stack

| Layer | Tech |
|---|---|
| Frontend | React 18, Vite 5, React Query 5, Zustand 4, Framer Motion, Recharts, Tailwind CSS 3 |
| Backend | FastAPI 0.115, SQLAlchemy 2 (async), PostgreSQL 16, Alembic, Pydantic v2 |
| Auth | JWT HS256 (15 min) + httpOnly refresh cookie (30 days), bcrypt, Telegram initData HMAC |
| Infra | Railway (backend + frontend + PostgreSQL + Redis), Docker multi-stage, GitHub Actions CI |
| Observability | Sentry, structured logging |
| Security | OWASP Top 10 reviewed, Bandit SAST, Trivy image scan, rate limiting via slowapi + Redis |

---

## Architecture

```
Telegram Bot / Web Browser
        │
        ▼
  FastAPI (Railway)
   ├── /auth           — JWT + refresh tokens
   ├── /transactions
   ├── /categories
   ├── /analytics
   ├── /budgets
   ├── /goals
   ├── /recurring
   └── /bot/webhook    — Telegram updates
        │
   PostgreSQL (Railway) + Redis (rate limits)
```

- Money stored as **integer cents** — no float rounding errors
- All queries filter by `current_user.id` — broken access control impossible by convention
- Cursor-based pagination (no OFFSET)
- APScheduler cron: recurring transactions daily, monthly Telegram digest on the 1st

---

## Running locally

```bash
# Backend
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt -r requirements-dev.txt
cp .env.example .env   # fill in DATABASE_URL, JWT_SECRET, BOT_TOKEN, FRONTEND_URL
alembic upgrade head
uvicorn app.main:app --reload

# Frontend
cd frontend
npm install
npm run dev

# Tests
cd backend && pytest --cov=app --cov-report=term-missing

# Security scan
bandit -r app -ll
```

---

## CI pipeline

Every PR runs: **Ruff** → **Bandit** → **pytest ≥ 70% coverage** → **ESLint** → **Vite build** → **Docker build** → **Trivy scan**

HIGH severity findings block merge.

---

## Environment variables

| Variable | Description |
|---|---|
| `DATABASE_URL` | `postgresql+asyncpg://...` |
| `JWT_SECRET` | 64-char hex (`openssl rand -hex 32`) |
| `BOT_TOKEN` | Telegram BotFather token |
| `FRONTEND_URL` | CORS origin + WebApp URL |
| `BACKEND_URL` | For Telegram webhook auto-registration |
| `REDIS_URL` | Redis for rate-limit storage (optional, falls back to memory) |
| `SENTRY_DSN` | Error tracking |

---

## License

MIT
