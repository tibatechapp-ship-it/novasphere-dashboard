# ADR 0001 — Runbooks are read-only

## Context
Raqib needed actionable guidance when anomalies fire. Options ranged
from direct in-app remediation (execute shell commands) to read-only
guidance (steps + Deep Links to external automation platforms).

## Decision
Runbooks are strictly read-only. No HTTP/WebSocket input may reach
any execution context. Every command is displayed as UI text only.
If a step requires execution, the runbook provides an action_url
pointing to an external platform (AWX/Rundeck/K8s).

## Consequences
- Preserves v0.2.0 security posture: JWT theft cannot escalate to RCE.
- Platform-agnostic — same runbook works for Linux, K8s, ECS.
- Auditable — every action click is logged via audit_log.
