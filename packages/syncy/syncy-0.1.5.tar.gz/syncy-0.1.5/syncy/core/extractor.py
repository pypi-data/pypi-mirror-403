from __future__ import annotations

import re
from typing import Dict, List, Optional

from .connectors import MSSQLConnector, PostgresConnector


Catalog = Dict[str, dict]


def _key(schema: str, name: str, obj_type: str) -> str:
    return f"{schema}.{name}:{obj_type}"


def _in_scope(schema: str, includes: Optional[List[str]], excludes: Optional[List[str]]) -> bool:
    if includes and schema not in includes:
        return False
    if excludes and schema in excludes:
        return False
    return True


_DEFAULT_TYPECAST_RE = re.compile(r"::[\w\s\[\]\.]+")


def _normalize_default(value: Optional[str]) -> str:
    if not value:
        return ""
    s = str(value).strip().lower()
    s = re.sub(r"\s+", " ", s)
    # Strip wrapping parentheses (common in MSSQL defaults)
    while s.startswith("(") and s.endswith(")") and len(s) > 1:
        s = s[1:-1].strip()
    # Strip trailing Postgres casts (e.g., 'x'::text)
    s = _DEFAULT_TYPECAST_RE.sub("", s).strip()
    return s


def _mssql_char_length(type_name: str, max_length: Optional[int]) -> Optional[int]:
    if max_length is None:
        return None
    if max_length == -1:
        return None
    length = int(max_length)
    if type_name in {"nchar", "nvarchar"}:
        length = int(length / 2)
    return length


def _normalize_mssql_type(
    type_name: str,
    max_length: Optional[int],
    precision: Optional[int],
    scale: Optional[int],
) -> str:
    t = (type_name or "").lower()
    if t in {"varchar", "nvarchar", "char", "nchar"}:
        length = _mssql_char_length(t, max_length)
        return f"varchar({length})" if length else "text"
    if t in {"text", "ntext"}:
        return "text"
    if t in {"int"}:
        return "int"
    if t in {"bigint"}:
        return "bigint"
    if t in {"smallint"}:
        return "smallint"
    if t in {"tinyint"}:
        return "smallint"
    if t in {"bit"}:
        return "boolean"
    if t in {"decimal", "numeric", "money", "smallmoney"}:
        if precision is not None and scale is not None:
            return f"numeric({precision},{scale})"
        if precision is not None:
            return f"numeric({precision})"
        return "numeric"
    if t in {"float", "real"}:
        return "float"
    if t in {"date"}:
        return "date"
    if t in {"datetime", "datetime2", "smalldatetime"}:
        return "timestamp"
    if t in {"time"}:
        return "time"
    if t in {"uniqueidentifier"}:
        return "uuid"
    if t in {"binary", "varbinary", "image", "rowversion", "timestamp"}:
        return "bytea"
    if t in {"xml", "sql_variant"}:
        return "text"
    return t or "unknown"


def _normalize_pg_type(
    data_type: str,
    udt_name: Optional[str],
    char_length: Optional[int],
    precision: Optional[int],
    scale: Optional[int],
) -> str:
    t = (data_type or "").lower()
    u = (udt_name or "").lower() if udt_name else ""
    if t in {"character varying", "character", "varchar", "char"}:
        if char_length:
            return f"varchar({int(char_length)})"
        return "text"
    if t in {"text"}:
        return "text"
    if t in {"integer"} or u in {"int4"}:
        return "int"
    if t in {"bigint"} or u in {"int8"}:
        return "bigint"
    if t in {"smallint"} or u in {"int2"}:
        return "smallint"
    if t in {"boolean"} or u in {"bool"}:
        return "boolean"
    if t in {"numeric", "decimal"}:
        if precision is not None and scale is not None:
            return f"numeric({precision},{scale})"
        if precision is not None:
            return f"numeric({precision})"
        return "numeric"
    if t in {"double precision"} or u in {"float8"}:
        return "float"
    if t in {"real"} or u in {"float4"}:
        return "float"
    if t in {"date"}:
        return "date"
    if t in {"timestamp without time zone", "timestamp with time zone"} or u in {"timestamp", "timestamptz"}:
        return "timestamp"
    if t in {"time without time zone", "time with time zone"} or u in {"time", "timetz"}:
        return "time"
    if t in {"uuid"} or u in {"uuid"}:
        return "uuid"
    if t in {"bytea"} or u in {"bytea"}:
        return "bytea"
    if t in {"json", "jsonb"} or u in {"json", "jsonb"}:
        return "json"
    if t in {"array"}:
        return "array"
    if t in {"user-defined"} and u:
        return u
    return t or u or "unknown"


def _column_signature(norm_type: str, is_nullable: bool, default_norm: str) -> str:
    parts = [f"type={norm_type}", f"nullable={'true' if is_nullable else 'false'}"]
    if default_norm:
        parts.append(f"default={default_norm}")
    return "|".join(parts)


