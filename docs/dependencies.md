# Story Dependencies

> Claude Code: check this before starting any story.
> If a dependency is not Done, finish it first.

---

## Dependency graph

```
S-01 (GitHub repo)
  └─ S-02 (CI pipeline)
       └─ S-03 (Docker build)
            └─ S-04 (Railway deploy)
                 └─ all production testing

A-01 (Register)
  └─ A-02 (Login + JWT)
       ├─ A-03 (Token refresh)
       ├─ A-04 (Logout)
       └─ [ALL protected endpoints — nothing below works without this]
            ├─ T-01 (Add transaction)
            │    └─ T-02 (List transactions)
            │         └─ T-03 (Edit), T-04 (Delete)
            ├─ T-05 (Categories)
            ├─ D-01 (Monthly totals) ← needs T-01 data to exist
            ├─ D-02 (Category chart) ← needs T-05 + T-01
            ├─ D-03 (Trend chart)    ← needs T-01
            └─ D-05 (Goals)

A-05 (Telegram auth)
  └─ 3.8 (Mini App frontend adaptation)
  [REQUIRES: BotFather bot created; BOT_TOKEN in Railway secrets]
```

---

## Dependency table

| Story | Hard dependencies (must be Done first) | External requirements |
|-------|----------------------------------------|-----------------------|
| A-02 | A-01 | — |
| A-03 | A-02 | — |
| A-04 | A-02 | — |
| A-05 | A-02 | BotFather bot created; BOT_TOKEN set in Railway |
| T-01..T-06 | A-02 | — |
| D-01..D-03 | T-01, T-05 | Need real transactions in DB to test |
| D-05 | A-02 | — |
| S-02 | S-01 | — |
| S-03 | S-02 | — |
| S-04 | S-03 | Railway account; RAILWAY_TOKEN in GitHub secrets |
| S-10 (Sentry) | S-04 | Sentry project created; SENTRY_DSN set |
| Frontend auth | A-02 deployed to Railway | VITE_API_URL set |
| Frontend dashboard | D-01, D-02, D-03 deployed | — |
| Mini App | A-05, Bot created in Telegram | Bot registered with BotFather |

---

## Phase 1 recommended implementation order

Follow this order to avoid blocked work:

```
1. S-01  → GitHub repo + branch protection
2. S-02  → CI pipeline skeleton (can start with placeholder tests)
3. 1.x   → Backend scaffold (FastAPI app factory, config, DB connection)
4. A-01  → Register endpoint + User model + Alembic migration
5. A-02  → Login + JWT + refresh token
6. A-03  → Token refresh
7. A-04  → Logout
8. S-03  → Dockerize backend
9. S-04  → Railway deploy (so frontend can point to real API)
10. T-05 → Categories (needed before transactions)
11. T-01 → Add transaction
12. T-02 → List transactions
13. T-03 → Edit transaction
14. T-04 → Delete transaction (soft)
15. T-06 → Filters
16. D-01 → Monthly totals
17. D-02 → Category breakdown
18. D-03 → Trend
19. D-05 → Goals
20. S-06 → Rate limiting
21. S-07 → Security headers
22. S-09 → Dependabot
23. S-10 → Sentry
24. Frontend scaffold
25. Frontend auth screens
26. Frontend dashboard + all tabs
27. A-05 → Telegram auth
28. Frontend Mini App adaptation
29. S-13 → OWASP checklist
```
