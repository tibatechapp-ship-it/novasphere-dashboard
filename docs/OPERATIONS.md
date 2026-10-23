# Operations Runbook

## Daily checks
```bash
curl -s https://raqib.example.com/health
docker compose -f docker-compose.prod.yml ps
df -h /var/lib/docker
```

## Weekly
- Review Grafana dashboard
- Check audit_log growth: SELECT COUNT(*) FROM audit_log;
- Check failed logins

## Common incidents

### WebSocket shows "منقطع"
1. Verify app: curl /health
2. Check proxy config for /ws block
3. Check app logs: docker logs raqib-app --tail 50

### Rate limit too aggressive/lax
Edit .env: LEGACY_RATE_LIMIT_REQUESTS, LEGACY_RATE_LIMIT_WINDOW_SECONDS

### Audit log huge
```bash
docker exec -it raqib-postgres psql -U raqib -d raqib_db -c "DELETE FROM audit_log WHERE ts < NOW() - INTERVAL '90 days';"
```

### Emergency stop
```bash
docker compose -f docker-compose.prod.yml down
# DESTRUCTIVE:
docker compose -f docker-compose.prod.yml down -v
```

## Log locations
- App: docker logs raqib-app -f
- Postgres: docker logs raqib-postgres -f
- Redis: docker logs raqib-redis -f

## Metrics endpoints
- /health — JSON liveness
- /metrics — Prometheus text
- /api/events — Auth required
- /api/insights — Auth required
- /api/audit/log — Auth required, self only
