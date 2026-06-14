# API Specification

> Claude Code: use this as the single source of truth for endpoint contracts.
> FastAPI generates /docs (Swagger) automatically — this file drives what gets built.

---

## Base URL

- Local: `http://localhost:8000`
- Production: `https://api.budget-app.up.railway.app` (update after deploy)

## Auth convention

- Protected endpoints: `Authorization: Bearer <access_token>` header
- `get_current_user` dependency extracts `user_id` from JWT — use in all protected routes
- Never trust `user_id` from request body

## Response format

Success: HTTP 200/201 + JSON body
Error:
```json
{ "detail": "Human-readable error message" }
```

---

## Auth endpoints — /auth

### POST /auth/register
```
Body:   { email: str, password: str (min 8 chars) }
200:    { access_token: str, token_type: "bearer", user: UserOut }
        + Set-Cookie: refresh_token=...; HttpOnly; Secure; SameSite=Strict; Path=/auth/refresh
400:    { detail: "Email already registered" }
422:    Pydantic validation error
```
Side effects: creates User, creates RefreshToken, writes audit_log action='register'

### POST /auth/login
```
Body:   { email: str, password: str }
200:    { access_token: str, token_type: "bearer", user: UserOut }
        + Set-Cookie: refresh_token (same as register)
401:    { detail: "Invalid credentials" }
429:    Rate limit exceeded (60/min per IP)
```
Side effects: writes audit_log action='login' or 'failed_login'

### POST /auth/refresh
```
Cookie: refresh_token (httpOnly)
200:    { access_token: str, token_type: "bearer" }
401:    { detail: "Invalid or expired refresh token" }
```
Side effects: rotates refresh token (old revoked, new issued)

### POST /auth/logout
```
Header: Authorization: Bearer <access_token>
200:    { ok: true }
```
Side effects: revokes refresh token in DB; clears cookie; audit_log action='logout'

### POST /auth/telegram
```
Body:   { init_data: str }   ← raw Telegram WebApp.initData string
200:    { access_token: str, token_type: "bearer", user: UserOut }
400:    { detail: "Invalid initData" }
400:    { detail: "initData expired" }
```
Validation: HMAC-SHA256 with BOT_TOKEN; reject if auth_date > 86400s ago
Side effects: upserts User (telegram_id); audit_log action='telegram_login'

---

## User endpoints — /user

### GET /user/me
```
Auth: Bearer
200: UserOut
```

### PATCH /user/me
```
Auth: Bearer
Body: { email?: str, currency?: str (3 chars) }
200: UserOut
400: { detail: "Email already taken" }
```

### DELETE /user/me
```
Auth: Bearer
200: { ok: true, message: "Account scheduled for deletion" }
```
Side effects: sets deleted_at; cascades to all user data after 30-day grace

---

## Transactions — /transactions

### GET /transactions
```
Auth: Bearer
Query params:
  date_from:   date (YYYY-MM-DD), default: first day of current month
  date_to:     date (YYYY-MM-DD), default: today
  category_id: UUID, optional
  type:        "income" | "expense", optional
  cursor:      UUID (last seen transaction id), optional
  limit:       int (1-100), default 50
200: {
  items: TransactionOut[],
  next_cursor: UUID | null   ← null means no more pages
}
```
Rules: deleted_at IS NULL; filter by current_user.id always

### POST /transactions
```
Auth: Bearer
Body: {
  amount_cents: int (> 0),
  category_id: UUID,
  tx_date: date,
  note: str | null (max 500 chars)
}
201: TransactionOut
400: { detail: "Category not found or does not belong to user" }
```

### PATCH /transactions/{id}
```
Auth: Bearer
Body: partial — any subset of POST body fields
200: TransactionOut
404: { detail: "Transaction not found" }
```
Rule: verify transaction.user_id == current_user.id before updating

### DELETE /transactions/{id}
```
Auth: Bearer
200: { ok: true }
404: { detail: "Transaction not found" }
```
Rule: sets deleted_at = now(); does NOT delete row

---

## Categories — /categories

### GET /categories
```
Auth: Bearer
200: CategoryOut[]
```
Returns all user's categories (no pagination — max 50)

### POST /categories
```
Auth: Bearer
Body: { name: str (max 64), color: str (#RRGGBB), type: "income" | "expense" }
201: CategoryOut
400: { detail: "Maximum 50 categories reached" }
```

### PATCH /categories/{id}
```
Auth: Bearer
Body: partial POST body
200: CategoryOut
404: not found
```

### DELETE /categories/{id}
```
Auth: Bearer
200: { ok: true }
```
Note: transactions with this category_id get category_id = NULL (SET NULL FK)

---

## Goals — /goals

### GET /goals
```
Auth: Bearer
200: GoalOut[]
```

### POST /goals
```
Auth: Bearer
Body: { name: str, target_cents: int, current_cents: int, deadline: date | null }
201: GoalOut
```

### PATCH /goals/{id}
```
Auth: Bearer
Body: partial POST body
200: GoalOut
```

### DELETE /goals/{id}
```
Auth: Bearer
200: { ok: true }
```

---

## Analytics — /analytics

### GET /analytics/summary
```
Auth: Bearer
Query: month=YYYY-MM (default: current month)
200: {
  month: "YYYY-MM",
  income_cents: int,
  expense_cents: int,
  balance_cents: int
}
```

### GET /analytics/categories
```
Auth: Bearer
Query: month=YYYY-MM
200: {
  month: "YYYY-MM",
  items: [
    { category_id: UUID, name: str, color: str, type: str, total_cents: int, percentage: float }
  ]
}
```
Returns top 5 categories + aggregated "Other" if more than 5

### GET /analytics/trend
```
Auth: Bearer
Query: months=6 (int, 1-24)
200: {
  items: [
    { month: "YYYY-MM", income_cents: int, expense_cents: int }
  ]
}
```
Ordered oldest → newest

---

## Pydantic schemas reference

```python
# schemas/user.py
class UserOut(BaseModel):
    id: UUID
    email: str | None
    telegram_id: int | None
    currency: str
    created_at: datetime

# schemas/transaction.py
class TransactionCreate(BaseModel):
    amount_cents: int = Field(gt=0)
    category_id: UUID
    tx_date: date
    note: str | None = Field(None, max_length=500)

class TransactionOut(TransactionCreate):
    id: UUID
    user_id: UUID
    created_at: datetime
    updated_at: datetime

# schemas/category.py
class CategoryCreate(BaseModel):
    name: str = Field(max_length=64)
    color: str = Field(pattern=r'^#[0-9A-Fa-f]{6}$')
    type: Literal['income', 'expense']

# schemas/goal.py
class GoalCreate(BaseModel):
    name: str = Field(max_length=128)
    target_cents: int = Field(gt=0)
    current_cents: int = Field(ge=0, default=0)
    deadline: date | None = None
```

---

## HTTP status codes used

| Code | When |
|------|------|
| 200 | Success (GET, PATCH, DELETE) |
| 201 | Created (POST) |
| 400 | Business logic error (duplicate email, wrong owner) |
| 401 | Missing/invalid/expired token |
| 403 | Authenticated but not authorized (wrong user) |
| 404 | Resource not found (and belongs to this user) |
| 422 | Pydantic validation failed |
| 429 | Rate limit exceeded |
| 500 | Unexpected server error (goes to Sentry) |