def extract_catalog_mssql(
    conn: MSSQLConnector, includes: Optional[List[str]] = None, excludes: Optional[List[str]] = None
) -> Catalog:
    """Extract tables, views, procedures, functions, and triggers from SQL Server.

    Read-only, system schemas filtered out. Returns a normalized catalog.
    """
    catalog: Catalog = {}

    # Tables
    sql_tables = r"""
    SELECT s.name AS schema_name, t.name AS table_name
    FROM sys.tables t
    JOIN sys.schemas s ON s.schema_id = t.schema_id
    WHERE s.name NOT IN ('sys', 'INFORMATION_SCHEMA')
      AND t.is_ms_shipped = 0
    """
    for schema, name in conn.fetchall(sql_tables):
        if not _in_scope(schema, includes, excludes):
            continue
        catalog[_key(schema, name, "table")] = {
            "schema": schema,
            "name": name,
            "type": "table",
            "definition": "",
        }

    # Columns
    sql_cols = r"""
    SELECT s.name AS schema_name,
           t.name AS table_name,
           c.name AS column_name,
           ty.name AS data_type,
           c.max_length,
           c.precision,
           c.scale,
           c.is_nullable,
           dc.definition AS default_definition
    FROM sys.tables t
    JOIN sys.schemas s ON s.schema_id = t.schema_id
    JOIN sys.columns c ON c.object_id = t.object_id
    JOIN sys.types ty ON c.user_type_id = ty.user_type_id
    LEFT JOIN sys.default_constraints dc ON c.default_object_id = dc.object_id
    WHERE s.name NOT IN ('sys', 'INFORMATION_SCHEMA')
      AND t.is_ms_shipped = 0
    """
    for schema, table, col, dtype, max_len, prec, scale, is_nullable, default_def in conn.fetchall(sql_cols):
        if not _in_scope(schema, includes, excludes):
            continue
        norm_type = _normalize_mssql_type(dtype, max_len, prec, scale)
        default_norm = _normalize_default(default_def)
        col_name = f"{table}.{col}"
        table_key = _key(schema, table, "table")
        catalog[_key(schema, col_name, "column")] = {
            "schema": schema,
            "name": col_name,
            "type": "column",
            "table": table,
            "table_key": table_key,
            "definition": _column_signature(norm_type, bool(is_nullable), default_norm),
        }

    # Views
    sql_views = r"""
    SELECT s.name AS schema_name, v.name AS object_name, 'view' AS obj_type,
           m.definition AS definition
    FROM sys.views v
    JOIN sys.schemas s ON s.schema_id = v.schema_id
    LEFT JOIN sys.sql_modules m ON m.object_id = v.object_id
    WHERE s.name NOT IN ('sys', 'INFORMATION_SCHEMA')
    """
    for schema, name, obj_type, definition in conn.fetchall(sql_views):
        if not _in_scope(schema, includes, excludes):
            continue
        catalog[_key(schema, name, obj_type)] = {
            "schema": schema,
            "name": name,
            "type": obj_type,
            "definition": definition or "",
        }

    # Procedures
    sql_procs = r"""
    SELECT s.name AS schema_name, p.name AS object_name, 'procedure' AS obj_type,
           m.definition AS definition
    FROM sys.procedures p
    JOIN sys.schemas s ON s.schema_id = p.schema_id
    LEFT JOIN sys.sql_modules m ON m.object_id = p.object_id
    WHERE s.name NOT IN ('sys', 'INFORMATION_SCHEMA')
    """
    for schema, name, obj_type, definition in conn.fetchall(sql_procs):
        if not _in_scope(schema, includes, excludes):
            continue
        catalog[_key(schema, name, obj_type)] = {
            "schema": schema,
            "name": name,
            "type": obj_type,
            "definition": definition or "",
        }

    # Functions
    sql_funcs = r"""
    SELECT s.name AS schema_name, o.name AS object_name, 'function' AS obj_type,
           m.definition AS definition
    FROM sys.objects o
    JOIN sys.schemas s ON s.schema_id = o.schema_id
    LEFT JOIN sys.sql_modules m ON m.object_id = o.object_id
    WHERE o.type IN ('FN','IF','TF')
      AND s.name NOT IN ('sys', 'INFORMATION_SCHEMA')
    """
    for schema, name, obj_type, definition in conn.fetchall(sql_funcs):
        if not _in_scope(schema, includes, excludes):
            continue
        catalog[_key(schema, name, obj_type)] = {
            "schema": schema,
            "name": name,
            "type": obj_type,
            "definition": definition or "",
        }

    # Triggers
    sql_trigs = r"""
    SELECT s.name AS schema_name, t.name AS object_name, 'trigger' AS obj_type,
           m.definition AS definition
    FROM sys.triggers t
    JOIN sys.objects o ON o.object_id = t.parent_id
    JOIN sys.schemas s ON s.schema_id = o.schema_id
    LEFT JOIN sys.sql_modules m ON m.object_id = t.object_id
    WHERE s.name NOT IN ('sys', 'INFORMATION_SCHEMA')
    """
    for schema, name, obj_type, definition in conn.fetchall(sql_trigs):
        if not _in_scope(schema, includes, excludes):
            continue
        catalog[_key(schema, name, obj_type)] = {
            "schema": schema,
            "name": name,
            "type": obj_type,
            "definition": definition or "",
        }

    return catalog


