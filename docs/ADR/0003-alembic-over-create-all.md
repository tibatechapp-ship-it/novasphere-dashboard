# ADR 0003 — Alembic over create_all in production

## Context
Base.metadata.create_all() is fast for dev but provides no upgrade path.

## Decision
Alembic runs at startup via alembic upgrade head. If migrations are
missing, fall back to create_all() only when ENV != production.

## Consequences
- Versioned, reversible schema changes.
- Migration history in Git — auditable diffs.
