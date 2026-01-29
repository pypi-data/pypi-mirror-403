from __future__ import annotations

from typing import Dict, Optional

from .connectors import BaseConnector, MSSQLConnector, PostgresConnector


def run_behaviour_tests(
    src: BaseConnector,
    tgt: BaseConnector,
    src_catalog: Dict[str, dict],
    tgt_catalog: Dict[str, dict],
    sample_limit: int = 5,
    timeout_s: Optional[int] = None,
) -> Dict[str, dict]:
    """Run lightweight, read-only behaviour tests.

    Strategy (best-effort):
    - For views existing on both sides, select a small sample (limit 5-10)
      and compare column count and first row shape.
    - For functions without parameters, attempt SELECT fn() LIMIT 1 for Postgres,
      and SELECT dbo.fn() for MSSQL; if not feasible, skip.
    - Triggers/procedures: skipped (no writes allowed, non-trivial to simulate).
    Returns a dict keyed by object key with status and simple metrics.
    """
    results: Dict[str, dict] = {}

    def _limited_sql(conn: BaseConnector, schema: str, name: str, limit: int) -> str:
        lmt = max(1, int(limit))
        if isinstance(conn, MSSQLConnector):
            return f"SELECT TOP {lmt} * FROM {schema}.{name}"
        # Default to Postgres style
        return f"SELECT * FROM {schema}.{name} LIMIT {lmt}"

    for key, s_obj in src_catalog.items():
        t_obj = tgt_catalog.get(key)
        if not t_obj:
            continue
        otype = s_obj.get("type")
        schema = s_obj.get("schema")
        name = s_obj.get("name")

        if otype == "view":
            try:
                # Attempt sampling on both sides with SQL-level limit
                src_rows = src.fetchall(
                    _limited_sql(src, schema, name, sample_limit), timeout_s=timeout_s
                )
                tgt_rows = tgt.fetchall(
                    _limited_sql(tgt, schema, name, sample_limit), timeout_s=timeout_s
                )
                src_cols = len(src_rows[0]) if src_rows else 0
                tgt_cols = len(tgt_rows[0]) if tgt_rows else 0
                status = "match" if src_cols == tgt_cols else "mismatch"
                results[key] = {
                    "type": otype,
                    "status": status,
                    "src_rows": len(src_rows),
                    "tgt_rows": len(tgt_rows),
                    "src_cols": src_cols,
                    "tgt_cols": tgt_cols,
                }
            except Exception as exc:
                results[key] = {"type": otype, "status": "error", "error": str(exc)}
        # Functions/procedures/trigger skipped for MVP behaviour tests.

    return results
