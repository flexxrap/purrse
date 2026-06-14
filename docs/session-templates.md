# Claude Code Session Templates

> Copy-paste these prompts. Fill in the [BRACKETS].
> These are optimized to give Claude Code the right context without wasting tokens.

---

## SESSION START — use this every time

```
Read CLAUDE.md and docs/backlog.md before doing anything.

Current task: story [ID] — [story title]
AC: [paste acceptance criteria from backlog.md]

Files you will likely touch:
- [list the files]

Propose a 3-5 step implementation plan and wait for my approval before writing any code.
```

---

## SESSION END — use before closing

```
Before we finish this story:
1. Run: cd backend && pytest --cov=app --cov-report=term-missing
2. Run: cd backend && bandit -r app/ -ll -x app/tests/
3. Check docs/done-criteria.md — tell me which items are met and which need attention
4. List every file you created or modified
5. What should I update in docs/backlog.md?
```

---

## STORY TEMPLATES by epic

### Starting an Auth story (A-xx)

```
Read CLAUDE.md, docs/backlog.md, docs/schema.md, docs/api-spec.md, docs/devsecops.md.

Task: implement story [A-XX]
AC: [paste from backlog]

Key rules to remember:
- JWT: HS256, access 15 min, refresh httpOnly cookie 30 days
- Passwords: bcrypt rounds=12
- Write to audit_log table on every auth event
- Rate limit: 60/min on this endpoint
- Tests: happy path + 401 unauthorized + 429 rate limit exceeded

Files: backend/app/routers/auth.py, backend/app/services/auth_service.py, backend/app/tests/test_auth.py
```

### Starting a Transaction/Category story (T-xx)

```
Read CLAUDE.md, docs/schema.md, docs/api-spec.md.

Task: implement story [T-XX]
AC: [paste from backlog]

Critical rule: every DB query MUST filter by current_user.id from JWT — never from request body.
Use soft delete (deleted_at) not DELETE.
Use cursor pagination (not OFFSET).

Files: backend/app/routers/transactions.py, backend/app/services/transaction_service.py, backend/app/tests/test_transactions.py
```

### Starting an Analytics story (D-xx)

```
Read CLAUDE.md, docs/schema.md, docs/api-spec.md.

Task: implement story [D-XX]
AC: [paste from backlog]

Use PostgreSQL aggregations (GROUP BY, window functions) — not Python-side calculations.
All money returned as INTEGER cents.
Default month = current month if not specified.

Files: backend/app/routers/analytics.py, backend/app/tests/test_analytics.py
```

### Starting a DevSecOps story (S-xx)

```
Read CLAUDE.md, docs/devsecops.md.

Task: implement story [S-XX]
AC: [paste from backlog]

Reference implementations are in docs/devsecops.md — use them as-is, do not invent your own patterns for security-critical code.

Files: [depends on story]
```

### Starting a Frontend story

```
Read CLAUDE.md.

Task: implement [frontend story]
AC: [paste]

Rules:
- Never use localStorage for tokens — access token in Zustand memory store only
- Use TanStack Query for server state (NOT useState + useEffect for API calls)
- API calls go in src/api/[domain].js
- No raw fetch() calls in components — always via api/ layer
- Handle loading and error states for every API call

Files: frontend/src/[relevant files]
```

---

## SPECIAL PURPOSE PROMPTS

### Code review before PR

```
Review the following diff against the security rules in CLAUDE.md.

Focus on:
1. Access control: does every query filter by current_user.id?
2. No raw SQL strings?
3. Pydantic validation on all inputs?
4. No secrets hardcoded?
5. Refresh token stored as hash, not raw value?
6. Any Bandit HIGH patterns (hardcoded passwords, string format in SQL)?

Answer: list each issue found, or confirm "no issues found".

[paste git diff here]
```

### Debug session

```
Context: FastAPI app, structure per CLAUDE.md.

Problem: [describe what's wrong]

Error message:
[paste full traceback]

Relevant code:
[paste the file or function]

Fix only this specific issue. Do not refactor other parts.
```

### Writing tests for existing code

```
Read CLAUDE.md.

Write pytest tests for [file/function].
Test file location: backend/app/tests/test_[name].py

Requirements:
- Use httpx AsyncClient + pytest-asyncio
- Happy path
- 401 Unauthorized (missing token)
- 403 Forbidden (wrong user's resource)
- 422 Validation error (bad input)
- [any story-specific edge cases]

Do not mock the database — use the test PostgreSQL instance.
```

### Adding a new Alembic migration

```
Read docs/schema.md.

I need to add [describe the schema change].

Steps:
1. Update the SQLAlchemy model in backend/app/models/[file].py
2. Create the Alembic migration: alembic revision --autogenerate -m "[description]"
3. Show me the generated migration file content so I can review it
4. Do NOT run alembic upgrade head — I will do that manually after review

Follow the query patterns in docs/schema.md.
```

### Implementing security middleware

```
Read docs/devsecops.md — specifically the "Application middleware stack" section.

Implement [specific middleware/security feature] following exactly the patterns shown there.
Do not invent new approaches — use the reference implementations.

Location: backend/app/middleware/[file].py
```

---

## QUICK REFERENCE — what each file is for

| File | When to read | Contains |
|------|-------------|----------|
| `CLAUDE.md` | Every session | Architecture rules, folder structure, forbidden patterns |
| `docs/backlog.md` | Every session start | Story status, AC, priorities |
| `docs/schema.md` | Models, migrations, queries | Table definitions, query patterns |
| `docs/api-spec.md` | Endpoints, schemas | Request/response contracts |
| `docs/devsecops.md` | Auth, middleware, CI | Security implementations, Dockerfile, CI YAML |
| `docs/dependencies.md` | Before starting a story | What must be done first |
| `docs/done-criteria.md` | Before closing a story | Checklist to verify |
| `docs/session-templates.md` | You are here | Copy-paste prompts |
