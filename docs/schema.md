# Database Schema Reference

> Claude Code: read this when implementing models, migrations, or queries.
> All money values are INTEGER cents. All PKs are UUID.

---

## General rules

- Primary keys: `UUID DEFAULT gen_random_uuid()`
- Timestamps: `TIMESTAMPTZ DEFAULT now()`
- Soft delete: `deleted_at TIMESTAMPTZ NULL` (NULL = active)
- All queries: filter `deleted_at IS NULL` unless explicitly recovering data
- Money: `INTEGER` cents only. 10.50 BYN = `1050`
- DB user has: SELECT, INSERT, UPDATE, DELETE only. No DDL in application code.
- All connections: `?sslmode=require`

---

## Table: users

```sql
CREATE TABLE users (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email           TEXT UNIQUE,          -- NULL for Telegram-only users
    telegram_id     BIGINT UNIQUE,        -- NULL for web-only users
    password_hash   TEXT,                 -- bcrypt; NULL for Telegram-only users
    currency        CHAR(3) NOT NULL DEFAULT 'BYN',  -- ISO 4217
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- At least one of email or telegram_id must be present
ALTER TABLE users ADD CONSTRAINT users_has_identity
    CHECK (email IS NOT NULL OR telegram_id IS NOT NULL);
```

SQLAlchemy model location: `backend/app/models/user.py`

---

## Table: refresh_tokens

```sql
CREATE TABLE refresh_tokens (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id     UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    token_hash  TEXT NOT NULL,           -- SHA-256 of the actual token string
    expires_at  TIMESTAMPTZ NOT NULL,
    revoked     BOOLEAN NOT NULL DEFAULT false,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX idx_refresh_tokens_user_id ON refresh_tokens(user_id);
CREATE INDEX idx_refresh_tokens_token_hash ON refresh_tokens(token_hash);
```

SQLAlchemy model location: `backend/app/models/refresh_token.py`

---

## Table: categories

```sql
CREATE TABLE categories (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id     UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    name        TEXT NOT NULL CHECK (char_length(name) <= 64),
    color       CHAR(7) NOT NULL CHECK (color ~ '^#[0-9A-Fa-f]{6}$'),
    type        TEXT NOT NULL CHECK (type IN ('income', 'expense')),
    created_at  TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX idx_categories_user_id ON categories(user_id);

-- Max 50 categories per user enforced in application layer (service)
```

SQLAlchemy model location: `backend/app/models/category.py`

---

## Table: transactions

```sql
CREATE TABLE transactions (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id         UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    category_id     UUID REFERENCES categories(id) ON DELETE SET NULL,
    amount_cents    INTEGER NOT NULL CHECK (amount_cents > 0),
    note            TEXT CHECK (char_length(note) <= 500),
    tx_date         DATE NOT NULL,           -- user-entered date, not server time
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
    deleted_at      TIMESTAMPTZ              -- NULL = active; soft delete
);

CREATE INDEX idx_transactions_user_id ON transactions(user_id);
CREATE INDEX idx_transactions_tx_date ON transactions(tx_date DESC);
CREATE INDEX idx_transactions_user_date ON transactions(user_id, tx_date DESC)
    WHERE deleted_at IS NULL;

-- Full-text search (Phase 2)
-- ALTER TABLE transactions ADD COLUMN note_tsv TSVECTOR
--     GENERATED ALWAYS AS (to_tsvector('russian', coalesce(note, ''))) STORED;
-- CREATE INDEX idx_transactions_note_fts ON transactions USING GIN(note_tsv);
```

SQLAlchemy model location: `backend/app/models/transaction.py`

---

## Table: goals

```sql
CREATE TABLE goals (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id         UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    name            TEXT NOT NULL CHECK (char_length(name) <= 128),
    target_cents    INTEGER NOT NULL CHECK (target_cents > 0),
    current_cents   INTEGER NOT NULL DEFAULT 0 CHECK (current_cents >= 0),
    deadline        DATE,                   -- nullable
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX idx_goals_user_id ON goals(user_id);
```

SQLAlchemy model location: `backend/app/models/goal.py`

---

## Table: audit_log (security)

```sql
CREATE TABLE audit_log (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id     UUID REFERENCES users(id) ON DELETE SET NULL,
    action      TEXT NOT NULL,             -- 'login', 'logout', 'register', 'telegram_login', 'failed_login'
    ip_address  INET,
    user_agent  TEXT,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX idx_audit_log_user_id ON audit_log(user_id, created_at DESC);

-- Retention: 90 days. Cleanup cron: DELETE FROM audit_log WHERE created_at < now() - interval '90 days'
```

SQLAlchemy model location: `backend/app/models/audit_log.py`

---

## Alembic migration workflow

```bash
# Create new migration after changing models
alembic revision --autogenerate -m "description_of_change"

# Review the generated file in alembic/versions/ before running!

# Apply migrations
alembic upgrade head

# Rollback one step
alembic downgrade -1

# Current state
alembic current
```

**Rule: never edit applied migrations. Always create a new one.**

---

## Query patterns (copy these, do not invent your own)

### List with soft-delete filter
```python
result = await db.execute(
    select(Transaction)
    .where(Transaction.user_id == current_user.id)
    .where(Transaction.deleted_at.is_(None))
    .order_by(Transaction.tx_date.desc())
    .limit(50)
)
transactions = result.scalars().all()
```

### Cursor pagination
```python
query = (
    select(Transaction)
    .where(Transaction.user_id == current_user.id)
    .where(Transaction.deleted_at.is_(None))
    .order_by(Transaction.id.desc())
)
if cursor:  # cursor = last seen transaction id
    query = query.where(Transaction.id < cursor)
query = query.limit(page_size + 1)  # fetch one extra to know if there's a next page
```

### Monthly analytics
```python
from sqlalchemy import func, extract

result = await db.execute(
    select(
        func.sum(Transaction.amount_cents).label("total"),
        Category.type.label("type")
    )
    .join(Category, Transaction.category_id == Category.id)
    .where(Transaction.user_id == current_user.id)
    .where(Transaction.deleted_at.is_(None))
    .where(extract('year', Transaction.tx_date) == year)
    .where(extract('month', Transaction.tx_date) == month)
    .group_by(Category.type)
)
```
