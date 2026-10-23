# Deployment Guide

## Prerequisites

- Docker 24+ and Docker Compose v2
- A reverse proxy (nginx, traefik, or Caddy)
- 2 GB RAM minimum, 4 GB recommended
- PostgreSQL 16+ (bundled in compose, or external)

## Quick start (production)

```bash
git clone https://github.com/tibatechapp-ship-it/raqib.git
cd raqib
cp .env.example .env
# Set: ENV=production, JWT_SECRET_KEY, POSTGRES_PASSWORD, REDIS_PASSWORD, GRAFANA_ADMIN_PASSWORD
docker compose -f docker-compose.prod.yml up -d --build
```

## Verification

```bash
curl -s http://localhost:8080/health
curl -s http://localhost:8080/metrics | head -3
docker compose -f docker-compose.prod.yml ps
```

## Reverse proxy (REQUIRED)

docker-compose.prod.yml does not expose ports. Front with Caddy or nginx.
See full guide in original delivery for Caddy/nginx config examples.

## Upgrade

```bash
git fetch origin && git checkout v0.4.1
docker compose -f docker-compose.prod.yml down
docker compose -f docker-compose.prod.yml up -d --build
```

alembic upgrade head runs automatically on startup.

## Common pitfalls

- POSTGRES_PASSWORD is required — docker-compose uses ${VAR:?} syntax
- WebSocket needs /ws upgrade headers in reverse proxy
- alembic fails if DB user lacks DDL rights
