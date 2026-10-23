#!/usr/bin/env bash
# Raqib setup — idempotent, safe, no destructive ops.
set -euo pipefail

cd "$(dirname "$0")"

log()  { printf "\033[1;34m[%s]\033[0m %s\n" "$(date +%H:%M:%S)" "$*"; }
ok()   { printf "\033[1;32m[ OK ]\033[0m %s\n" "$*"; }
warn() { printf "\033[1;33m[WARN]\033[0m %s\n" "$*"; }
die()  { printf "\033[1;31m[FAIL]\033[0m %s\n" "$*" >&2; exit 1; }

# ---- 1. Python version ----
PY=$(command -v python3 || die "python3 not found")
$PY - <<'PYCHK' || die "Python 3.11+ required"
import sys
sys.exit(0 if sys.version_info >= (3, 11) else 1)
PYCHK
ok "Python >= 3.11"

# ---- 2. Virtualenv ----
if [ ! -d .venv ]; then
    log "creating .venv"
    $PY -m venv .venv
fi
# shellcheck disable=SC1091
source .venv/bin/activate
ok "venv active"

# ---- 3. Install ----
log "installing dependencies (idempotent)"
pip install --upgrade pip -q
pip install -q -r requirements.txt
ok "dependencies installed"

# ---- 4. .env ----
if [ ! -f .env ]; then
    cp .env.example .env
    SECRET=$($PY -c "import secrets; print(secrets.token_urlsafe(32))")
    $PY - "$SECRET" <<'PYENV'
import sys, pathlib
p = pathlib.Path(".env")
s = p.read_text()
s = s.replace("dev-only-insecure-secret-change-me-32chars-min", sys.argv[1])
p.write_text(s)
PYENV
    ok ".env created with random JWT secret"
else
    ok ".env already exists"
fi

# ---- 5. Migrations ----
log "applying alembic migrations"
alembic upgrade head
ok "database ready"

# ---- 6. Optional: create initial user ----
if [ "${1:-}" = "--with-user" ]; then
    read -rp "username: " U
    read -rsp "password: " P; echo

    # SECURITY: pass credentials via argv, NEVER via string interpolation.
    "$PY" - "$U" "$P" <<'PYCREATE'
import sys
from app.db.session import SessionLocal
from app.api.auth import _create_user

username, password = sys.argv[1], sys.argv[2]
db = SessionLocal()
try:
    _create_user(db, username, password)
    print(f"user created: {username}")
except Exception as e:
    print(f"user creation failed: {e}", file=sys.stderr)
    sys.exit(1)
finally:
    db.close()
PYCREATE
fi

ok "setup complete"
cat <<'NEXT'

Next steps:
  source .venv/bin/activate
  uvicorn app.main:app --reload --port 8080
  open http://localhost:8080

Production:
  docker compose -f docker-compose.prod.yml up -d --build
NEXT