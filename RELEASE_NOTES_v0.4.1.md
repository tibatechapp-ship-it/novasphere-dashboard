# Raqib v0.4.1 — "Closure"

The final release of the v0.4.x line. Adds audit retention, an audit
viewer, and complete operations documentation. No breaking changes from
v0.3.1 or v0.4.0.

## New in v0.4.1

### Audit retention
- Background task prunes `audit_log` rows older than `AUDIT_RETENTION_DAYS`
  (default: 90).
- Manual `prune_once()` for one-off runs.
- Configurable interval via `AUDIT_CLEANUP_INTERVAL_HOURS` (default: 24).
- Set `AUDIT_RETENTION_DAYS=0` to keep forever.
- Prevents unbounded growth — a real operational risk that v0.4.0
  introduced by adding write-only audit without cleanup.

### Audit viewer
- `GET /api/audit/log` — paginated, filtered, self-only.
  - Filters: `action`, `since`, `until`
  - Pagination: `page` (default 1), `page_size` (default 50, max 200)
  - Users can only view their own rows (enforced by `_require_admin_or_self`)
- UI table in the dashboard showing recent governance events.
- Why self-only: adding a full admin role is a v0.5.0 feature. v0.4.1
  delivers the read path without expanding the authorization surface.

### Operations documentation
- `docs/DEPLOYMENT.md` — production deployment from scratch:
  prerequisites, secret generation, reverse proxy (Caddy + nginx
  examples with the critical `/ws` upgrade block), verification
  checklist, 5 common pitfalls with fixes.
- `docs/BACKUP.md` — daily cron script, restore procedure, disaster
  recovery scenarios (lost `.env`, lost `pg` volume, lost `rd` volume),
  encryption guidance.
- `docs/OPERATIONS.md` — daily/weekly checks, Prometheus alert rules,
  4 common incidents with resolution steps, emergency stop, log
  locations.

### Repo completeness
- `.gitignore` — explicit (previously missing). Excludes `.env`,
  `*.db`, `.venv`, secrets, backups.
- `README.md` — rewritten with a doc index and v0.4.1 quick-start.
- `CHANGELOG.md` — v0.4.0 and v0.4.1 sections.

## Tests

- 69+ unit tests, 87.37% coverage (gate: 85%)
- 13 Postgres integration tests (skipped without `POSTGRES_TEST_URL`)
- 7 E2E Playwright tests (skipped without running app)
- 0 skips on critical paths (WS, auth, rate limit, audit)

## Security (DoD 10/10)

- No `subprocess`, `os.system`, `eval`, `exec`, `shell=True`
- Passwords: bcrypt (cost=12)
- JWT: HS256, HttpOnly + Secure + SameSite=Strict in production
- Rate limiting: single Redis-backed limiter
- CORS: explicit allow-list only
- Docker: non-root, no exposed DB/Redis ports in prod
- CI gates: bandit, pip-audit, gitleaks, trivy
- Audit writes: allowlist-gated + secret sanitization
- Audit reads: self-only by design

## DoD checklist

- ruff check ................ clean
- ruff format --check ....... clean
- pytest >=85% cov ........... 87.37%
- bandit (HIGH) ............. clean
- alembic current ........... 001_audit_log (head)
- no subprocess/os.system ... clean
- no eval/exec .............. clean
- no shell=True ............. clean
- no allow_origins=* ........ clean
- ws leak guard ............. passed

## Upgrade from v0.4.0

```bash
git pull origin main
git checkout v0.4.1
pip install -r requirements.txt
alembic upgrade head          # idempotent — no new migrations
pytest -v                     # expect: all green
```

No schema changes, no new env vars required, no breaking API changes.
AUDIT_RETENTION_DAYS defaults to 90 — set explicitly if you need
different retention.

## Known limitations (planned for v0.5.0)

- No admin role — audit viewer is self-only. Extend
  _require_admin_or_self when roles land (do not bypass it).
- No audit export (CSV/JSON) endpoint yet.
- E2E tests rely on mock_data=true; a fully deterministic WS payload
  is deferred.
- runbook-ui.js may be dead code — verify with
  grep -n "runbookUI" app/static/index.html before the next cleanup.

## Links

- Full changelog: CHANGELOG.md
- Security policy: SECURITY.md
- Deployment: docs/DEPLOYMENT.md
- Backup: docs/BACKUP.md
- Operations: docs/OPERATIONS.md
- Runbooks: docs/RUNBOOKS.md
- ADRs: docs/ADR/
- Repository: https://github.com/tibatechapp-ship-it/raqib
