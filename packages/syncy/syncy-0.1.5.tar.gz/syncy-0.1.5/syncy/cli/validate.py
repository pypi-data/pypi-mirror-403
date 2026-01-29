from __future__ import annotations

import sys
from datetime import datetime
from typing import Any, Dict, List, Optional

import click

from .. import __version__
from .base import cli
from .utils import (
    DEFAULT_BEHAVIOUR_LIMIT,
    DEFAULT_BEHAVIOUR_TIMEOUT_S,
    LOCAL_TZ,
    _engine_info,
    _make_output_dir,
)
from ..core.connectors import MSSQLConnector, PostgresConnector
from ..core.report import generate_reports
from ..config.runtime import (
    load_yaml_config,
    resolve_connection_urls,
    resolve_validate_objects,
    OBJECT_TYPE_MAP,
    resolve_rule_pack,
)


@cli.command("validate")
@click.option("--source", "source_url", help="Source DB URL (e.g., mssql://...)")
@click.option("--target", "target_url", help="Target DB URL (e.g., postgresql://...)")
@click.option("--config", "config_path", help="Path to validator.yaml", default=None)
@click.option(
    "--out",
    "out_dir",
    help="Output directory base (timestamped subdir created).",
    default=None,
)
@click.option(
    "--include-schemas",
    "include_schemas",
    help="Comma-separated schemas to include",
    default=None,
)
@click.option(
    "--exclude-schemas",
    "exclude_schemas",
    help="Comma-separated schemas to exclude",
    default=None,
)
@click.option(
    "--rules",
    "rules_path",
    help="Path to rules YAML (or set 'rules' in validator.yaml)",
    default=None,
)
@click.option(
    "--objects",
    "validate_objects",
    help="Comma-separated objects to validate (tables,views,procedures,functions,triggers)",
    default=None,
)
@click.option(
    "--open/--no-open",
    "open_report",
    default=False,
    help="Open the HTML report after generation",
)
@click.option(
    "--min-coverage",
    "min_coverage",
    type=float,
    help="Fail if coverage percentage is below this threshold",
    default=None,
)
@click.option(
    "--fail-on-major/--no-fail-on-major",
    "fail_on_major",
    default=True,
    help="Exit non-zero if any findings exist (default: enabled)",
)
def validate(
    source_url: Optional[str],
    target_url: Optional[str],
    config_path: Optional[str],
    out_dir: Optional[str],
    include_schemas: Optional[str],
    exclude_schemas: Optional[str],
    rules_path: Optional[str],
    validate_objects: Optional[str],
    open_report: bool,
    min_coverage: Optional[float],
    fail_on_major: bool,
) -> None:
    """Validate migrated logic and schema objects between two engines.

    Safe mode: only executes read-only queries.
    """

    try:
        src_url, tgt_url = resolve_connection_urls(source_url, target_url, config_path)
    except click.ClickException:
        raise
    except Exception as exc:  # pragma: no cover
        raise click.ClickException(str(exc))

    out_path = _make_output_dir(out_dir)

    includes = [s.strip() for s in include_schemas.split(",") if s.strip()] if include_schemas else None
    excludes = [s.strip() for s in exclude_schemas.split(",") if s.strip()] if exclude_schemas else None
    if includes is None or excludes is None:
        cfg_scopes = load_yaml_config(config_path)
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

    validate_list, unknown_objs, src_label = resolve_validate_objects(
        validate_objects, config_path
    )
    if unknown_objs and src_label == "cli":
        raise click.ClickException(
            "Unknown object type(s): " + ", ".join(sorted(set(unknown_objs)))
        )
    if unknown_objs and src_label == "config":
        click.echo(
            "Warning: unknown validate objects in config: "
            + ", ".join(sorted(set(unknown_objs))),
            err=True,
        )
    if not validate_list:
        click.echo("Warning: no object types selected; nothing to validate.", err=True)

    if src_url.lower().startswith("mssql"):
        src = MSSQLConnector.from_url(src_url)
    elif src_url.lower().startswith("postgres"):
        src = PostgresConnector.from_url(src_url)
    else:
        raise click.ClickException("Unsupported source scheme. Use mssql:// or postgresql://")

    if tgt_url.lower().startswith("mssql"):
        tgt = MSSQLConnector.from_url(tgt_url)
    elif tgt_url.lower().startswith("postgres"):
        tgt = PostgresConnector.from_url(tgt_url)
    else:
        raise click.ClickException("Unsupported target scheme. Use mssql:// or postgresql://")

    from ..core.extractor import extract_catalog_mssql, extract_catalog_postgres
    from ..core.diff_engine import compare_catalogs

    def filter_catalog(catalog: Dict[str, Any]) -> Dict[str, Any]:
        if not validate_list:
            return {}
        allowed = set()
        for obj in validate_list:
            allowed.update(OBJECT_TYPE_MAP.get(obj, set()))
        return {k: v for k, v in catalog.items() if v.get("type") in allowed}

    click.echo("Extracting source catalog (read-only)...")
    if isinstance(src, MSSQLConnector):
        src_catalog = extract_catalog_mssql(src, includes, excludes)
    else:
        src_catalog = extract_catalog_postgres(src, includes, excludes)
    src_catalog = filter_catalog(src_catalog)

    click.echo("Extracting target catalog (read-only)...")
    if isinstance(tgt, MSSQLConnector):
        tgt_catalog = extract_catalog_mssql(tgt, includes, excludes)
    else:
        tgt_catalog = extract_catalog_postgres(tgt, includes, excludes)
    tgt_catalog = filter_catalog(tgt_catalog)

    cfg_rules = load_yaml_config(config_path)
    rules = resolve_rule_pack(rules_path, cfg_rules)

    click.echo("Comparing catalogs and applying rules...")
    comparison = compare_catalogs(src_catalog, tgt_catalog, rules)

    from ..core.behaviour import run_behaviour_tests

    behaviour = {}
    if "views" in validate_list:
        click.echo("Running behaviour tests (read-only samples)...")
        behaviour = run_behaviour_tests(
            src,
            tgt,
            src_catalog,
            tgt_catalog,
            sample_limit=DEFAULT_BEHAVIOUR_LIMIT,
            timeout_s=DEFAULT_BEHAVIOUR_TIMEOUT_S,
        )
    else:
        click.echo("Skipping behaviour tests (views not selected).")

    src_info = _engine_info(src)
    tgt_info = _engine_info(tgt)

    results: Dict[str, Any] = {
        "version": __version__,
        "runtime_utc": datetime.now(LOCAL_TZ).isoformat(),
        "source_url": src.redacted_url,
        "target_url": tgt.redacted_url,
        "source_info": src_info,
        "target_info": tgt_info,
        "coverage": comparison.get("coverage", {}),
        "findings": comparison.get("findings", {}),
        "behaviour": behaviour,
        "finding_counts": comparison.get("finding_counts", {}),
        "status": comparison.get("status", "unknown"),
        "rules_source": (
            rules_path
            or (
                cfg_rules.get("rules")
                if isinstance(cfg_rules.get("rules"), str)
                else ("inline" if isinstance(cfg_rules.get("rules"), list) else "built-in")
            )
        ),
        "params": {
            "include_schemas": includes,
            "exclude_schemas": excludes,
            "validate_objects": validate_list,
            "behaviour_limit": DEFAULT_BEHAVIOUR_LIMIT,
            "behaviour_timeout_s": DEFAULT_BEHAVIOUR_TIMEOUT_S,
        },
    }

    reasons: List[str] = []
    finding_counts = results.get("finding_counts", {}) or {}
    rule_hits = int(finding_counts.get("rule_hits", 0))
    mismatches = int(finding_counts.get("mismatches", 0))
    missing = int(finding_counts.get("missing", 0))
    total_findings = rule_hits + mismatches + missing
    if fail_on_major and total_findings > 0:
        reasons.append(f"{total_findings} finding(s)")
    cov_pct = float(results.get("coverage", {}).get("coverage_pct", 0.0) or 0.0)
    if min_coverage is not None and cov_pct < float(min_coverage):
        reasons.append(f"coverage {cov_pct:.2f}% < min {float(min_coverage):.2f}%")

    results["thresholds"] = {
        "fail_on_findings": fail_on_major,
        "min_coverage": min_coverage,
        "fail_reasons": reasons,
    }

    generate_reports(results, out_path)

    click.echo(f"Reports written to: {out_path}")

    coverage = results.get("coverage", {}) or {}
    status = results.get("status", "unknown")
    status_label = click.style(status.upper(), fg="green" if status == "pass" else "red", bold=True)
    cov_pct = float(coverage.get("coverage_pct", 0.0) or 0.0)
    cov_line = f"Coverage: {cov_pct:.2f}% ({coverage.get('compared_objects', 0)}/{coverage.get('total_objects', 0)})"
    findings_line = f"Findings: Rules {rule_hits} | Mismatch {mismatches} | Missing {missing}"
    if reasons:
        thresh_line = click.style("Thresholds: FAILED — " + "; ".join(str(r) for r in reasons), fg="red")
    else:
        thresh_line = click.style("Thresholds: OK", fg="green")

    click.echo("\nSummary:")
    click.echo(f"- Status: {status_label}")
    click.echo(f"- {cov_line}")
    click.echo(f"- {findings_line}")
    click.echo(f"- {thresh_line}")

    findings = results.get("findings", {}) or {}
    status_colors = {
        "match": "green",
        "equivalent_with_rules": "yellow",
        "mismatch": "red",
        "missing_in_source": "red",
        "missing_in_target": "red",
    }
    if findings:
        click.echo("- All findings:")
        for obj_key in sorted(findings.keys()):
            item = findings[obj_key] or {}
            st = str(item.get("status", "unknown"))
            st_label = click.style(st, fg=status_colors.get(st, "white"), bold=(st != "match"))
            rules_str = "-"
            if item.get("rules"):
                rules_str = "; ".join(
                    f"{r.get('id','?')} {r.get('desc','')}"
                    for r in item.get("rules", [])
                )
            click.echo(f"  \u2022 {obj_key}: {st_label} | {rules_str}")
    click.echo("")

    if open_report:
        try:
            import webbrowser

            html_uri = (out_path / "index.html").resolve().as_uri()
            webbrowser.open(html_uri)
        except Exception:
            pass

    if reasons:
        click.echo("Validation failed thresholds: " + "; ".join(reasons), err=True)
        sys.exit(2)
    else:
        sys.exit(0)


__all__ = ["validate"]
