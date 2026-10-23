"""Background mock data generator for development."""

import asyncio
import logging
import random
import time
from typing import Any

from app.core.config import get_settings
from app.db.session import SessionLocal
from app.models.event import Event

logger = logging.getLogger(__name__)

AGENTS = [
    {"id": "A01", "name": "Profiler", "group": "core"},
    {"id": "A02", "name": "Analyst", "group": "core"},
    {"id": "A03", "name": "Monitor", "group": "ops"},
    {"id": "A04", "name": "Reporter", "group": "ops"},
]

_MSG_POOL = [
    ("Agent A03 completed task #42", "info", "info"),
    ("WebSocket client connected", "info", "info"),
    ("CPU spike detected", "warn", "warn"),
    ("Memory threshold 80%", "warn", "warn"),
    ("New agent registered", "info", "info"),
    ("Task queue drained", "info", "info"),
    ("Connection timeout to database", "error", "error"),
    ("Service crashed unexpectedly", "error", "critical"),
]


def generate_snapshot() -> dict[str, Any]:
    """Generate a single metrics + events snapshot."""
    cpu = round(random.uniform(5, 95), 1)
    mem = round(random.uniform(20, 85), 1)
    rps = random.randint(10, 400)
    lat = random.randint(5, 120)

    events = []
    for _ in range(5):
        msg, level, severity = random.choice(_MSG_POOL)
        events.append(
            {
                "ts": time.time() - random.uniform(0, 30),
                "level": level,
                "severity": severity,
                "msg": msg,
            }
        )

    return {
        "ts": time.time(),
        "cpu": cpu,
        "mem": mem,
        "req_per_sec": rps,
        "latency_ms": lat,
        "agents": [
            {
                "id": a["id"],
                "name": a["name"],
                "group": a["group"],
                "status": random.choice(["online", "online", "online", "busy", "idle"]),
                "load": random.randint(0, 100),
                "tasks": random.randint(0, 50),
            }
            for a in AGENTS
        ],
        "events": events,
    }


async def background_generator(manager) -> None:
    """Broadcast a fresh snapshot every second."""
    if not get_settings().mock_data:
        logger.info("MOCK_DATA=false — background generator disabled")
        return

    logger.info("Starting background data generator")
    while True:
        payload = generate_snapshot()

        # Persist 2 events per tick
        try:
            db = SessionLocal()
            for ev in payload["events"][:2]:
                db.add(
                    Event(
                        level=ev["level"],
                        severity=ev.get("severity", "info"),
                        message=ev["msg"],
                        metric_cpu=payload["cpu"],
                        metric_mem=payload["mem"],
                        metric_rps=payload["req_per_sec"],
                    )
                )
            db.commit()
            db.close()
        except Exception as exc:
            logger.error("Background DB write failed: %s", exc)

        await manager.broadcast(payload)
        await asyncio.sleep(1.0)
