from __future__ import annotations

"""Validation data transfer objects.

These types define the standard shape for validation results across the system
(compiler, preflight, runtime checks).
"""

from typing import Literal, Optional

from pydantic import BaseModel, Field

ValidationSeverity = Literal["error", "warning", "info"]


class ValidationLocation(BaseModel):
    node_id: Optional[str] = None
    field: Optional[str] = None

    model_config = {"extra": "forbid"}


class ValidationIssue(BaseModel):
    severity: ValidationSeverity
    code: str
    message: str
    location: ValidationLocation = Field(default_factory=ValidationLocation)

    model_config = {"extra": "forbid"}


class ValidationReport(BaseModel):
    ok: bool
    issues: list[ValidationIssue] = Field(default_factory=list)

    model_config = {"extra": "forbid"}
