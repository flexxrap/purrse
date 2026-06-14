# Definition of Done

> Claude Code: before marking any story as done, verify ALL checkboxes below.
> A story is not done until every applicable box is checked.

---

## Story-level DoD

Every story, no exceptions:

- [ ] Code written and reviewed (or self-reviewed with security checklist)
- [ ] Tests pass locally (`pytest --cov=app`)
- [ ] Coverage did not drop below 70%
- [ ] Bandit clean (`bandit -r app -ll` — no HIGH findings)
- [ ] No `print()` left in code
- [ ] No secrets or tokens in code
- [ ] All inputs validated via Pydantic schema
- [ ] Every DB query filters by `current_user.id` (if user data involved)
- [ ] CI is green on the PR branch
- [ ] Acceptance criteria from backlog.md are met

For backend stories specifically:
- [ ] New endpoint appears in FastAPI /docs (Swagger)
- [ ] At minimum: 1 happy path test + 1 unauthorized test

For frontend stories specifically:
- [ ] Feature works in browser (Chrome + Firefox)
- [ ] No access token in localStorage (check DevTools → Application → Local Storage)
- [ ] API errors handled gracefully (no unhandled promise rejections)

---

## Phase-level DoD

Before calling Phase 1 complete:

- [ ] All P0 stories in phase: status = `[x]` in backlog.md
- [ ] CI pipeline green on main branch
- [ ] App deployed to Railway prod URL (not just staging)
- [ ] Sentry receiving events from production
- [ ] OWASP Top 10 checklist (S-13) reviewed and P0/P1 findings fixed
- [ ] README updated with: how to run locally, env vars needed, how to deploy
- [ ] All environment variables documented in README (names only, no values)

---

## Public launch DoD

Before opening to non-test users:

- [ ] All Phase 1 DoD items complete
- [ ] Privacy policy page exists and is linked from the app
- [ ] GDPR data export endpoint working (S-11, can be manual for now)
- [ ] Rate limiting tested under simulated load
- [ ] DB backup has been created AND successfully restored at least once
- [ ] Telegram Mini App tested in production bot (not test environment)
- [ ] Zero CRITICAL Trivy CVEs in current production image
- [ ] Sentry error rate < 0.1% over 48 hours of testing
- [ ] No hardcoded test data or debug routes in production code

---

## How Claude Code should use this file

At the end of each story session, run through the applicable checklist above.
If any item is not met, fix it before asking me to mark the story as done.

When I say "wrap up this story", respond with:
1. Which DoD items are met
2. Which items need attention
3. Exact commands to run to verify (pytest, bandit, etc.)
