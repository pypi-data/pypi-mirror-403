# Copyright (c) 2026 Celestir LLC
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Configuration models for GridSeal."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


class VerificationConfig(BaseModel):
    """
    Configuration for the verification engine.

    Attributes:
        checks: List of check names to run (e.g., ["grounding", "confidence"])
        threshold: Default score threshold for all checks (0.0 to 1.0)
        on_fail: Action when checks fail
            - "log": Silent logging only
            - "flag": Log warning and add to flags
            - "block": Raise VerificationError
    """

    checks: list[str] = Field(
        default=["grounding"],
        description="List of verification checks to run",
    )
    threshold: float = Field(
        default=0.7,
        ge=0.0,
        le=1.0,
        description="Default score threshold for passing checks",
    )
    on_fail: Literal["log", "flag", "block"] = Field(
        default="flag",
        description="Action when verification fails",
    )
    thresholds: dict[str, float] = Field(
        default_factory=dict,
        description="Per-check threshold overrides",
    )

    def get_threshold(self, check_name: str) -> float:
        """Get threshold for a specific check."""
        return self.thresholds.get(check_name, self.threshold)


class AuditConfig(BaseModel):
    """
    Configuration for the audit store.

    Attributes:
        backend: Storage backend ("sqlite", "postgresql", "memory")
        path: Path for SQLite database file
        connection: Connection string for PostgreSQL
        retention_days: How long to keep records (default: 7 years)
    """

    backend: Literal["sqlite", "postgresql", "memory"] = Field(
        default="sqlite",
        description="Storage backend type",
    )
    path: str = Field(
        default="./gridseal_audit.db",
        description="Path for SQLite database",
    )
    connection: str | None = Field(
        default=None,
        description="PostgreSQL connection string",
    )
    retention_days: int = Field(
        default=2555,
        ge=1,
        description="Audit record retention period in days",
    )


class GridSealConfig(BaseModel):
    """
    Top-level GridSeal configuration.

    Attributes:
        mode: Operating mode
            - "standalone": Full verification + tracing
            - "adapter": Adds compliance to existing observability
        verification: Verification engine configuration
        audit: Audit store configuration
    """

    mode: Literal["standalone", "adapter"] = Field(
        default="standalone",
        description="Operating mode",
    )
    verification: VerificationConfig = Field(default_factory=VerificationConfig)
    audit: AuditConfig = Field(default_factory=AuditConfig)

    model_config = {"extra": "forbid"}


def parse_config(
    mode: str | None = None,
    verification: dict[str, Any] | VerificationConfig | None = None,
    audit: dict[str, Any] | AuditConfig | None = None,
) -> GridSealConfig:
    """
    Parse configuration from various input formats.

    Accepts dicts or config objects, returns validated GridSealConfig.
    """
    from typing import Any

    if isinstance(verification, dict):
        verification = VerificationConfig(**verification)
    if isinstance(audit, dict):
        audit = AuditConfig(**audit)

    return GridSealConfig(
        mode=mode or "standalone",  # type: ignore[arg-type]
        verification=verification or VerificationConfig(),
        audit=audit or AuditConfig(),
    )
