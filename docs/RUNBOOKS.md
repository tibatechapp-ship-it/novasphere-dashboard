# Runbooks Developer Guide

## How to add a runbook

1. Create a YAML file in runbooks/ following schema.py
2. Define: title, severity, conditions, steps, action_url
3. Steps: step (text), command (optional), platform_hint (linux/kubernetes/generic)
4. Platform-neutral: use platform_hint to filter steps per environment
5. No eval/exec — conditions use structured matching only

## Schema
```yaml
title: "CPU Critical"
severity: critical
conditions:
  - metric: cpu
    operator: ">"
    threshold: 90
steps:
  - step: "Check top processes"
    command: "top -o %CPU"
    platform_hint: linux
  - step: "Verify recovery"
    command: "curl -s localhost:8080/health"
    platform_hint: generic
action_url: "https://awx.example.com/runbook/cpu_critical"
```

## Important
- Runbooks are READ-ONLY (UI text only, no execution)
- Deep Links point to external automation platforms
- See ADR/0001-runbooks-are-read-only.md
