# Raqib — Agent Brief (v0.4.1)

## Project
Real-time AI Analytics Dashboard — FastAPI + WebSocket + JWT + Smart Runbooks + Audit Trail.

## Non-negotiables
1. No subprocess, os.system, eval, exec, shell=True in app/
2. Runbooks are read-only UI text (no execution)
3. Single Redis-backed rate limiter (no duplicate)
4. Real WebSocket tests (no skips on critical paths)
5. Real Prometheus metrics via Instrumentator
6. Safe lifespan migration (try/except fallback)
7. Production-safe Docker (no exposed DB/Redis ports)
8. Dependency hygiene (no asyncpg, no passlib)
9. Cookie/CORS coherence (secure, samesite per env)
10. Coverage gate >= 85%

## Phases
- Phase 1: Foundation (app/ refactor, Alembic, lifespan)
- Phase 2: Rate limiting + metrics
- Phase 3: Smart runbooks
- Phase 4: Testing + CI
- Phase 5: Observability + docs
- Phase 6: Final (DoD, PR templates, release)

## v0.4.0 Paths
- A: audit_log (model + migration + service + API + tests)
- B: Runbook UI (index.html + runbook-ui.js)
- C: Copy-to-clipboard + ARIA
- D: Postgres integration tests

## v0.4.1 Paths
- A: Audit retention (background cleanup)
- B: Audit viewer (GET /api/audit/log + UI)
- C: Operations docs (DEPLOYMENT, BACKUP, OPERATIONS)
- D: Repo completeness (.gitignore, README)
