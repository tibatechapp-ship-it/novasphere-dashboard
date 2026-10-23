"""Runbook engine — evaluates structured conditions (no eval, no exec)."""

import logging
from pathlib import Path

from app.core.config import get_settings
from app.schemas.insights import Runbook, RunbookStep
from runbooks.schema import RunbookSpec, load_runbooks

logger = logging.getLogger(__name__)


def _resolve_runbook_dir() -> Path:
    """Resolve runbooks directory — configurable, layout-independent."""
    s = get_settings()
    if s.runbooks_dir:
        return Path(s.runbooks_dir).expanduser().resolve()
    # Default: <repo_root>/runbooks relative to this file
    return Path(__file__).resolve().parents[2] / "runbooks"


_RUNBOOK_DIR = _resolve_runbook_dir()
_SPECS: list[RunbookSpec] | None = None


def _get_specs() -> list[RunbookSpec]:
    global _SPECS
    if _SPECS is None:
        _SPECS = load_runbooks(_RUNBOOK_DIR)
        logger.info("Loaded %d runbooks from %s", len(_SPECS), _RUNBOOK_DIR)
    return _SPECS


def _matches(condition: dict, metrics: dict, error_count: int) -> bool:
    """Structured condition evaluator — no eval, no user input."""
    mapping = {
        "cpu_gt": lambda v: metrics.get("cpu") is not None and metrics["cpu"] > v,
        "memory_gt": lambda v: metrics.get("mem") is not None and metrics["mem"] > v,
        "latency_ms_gt": lambda v: (
            metrics.get("latency_ms") is not None and metrics["latency_ms"] > v
        ),
        "rps_gt": lambda v: metrics.get("req_per_sec") is not None and metrics["req_per_sec"] > v,
        "error_events_gte": lambda v: error_count >= v,
    }
    for key, value in condition.items():
        if key not in mapping:
            return False
        if not mapping[key](value):
            return False
    return True


def select_runbooks(metrics: dict, error_count: int, platform: str = "generic") -> list[Runbook]:
    """Pick all matching runbooks (only the highest severity recommended)."""
    settings = get_settings()
    results: list[Runbook] = []

    for spec in _get_specs():
        if not _matches(spec.condition, metrics, error_count):
            continue

        # Filter steps by platform (generic always included)
        steps = [
            RunbookStep(
                step=s.step,
                command=s.command,
                platform_hint=s.platform_hint,
            )
            for s in spec.steps
            if s.platform_hint == "generic" or s.platform_hint == platform
        ]
        if not steps:
            continue

        action_url = None
        if spec.action_url_template and settings.remediation_platform_url:
            action_url = settings.remediation_platform_url.rstrip("/") + spec.action_url_template

        results.append(
            Runbook(
                title=spec.title,
                severity=spec.severity,
                steps=steps,
                action_url=action_url,
            )
        )

    # Sort: critical > error > warn > info
    order = {"critical": 0, "error": 1, "warn": 2, "info": 3}
    results.sort(key=lambda r: order.get(r.severity, 99))
    return results
