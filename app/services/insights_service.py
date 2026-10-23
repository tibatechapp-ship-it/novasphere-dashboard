"""Heuristic insights engine — delegates runbook generation to YAML specs."""

from app.schemas.insights import InsightsRequest, InsightsResponse
from app.services.runbook_engine import select_runbooks


def analyze(payload: InsightsRequest) -> InsightsResponse:
    last = payload.events[-10:]
    metrics = payload.metrics

    levels: dict[str, int] = {}
    for ev in last:
        lvl = ev.get("level", "info")
        levels[lvl] = levels.get(lvl, 0) + 1

    error_count = levels.get("error", 0)

    insights: list[str] = []
    if metrics.get("cpu") and metrics["cpu"] > 90:
        insights.append(f"CPU حرج ({metrics['cpu']}%) — يتطلب تدخل فوري")
    if metrics.get("mem") and metrics["mem"] > 90:
        insights.append(f"ذاكرة حرجة ({metrics['mem']}%) — خطر OOM")
    if metrics.get("latency_ms") and metrics["latency_ms"] > 100:
        insights.append(f"زمن استجابة مرتفع ({metrics['latency_ms']}ms)")
    if metrics.get("req_per_sec") and metrics["req_per_sec"] > 350:
        insights.append(f"إنتاجية عالية ({metrics['req_per_sec']} req/s)")
    if error_count > 0:
        insights.append(f"تم رصد {error_count} خطأ في آخر {len(last)} أحداث")
    if not insights:
        insights.append("النظام يعمل بشكل طبيعي — لا توجد شذوذ")

    # Runbooks: include platform from payload if provided
    platform = (payload.metrics.get("platform") or "generic").lower()
    if platform not in ("linux", "kubernetes", "generic"):
        platform = "generic"

    candidates = select_runbooks(metrics, error_count, platform=platform)
    top_runbook = candidates[0] if candidates else None

    return InsightsResponse(
        summary=" | ".join(insights),
        insights=insights,
        runbook=top_runbook,
        stats={
            "events": len(last),
            "levels": levels,
            "cpu": metrics.get("cpu"),
            "mem": metrics.get("mem"),
            "rps": metrics.get("req_per_sec"),
            "latency": metrics.get("latency_ms"),
            "runbooks_matched": len(candidates),
        },
    )