def extract_catalog_postgres(
    conn: PostgresConnector, includes: Optional[List[str]] = None, excludes: Optional[List[str]] = None
) -> Catalog:
    """Extract tables, views, procedures (pg>=11), functions, triggers from PostgreSQL."""
    catalog: Catalog = {}

    # Tables
    sql_tables = r"""
    SELECT table_schema, table_name
    FROM information_schema.tables
    WHERE table_type = 'BASE TABLE'
      AND table_schema NOT IN ('pg_catalog', 'information_schema')
    """
    for schema, name in conn.fetchall(sql_tables):
        if not _in_scope(schema, includes, excludes):
            continue
        catalog[_key(schema, name, "table")] = {
            "schema": schema,
            "name": name,
            "type": "table",
            "definition": "",
        }

    # Columns
    sql_cols = r"""
    SELECT table_schema,
           table_name,
           column_name,
           data_type,
           udt_name,
           character_maximum_length,
           numeric_precision,
           numeric_scale,
           is_nullable,
           column_default
    FROM information_schema.columns
    WHERE table_schema NOT IN ('pg_catalog', 'information_schema')
    """
    for schema, table, col, dtype, udt, char_len, prec, scale, is_nullable, default_def in conn.fetchall(sql_cols):
        if not _in_scope(schema, includes, excludes):
            continue
        norm_type = _normalize_pg_type(dtype, udt, char_len, prec, scale)
        default_norm = _normalize_default(default_def)
        col_name = f"{table}.{col}"
        table_key = _key(schema, table, "table")
        catalog[_key(schema, col_name, "column")] = {
            "schema": schema,
            "name": col_name,
            "type": "column",
            "table": table,
            "table_key": table_key,
            "definition": _column_signature(norm_type, str(is_nullable).upper() == "YES", default_norm),
        }

    # Views
    sql_views = r"""
    SELECT n.nspname AS schema_name, c.relname AS object_name, 'view' AS obj_type,
           pg_get_viewdef(c.oid, true) AS definition
    FROM pg_class c
    JOIN pg_namespace n ON n.oid = c.relnamespace
    WHERE c.relkind = 'v'
      AND n.nspname NOT IN ('pg_catalog', 'information_schema')
    """
    for schema, name, obj_type, definition in conn.fetchall(sql_views):
        if not _in_scope(schema, includes, excludes):
            continue
        catalog[_key(schema, name, obj_type)] = {
            "schema": schema,
            "name": name,
            "type": obj_type,
            "definition": definition or "",
        }

    # Functions
    sql_funcs = r"""
    SELECT n.nspname AS schema_name, p.proname AS object_name, 'function' AS obj_type,
           pg_get_functiondef(p.oid) AS definition
    FROM pg_proc p
    JOIN pg_namespace n ON n.oid = p.pronamespace
    WHERE p.prokind = 'f'
      AND n.nspname NOT IN ('pg_catalog', 'information_schema')
    """
    for schema, name, obj_type, definition in conn.fetchall(sql_funcs):
        if not _in_scope(schema, includes, excludes):
            continue
        catalog[_key(schema, name, obj_type)] = {
            "schema": schema,
            "name": name,
            "type": obj_type,
            "definition": definition or "",
        }

    # Procedures (PostgreSQL 11+)
    sql_procs = r"""
    SELECT n.nspname AS schema_name, p.proname AS object_name, 'procedure' AS obj_type,
           pg_get_functiondef(p.oid) AS definition
    FROM pg_proc p
    JOIN pg_namespace n ON n.oid = p.pronamespace
    WHERE p.prokind = 'p'
      AND n.nspname NOT IN ('pg_catalog', 'information_schema')
    """
    try:
        for schema, name, obj_type, definition in conn.fetchall(sql_procs):
            if not _in_scope(schema, includes, excludes):
                continue
            catalog[_key(schema, name, obj_type)] = {
                "schema": schema,
                "name": name,
                "type": obj_type,
                "definition": definition or "",
            }
    except Exception:
        # Older versions may not support 'p' kind; ignore gracefully.
        pass

    # Triggers
    sql_trigs = r"""
    SELECT n.nspname AS schema_name, tg.tgname AS object_name, 'trigger' AS obj_type,
           pg_get_triggerdef(tg.oid, true) AS definition
    FROM pg_trigger tg
    JOIN pg_class c ON c.oid = tg.tgrelid
    JOIN pg_namespace n ON n.oid = c.relnamespace
    WHERE NOT tg.tgisinternal
      AND n.nspname NOT IN ('pg_catalog', 'information_schema')
    """
    for schema, name, obj_type, definition in conn.fetchall(sql_trigs):
        if not _in_scope(schema, includes, excludes):
            continue
        catalog[_key(schema, name, obj_type)] = {
            "schema": schema,
            "name": name,
            "type": obj_type,
            "definition": definition or "",
        }

    return catalog
