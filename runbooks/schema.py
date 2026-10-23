"""Pydantic schema for runbook YAML validation."""

from pathlib import Path
from typing import Literal

import yaml
from pydantic import BaseModel, Field, ValidationError

Severity = Literal["info", "warn", "error", "critical"]
Platform = Literal["linux", "kubernetes", "generic"]


class RunbookStepSpec(BaseModel):
    step: str = Field(min_length=5, max_length=500)
    command: str | None = Field(default=None, max_length=500)
    platform_hint: Platform = "generic"


class RunbookSpec(BaseModel):
    id: str = Field(pattern=r"^[a-z0-9_\-]+$", max_length=100)
    title: str = Field(min_length=5, max_length=200)
    severity: Severity
    condition: dict
    steps: list[RunbookStepSpec] = Field(min_length=1)
    action_url_template: str | None = None


def load_runbooks(directory: Path) -> list[RunbookSpec]:
    """Load and validate all *.yml in directory. Raises on invalid spec."""
    specs: list[RunbookSpec] = []
    for path in sorted(directory.glob("*.yml")):
        with path.open("r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
        try:
            specs.append(RunbookSpec(**data))
        except ValidationError as exc:
            raise RuntimeError(f"Invalid runbook {path.name}: {exc}") from exc
    return specs
