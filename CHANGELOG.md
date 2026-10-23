# Changelog

## [0.4.1] — 2026-10-23

### Added
- Audit retention: background task prunes audit_log rows older than AUDIT_RETENTION_DAYS (default 90).
- Audit viewer: GET /api/audit/log with pagination + filters (self-only).
- Audit UI table in dashboard.
- docs/DEPLOYMENT.md, docs/BACKUP.md, docs/OPERATIONS.md.
- .gitignore (explicit).
- README.md (rewritten with doc index).

### Changed
- app/api/audit.py — added GET /api/audit/log.
- app/main.py — starts retention background task in lifespan.
- app/core/config.py — added audit_retention_days, audit_cleanup_interval_hours.

### Security
- Audit viewer enforces self-only access.
- Retention prevents unbounded growth.

## [0.4.0] — 2026-10-23

### Added
- Path A — audit_log: model + migration + service + 2 endpoints + 11 tests.
- Path B — Runbook UI: index.html rewrite with severity badge, steps, action button.
- Path C — Copy-to-clipboard + ARIA: copy button, aria-live, document.execCommand fallback.
- Path D — Postgres integration: 13 tests + integration.yml workflow.
- E2E: 7 Playwright tests + e2e.yml workflow.
- requirements-e2e.txt.
- pytest marker integration.

### Changed
- tests/conftest.py — added db_session fixture.
- app/db/base.py — registers audit_log model.
- app/main.py — includes audit router.

### Security
- Audit actions allowlist-gated.
- _sanitize() strips 10 forbidden keys.
- No FK on user (governance preservation).
- No new subprocess/eval/exec.

## [0.3.1] — 2026-10-23

### Fixed
- WebSocket leak (receive() instead of sleep(3600)).
- DB isolation in tests.
- Coverage raised from 80% to 87.37%.

## [0.3.0] — 2026-10-23

### Added
- Initial release: FastAPI + WebSocket + JWT + Smart Runbooks + Prometheus.
