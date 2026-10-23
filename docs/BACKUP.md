# Backup & Restore

## What to back up
- PostgreSQL (users, events, audit_log) — CRITICAL
- .env (secrets) — CRITICAL (offline only)
- Redis (rate limits) — rebuilds on restart
- Grafana dashboards — re-provisioned on start

## Daily backup (cron)
```bash
#!/bin/bash
set -euo pipefail
BACKUP_DIR=/var/backups/raqib
DATE=$(date +%Y%m%d-%H%M%S)
mkdir -p "$BACKUP_DIR"
docker exec raqib-postgres pg_dump -U raqib -Fc raqib_db > "$BACKUP_DIR/db-$DATE.dump"
find "$BACKUP_DIR" -name 'db-*.dump' -mtime +30 -delete
```

## Restore
```bash
docker compose -f docker-compose.prod.yml stop raqib
docker exec -it raqib-postgres psql -U raqib -d raqib_db -c "DROP SCHEMA public CASCADE; CREATE SCHEMA public;"
docker exec -i raqib-postgres pg_restore -U raqib -d raqib_db < /var/backups/raqib/db-YYYYMMDD-HHMMSS.dump
docker compose -f docker-compose.prod.yml start raqib
```

## Disaster recovery
- Lost .env: users re-authenticate (JWTs invalidate), passwords remain valid.
- Lost pg volume: restore from backup. If no backup, all data lost.
- Lost rd volume: no data loss, rate limits reset.

## Encryption
Store backups on encrypted volumes or encrypt dumps: gpg --symmetric --cipher-algo AES256 db-X.dump
