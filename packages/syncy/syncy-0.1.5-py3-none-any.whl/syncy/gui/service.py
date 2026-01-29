"""Service layer to run validation without invoking the CLI directly.

This wraps the existing syncy validation pipeline so the GUI can call it
programmatically and render the returned summary.
"""

from __future__ import annotations

from datetime import datetime, timezone, timedelta
from typing import Optional

from .. import __version__
from ..cli import (
    DEFAULT_BEHAVIOUR_LIMIT,
    DEFAULT_BEHAVIOUR_TIMEOUT_S,
    _engine_info,
    _make_output_dir,
)
from ..config.runtime import (
    load_yaml_config,
    resolve_connection_urls,
    resolve_rule_pack,
    resolve_validate_objects,
    OBJECT_TYPE_MAP,
    VALIDATE_OBJECTS,
)
from ..core.behaviour import run_behaviour_tests
from ..core.connectors import MSSQLConnector, PostgresConnector
from ..core.diff_engine import compare_catalogs
from ..core.extractor import extract_catalog_mssql, extract_catalog_postgres
from ..core.report import generate_reports
from .state import RunConfig, RunResult


def run_validation(cfg: RunConfig) -> RunResult:
    """Execute a validation run and return a condensed result for the UI."""
    # Resolve connection URLs (same precedence as CLI)
    src_url, tgt_url = resolve_connection_urls(cfg.source_url, cfg.target_url, cfg.config_path)
    validate_list = list(cfg.validate_objects or [])
    if not validate_list:
        validate_list, _unknown, _src = resolve_validate_objects(None, cfg.config_path)
    if not validate_list:
        validate_list = list(VALIDATE_OBJECTS)

    out_path = _make_output_dir(None)

    includes = cfg.include_schemas or None
    excludes = cfg.exclude_schemas or None
    if includes is None or excludes is None:
        cfg_scopes = load_yaml_config(cfg.config_path)
        if includes is None:
            inc = cfg_scopes.get("include_schemas")
            if isinstance(inc, list):
                includes = [str(s) for s in inc]
            elif isinstance(inc, str):
                includes = [s.strip() for s in inc.split(",") if s.strip()]
        if excludes is None:
            exc = cfg_scopes.get("exclude_schemas")
            if isinstance(exc, list):
                excludes = [str(s) for s in exc]
            elif isinstance(exc, str):
                excludes = [s.strip() for s in exc.split(",") if s.strip()]

    def filter_catalog(catalog: dict) -> dict:
        if not validate_list:
            return {}
        allowed = set()
        for obj in validate_list:
            allowed.update(OBJECT_TYPE_MAP.get(obj, set()))
        return {k: v for k, v in catalog.items() if v.get("type") in allowed}

    # Initialize connectors
    src = MSSQLConnector.from_url(src_url) if src_url.lower().startswith("mssql") else PostgresConnector.from_url(src_url)
    tgt = MSSQLConnector.from_url(tgt_url) if tgt_url.lower().startswith("mssql") else PostgresConnector.from_url(tgt_url)

    # Extract catalogs
    if isinstance(src, MSSQLConnector):
        src_catalog = extract_catalog_mssql(src, includes, excludes)
    else:
        src_catalog = extract_catalog_postgres(src, includes, excludes)
    if isinstance(tgt, MSSQLConnector):
        tgt_catalog = extract_catalog_mssql(tgt, includes, excludes)
    else:
        tgt_catalog = extract_catalog_postgres(tgt, includes, excludes)
    src_catalog = filter_catalog(src_catalog)
    tgt_catalog = filter_catalog(tgt_catalog)

    # Resolve rules
    cfg_rules = load_yaml_config(cfg.config_path)
    rules = resolve_rule_pack(cfg.rules_path, cfg_rules)

    # Compare and run behaviour tests
    comparison = compare_catalogs(src_catalog, tgt_catalog, rules)
    behaviour = {}
    if "views" in validate_list:
        behaviour = run_behaviour_tests(
            src,
            tgt,
            src_catalog,
            tgt_catalog,
            sample_limit=DEFAULT_BEHAVIOUR_LIMIT,
            timeout_s=DEFAULT_BEHAVIOUR_TIMEOUT_S,
        )

    # Summarize and write reports
    results = {
        "version": __version__,
        "runtime_utc": datetime.now(timezone.utc).isoformat(),
        "source_url": src.redacted_url,
        "target_url": tgt.redacted_url,
        "source_info": _engine_info(src),
        "target_info": _engine_info(tgt),
        "coverage": comparison.get("coverage", {}),
        "findings": comparison.get("findings", {}),
        "behaviour": behaviour,
        "finding_counts": comparison.get("finding_counts", {}),
        "status": comparison.get("status", "unknown"),
        "params": {
            "include_schemas": includes,
            "exclude_schemas": excludes,
            "validate_objects": validate_list,
            "behaviour_limit": DEFAULT_BEHAVIOUR_LIMIT,
            "behaviour_timeout_s": DEFAULT_BEHAVIOUR_TIMEOUT_S,
        },
        "thresholds": {
            "fail_on_findings": cfg.fail_on_findings,
            "min_coverage": cfg.min_coverage,
            "fail_reasons": [],
        },
    }

    generate_reports(results, out_path)

    cov = results["coverage"]
    counts = results["finding_counts"]
    reasons = results["thresholds"]["fail_reasons"]
    status = results.get("status", "unknown")

    # Apply threshold logic to capture user intent
    rule_hits = int(counts.get("rule_hits", 0))
    mismatches = int(counts.get("mismatches", 0))
    missing = int(counts.get("missing", 0))
    total_findings = rule_hits + mismatches + missing
    if cfg.fail_on_findings and total_findings > 0:
        reasons.append(f"{total_findings} finding(s)")
    cov_pct = float(cov.get("coverage_pct", 0.0) or 0.0)
    if cfg.min_coverage is not None and cov_pct < float(cfg.min_coverage):
        reasons.append(f"coverage {cov_pct:.2f}% < min {float(cfg.min_coverage):.2f}%")

    display_status = "fail" if reasons else status

    return RunResult(
        status=display_status,
        coverage_pct=cov_pct,
        compared=int(cov.get("compared_objects", 0)),
        total=int(cov.get("total_objects", 0)),
        rule_hits=rule_hits,
        mismatches=mismatches,
        missing=missing,
        fail_reasons=reasons,
        findings=results.get("findings", {}),
        report_dir=str(out_path),
    )
