from __future__ import annotations

import re
from typing import Dict, List, Tuple


Catalog = Dict[str, dict]


def _normalize_sql(text: str) -> str:
    s = text or ""
    s = s.replace("[", '"').replace("]", '"')
    s = re.sub(r"\s+", " ", s).strip().lower()
    return s


def _apply_rules(src_sql: str, tgt_sql: str, rules: List[dict]) -> List[dict]:
    findings: List[dict] = []
    s = _normalize_sql(src_sql)
    t = _normalize_sql(tgt_sql)

    def _hint_of(rules: List[dict], rid: str) -> str:
        for r in rules:
            if r.get("id") == rid:
                return r.get("hint", "")
        return ""

    def add(rule_id: str, desc: str) -> None:
        hint = _hint_of(rules, rule_id)
        row = {"id": rule_id, "desc": desc}
        if hint:
            row["hint"] = hint
        findings.append(row)

    # R01: TOP vs LIMIT
    if ("select top" in s) != (" limit " in t):
        add("R01", "TOP vs LIMIT")

    # R02: ISNULL vs COALESCE
    if ("isnull(" in s) != ("coalesce(" in t):
        add("R02", "ISNULL() vs COALESCE()")

    # R03: IDENTITY vs SEQUENCE/IDENTITY
    if (" identity(" in s) and not ("generated" in t or "nextval(" in t or "identity" in t):
        add("R03", "IDENTITY vs SEQUENCE")

    # R04: BIT vs BOOLEAN
    if (" bit" in s) and (" boolean" not in t):
        add("R04", "BIT vs BOOLEAN")

    # R05: DATETIME vs TIMESTAMP
    if (" datetime" in s) and (" timestamp" not in t):
        add("R05", "DATETIME vs TIMESTAMP")

    # R06: NVARCHAR length mismatch (heuristic)
    if "nvarchar(" in s and "varchar(" in t:
        add("R06", "NVARCHAR length mismatch")

    # R07: UUID vs UNIQUEIDENTIFIER
    if ("uniqueidentifier" in s) and ("uuid" not in t):
        add("R07", "UUID vs UNIQUEIDENTIFIER")

    # R08: Collation differences
    if (" collate " in s) != (" collate " in t):
        add("R08", "Collation differences")

    # R09: Trigger timing mismatch
    if (" instead of " in s) and not (" before " in t or " after " in t):
        add("R09", "Trigger timing mismatch")

    # R10: Function name mismatch (common LEN vs length)
    if (" len(" in s) and (" length(" not in t):
        add("R10", "Function name mismatch")

    return findings


def compare_catalogs(src: Catalog, tgt: Catalog, rules: List[dict]) -> Dict[str, object]:
    """Compare normalized catalogs and apply rule pack.

    Returns summary with coverage, status, finding counts, and per-object findings.
    """
    all_keys = set(src.keys()) | set(tgt.keys())
    src_tables = {k for k, v in src.items() if v.get("type") == "table"}
    tgt_tables = {k for k, v in tgt.items() if v.get("type") == "table"}
    findings: Dict[str, dict] = {}
    rule_hits_total = 0
    mismatch_count = 0
    missing_count = 0
    matched = 0
    compared = 0

    def _skip_column_due_to_parent(key: str, s_obj: dict | None, t_obj: dict | None) -> bool:
        obj = s_obj or t_obj
        if not obj or obj.get("type") != "column":
            return False
        parent = obj.get("table_key")
        if not parent:
            return False
        return parent not in src_tables or parent not in tgt_tables

    processed_keys: List[str] = []
    for key in sorted(all_keys):
        s_obj = src.get(key)
        t_obj = tgt.get(key)
        if _skip_column_due_to_parent(key, s_obj, t_obj):
            continue
        processed_keys.append(key)
        entry = {"status": None, "rules": []}  # type: ignore[assignment]

        if s_obj and not t_obj:
            entry["status"] = "missing_in_target"
            missing_count += 1
        elif t_obj and not s_obj:
            entry["status"] = "missing_in_source"
            missing_count += 1
        else:
            compared += 1
            s_def = s_obj.get("definition", "")
            t_def = t_obj.get("definition", "")
            obj_type = s_obj.get("type")
            if obj_type in {"table", "column"}:
                if _normalize_sql(s_def) == _normalize_sql(t_def):
                    entry["status"] = "match"
                    matched += 1
                else:
                    entry["status"] = "mismatch"
                    mismatch_count += 1
            else:
                if _normalize_sql(s_def) == _normalize_sql(t_def):
                    entry["status"] = "match"
                    matched += 1
                else:
                    rule_hits = _apply_rules(s_def, t_def, rules)
                    entry["rules"] = rule_hits
                    entry["status"] = "equivalent_with_rules" if rule_hits else "mismatch"
                    if rule_hits:
                        rule_hits_total += len(rule_hits)
                    else:
                        mismatch_count += 1

        findings[key] = entry

    total_objects = len(processed_keys)
    coverage = {
        "total_objects": total_objects,
        "compared_objects": compared,
        "matched_objects": matched,
        "coverage_pct": (compared / total_objects * 100.0) if total_objects else 0.0,
    }

    has_issues = rule_hits_total > 0 or mismatch_count > 0 or missing_count > 0
    status = "fail" if has_issues else "pass"

    return {
        "coverage": coverage,
        "finding_counts": {
            "rule_hits": rule_hits_total,
            "mismatches": mismatch_count,
            "missing": missing_count,
        },
        "status": status,
        "findings": findings,
    }
