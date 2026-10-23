# Raqib — Real-time AI Analytics Dashboard

FastAPI + WebSocket + JWT + Smart Runbooks. Production-ready v0.3.1.

## Quick start (development)

```bash
./setup.sh
source .venv/bin/activate
alembic upgrade head
uvicorn app.main:app --reload --port 8080
```

Open http://localhost:8080

## Common commands

```bash
make help           # list all targets
make dev            # run with reload
make test           # pytest
make check          # lint + format + tests + bandit
make dod            # full Definition of Done
make docker-dev     # dev stack
make docker-prod    # prod stack
```

## Security boundary

Raqib never executes commands. Runbooks are read-only guidance.
Deep Links point to your automation platform (AWX/Rundeck/K8s).

## Documentation

- AGENT_BRIEF.md — phase-based execution contract
- SECURITY.md — threat model + disclosure
- CONTRIBUTING.md — dev workflow + PR checklist
- docs/RUNBOOKS.md — how to add a runbook
- docs/ADR/ — architecture decisions
- CHANGELOG.md — release history
