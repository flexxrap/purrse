# Product Backlog — Story Status

> Update this file after completing each story. Change `[ ]` to `[x]`.
> Claude Code reads this file to understand what is done and what is next.

---

## How to read this file

- `[x]` = Done (merged to main, deployed)
- `[~]` = In Progress (current session)
- `[ ]` = Todo
- `[-]` = Skipped / deferred to later phase

**Current focus: Phase 1 MVP**

---

## Epic 1 — Authentication & User Management

| ID | Story | Priority | SP | Status | AC |
|----|-------|----------|----|--------|----|
| A-01 | Register with email + password | P0 | 3 | `[x]` | bcrypt stored; JWT returned; 400 on duplicate email |
| A-02 | Login → JWT + refresh cookie | P0 | 3 | `[x]` | Access 15 min; httpOnly cookie 30 days; /me returns user |
| A-03 | Refresh session silently | P0 | 2 | `[x]` | Silent refresh before expiry; revoked token → 401 |
| A-04 | Logout + invalidate session | P0 | 1 | `[x]` | refresh_tokens.revoked=true; cookie cleared |
| A-05 | Telegram Mini App login | P0 | 5 | `[ ]` | initData HMAC verified; user upserted; JWT issued |
| A-06 | Update email or currency | Should | 2 | `[ ]` | Validation; email uniqueness check |
| A-07 | Delete account + all data | Should | 3 | `[ ]` | Cascade delete; GDPR; Phase 2 |
| A-08 | Change password | Should | 2 | `[ ]` | Old password required; new bcrypt hash |

---

## Epic 2 — Transactions & Categories

| ID | Story | Priority | SP | Status | AC |
|----|-------|----------|----|--------|----|
| T-01 | Add transaction | P0 | 3 | `[x]` | amount_cents stored; category required; date defaults today |
| T-02 | List transactions (paginated) | P0 | 3 | `[x]` | Default last 30 days; cursor pagination; <200ms p95 |
| T-03 | Edit transaction | P0 | 2 | `[x]` | All fields editable; updated_at set |
| T-04 | Delete transaction (soft) | P0 | 1 | `[x]` | Sets deleted_at; data recoverable 30 days |
| T-05 | Create/manage categories | P0 | 3 | `[x]` | Max 50 per user; color validated as hex |
| T-06 | Filter by date, category, type | Must | 3 | `[ ]` | Filters combinable; URL-param driven |
| T-07 | Search by note text | Should | 2 | `[ ]` | PostgreSQL full-text; min 3 chars; Phase 2 |
| T-08 | Import from CSV | Could | 8 | `[ ]` | Column mapping; preview; Phase 3 |
| T-09 | Export to CSV/PDF | Should | 5 | `[ ]` | Async job; download link; Phase 2 |
| T-10 | Recurring transactions | Could | 5 | `[ ]` | Weekly/monthly/yearly; Phase 3 |

---

## Epic 3 — Dashboard & Analytics

| ID | Story | Priority | SP | Status | AC |
|----|-------|----------|----|--------|----|
| D-01 | Monthly totals (income/expense/balance) | P0 | 3 | `[x]` | Server-side calc; updates <1s |
| D-02 | Category breakdown chart | Must | 3 | `[x]` | Top 5 + Other; category colors |
| D-03 | Monthly trend line (last 6 months) | Must | 3 | `[x]` | Income vs expense; hover tooltip |
| D-04 | Budget planning bar (planned vs actual) | Should | 3 | `[ ]` | Per category; red when over; Phase 2 |
| D-05 | Goals progress bars | Must | 3 | `[x]` | Months to completion from free balance |
| D-06 | Monthly budget per category + alerts | Should | 5 | `[ ]` | Alert at 80%; Telegram notify; Phase 2 |

---

## Epic 4 — DevSecOps & Infrastructure

| ID | Task | Priority | SP | Status | Acceptance Criteria |
|----|------|----------|----|--------|---------------------|
| S-01 | GitHub repo + branch protection | P0 | 1 | `[x]` | Direct push to main blocked; CI required |
| S-02 | CI: lint + test + Bandit + Trivy | P0 | 3 | `[x]` | Pipeline <5 min; HIGH findings block merge |
| S-03 | Docker multi-stage build | P0 | 2 | `[x]` | Image <200 MB; non-root user |
| S-04 | Railway deploy + env secrets | P0 | 2 | `[ ]` | No secrets in code; prod URL live |
| S-05 | HTTPS + HSTS | P0 | 1 | `[x]` | Railway auto-TLS; HSTS header |
| S-06 | Rate limiting on auth endpoints | P0 | 2 | `[ ]` | 60/min per IP; 429 with Retry-After |
| S-07 | Security headers middleware | P0 | 2 | `[x]` | CSP, X-Frame-Options, etc. |
| S-08 | Automated DB backups to R2 | Must | 3 | `[ ]` | Daily; verified restore; Phase 2 |
| S-09 | Dependabot for Python + npm | Must | 1 | `[x]` | PRs within 24h of new CVE |
| S-10 | Sentry integration | Must | 2 | `[ ]` | Errors in Sentry <30s; p95 tracked |
| S-11 | GDPR: export + deletion | Should | 3 | `[ ]` | JSON export; deletion <30s; Phase 2 |
| S-12 | DB connection pooling | Should | 2 | `[ ]` | Pool 10; overflow 20; Phase 2 |
| S-13 | OWASP Top 10 checklist review | Must | 5 | `[ ]` | P0/P1 findings fixed before launch |

---

## Phase summary

| Phase | Stories | Status |
|-------|---------|--------|
| Phase 1 MVP | A-01..A-05, T-01..T-06, D-01..D-03, D-05, S-01..S-07, S-09, S-10, S-13 | Not started |
| Phase 2 | A-06..A-08, T-07, T-09, D-04, D-06, S-08, S-11, S-12 | Not started |
| Phase 3 | T-08, T-10 | Not started |

---

## Completed stories log

<!-- Move stories here when done, with date -->
<!-- Example: -->
<!-- - [x] A-01 Register — Done 2025-06-15 -->
