"""Shared GUI state definitions."""

from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class RunConfig:
    """User-provided configuration for a validation run."""

    source_url: Optional[str] = None
    target_url: Optional[str] = None
    config_path: Optional[str] = None
    include_schemas: List[str] = field(default_factory=list)
    exclude_schemas: List[str] = field(default_factory=list)
    rules_path: Optional[str] = None
    validate_objects: List[str] = field(default_factory=list)
    min_coverage: Optional[float] = None
    fail_on_findings: bool = True


@dataclass
class RunResult:
    """Results returned by the validation pipeline for UI rendering."""

    status: str
    coverage_pct: float
    compared: int
    total: int
    rule_hits: int
    mismatches: int
    missing: int
    fail_reasons: List[str] = field(default_factory=list)
    findings: dict = field(default_factory=dict)
    report_dir: Optional[str] = None

