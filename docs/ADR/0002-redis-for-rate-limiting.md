# ADR 0002 — Redis-backed rate limiting

## Context
In-memory rate limiting works for a single process but breaks under
horizontal scaling.

## Decision
Use slowapi + Redis storage for a single shared limiter across replicas.
Fall back to memory in dev when Redis is unavailable.

## Consequences
- Correct quotas across N replicas.
- Adds Redis as a runtime dependency.
