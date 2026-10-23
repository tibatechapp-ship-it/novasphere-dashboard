#!/usr/bin/env bash
# Static regression guard: fails if ws.py reverts to leak-prone patterns.
set -euo pipefail
cd "$(dirname "$0")/.."

WS_FILE="app/api/ws.py"
FAIL=0

echo "── WebSocket leak guard ──"

# 1) Forbid long asyncio.sleep in the WS handler loop
if grep -nE "asyncio\.sleep\s*\(\s*(3600|[0-9]{4,})" "$WS_FILE" >/dev/null 2>&1; then
    echo "❌ ws.py uses long asyncio.sleep — disconnects go undetected"
    FAIL=1
else
    echo "✅ no long sleep in ws.py"
fi

# 2) Require ws.receive() in the handler
if ! grep -qE "await\s+ws\.receive" "$WS_FILE"; then
    echo "❌ ws.py does not call await ws.receive() — cannot detect disconnect"
    FAIL=1
else
    echo "✅ ws.receive() present"
fi

# 3) Require disconnect in a finally block
if ! awk '/finally:/{f=1} f && /manager\.disconnect/{found=1; exit} END{exit (found ? 0 : 1)}' "$WS_FILE"; then
    echo "❌ manager.disconnect must be in a finally block"
    FAIL=1
else
    echo "✅ disconnect in finally"
fi

if [ "$FAIL" -eq 0 ]; then
    echo "✅ WebSocket leak guard passed"
fi
exit "$FAIL"