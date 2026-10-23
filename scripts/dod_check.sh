#!/usr/bin/env bash
# Definition of Done — run before opening a release PR.
set -euo pipefail
cd "$(dirname "$0")/.."

pass=0; fail=0
check() {
    local name="$1"; shift
    if "$@" >/dev/null 2>&1; then
        printf "✅  %s\n" "$name"; pass=$((pass+1))
    else
        printf "❌  %s\n" "$name"; fail=$((fail+1))
    fi
}

echo "── DoD checklist ──"
check "ruff check"          ruff check .
check "ruff format --check" ruff format --check .
check "pytest ≥85% cov"     pytest --cov=app --cov-fail-under=85 -q
check "bandit (HIGH)"       bandit -r app/ -lll -q -x tests
check "alembic current"     alembic current
check "no subprocess/os.system" bash -c "! grep -rEn 'subprocess\.|os\.system|os\.popen' app/"
check "no eval/exec"            bash -c "! grep -rEn '\b(eval|exec)\(' app/ --include='*.py'"
check "no shell=True"           bash -c "! grep -rn 'shell=True' app/"
check "no allow_origins=*"      bash -c "! grep -rn 'allow_origins=\\[\"\\*\"\\]' app/"
check "ws leak guard"            bash ./scripts/check_ws_leak_guard.sh

if [ "$fail" -gt 0 ]; then
    echo; echo "$fail check(s) failed." >&2; exit 1
fi
echo; echo "All $pass checks passed."