from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any, Dict, Iterable, List, Optional, Tuple
from urllib.parse import parse_qs, urlencode, urlparse


WRITE_KEYWORDS = {
    "insert",
    "update",
    "delete",
    "alter",
    "create",
    "drop",
    "truncate",
    "merge",
    "grant",
    "revoke",
    "exec",
}


def _ensure_read_only(sql: str) -> None:
    head = re.split(r"\s+", sql.strip(), maxsplit=1)[0].lower()
    if head in WRITE_KEYWORDS:
        raise ValueError("Write operations are not allowed in safe mode.")


def _redact_password(url: str) -> str:
    parsed = urlparse(url)
    if parsed.password:
        redacted_netloc = parsed.netloc.replace(parsed.password, "****")
        return parsed._replace(netloc=redacted_netloc).geturl()
    return url


@dataclass
class BaseConnector:
    """Common behaviours for connectors. Subclasses must provide `_connect`.

    All operations are read-only guarded by `_ensure_read_only`.
    """

    url: str
    autoconnect: bool = False

    def __post_init__(self) -> None:  # pragma: no cover - runtime connection
        self._conn = None
        self._cursor = None
        if self.autoconnect:
            self.connect()

    @property
    def redacted_url(self) -> str:
        return _redact_password(self.url)

    # --- Connection lifecycle ---
    def connect(self) -> None:  # pragma: no cover - runtime connection
        if self._conn is None:
            self._conn = self._connect()

    def close(self) -> None:  # pragma: no cover - runtime connection
        try:
            if self._cursor is not None:
                self._cursor.close()
        finally:
            if self._conn is not None:
                self._conn.close()
        self._cursor = None
        self._conn = None

    # --- Read-only execution ---
    def fetchall(
        self,
        sql: str,
        params: Optional[Tuple[Any, ...]] = None,
        timeout_s: Optional[int] = None,
    ) -> List[Tuple]:
        _ensure_read_only(sql)
        self.connect()
        cur = self._cursor or self._conn.cursor()
        self._cursor = cur
        token = self._before_query(cur, timeout_s)
        try:
            cur.execute(sql, params or tuple())
            rows = cur.fetchall()
            return rows
        finally:
            self._after_query(cur, token)

    def fetchone(
        self,
        sql: str,
        params: Optional[Tuple[Any, ...]] = None,
        timeout_s: Optional[int] = None,
    ) -> Optional[Tuple]:
        _ensure_read_only(sql)
        self.connect()
        cur = self._cursor or self._conn.cursor()
        self._cursor = cur
        token = self._before_query(cur, timeout_s)
        try:
            cur.execute(sql, params or tuple())
            return cur.fetchone()
        finally:
            self._after_query(cur, token)

    # --- Factory ---
    @classmethod
    def from_url(cls, url: str) -> "BaseConnector":  # pragma: no cover - overridden
        raise NotImplementedError

    # --- Internal ---
    def _connect(self):  # pragma: no cover - overridden
        raise NotImplementedError

    # --- Query-timeout hooks (engine-specific) ---
    def _before_query(self, cur, timeout_s: Optional[int]):  # pragma: no cover - default no-op
        return None

    def _after_query(self, cur, token):  # pragma: no cover - default no-op
        return None


def _parse_url_common(url: str) -> Tuple[str, int, str, Optional[str], Optional[str], Dict[str, str]]:
    p = urlparse(url)
    host = p.hostname or "localhost"
    port = p.port or (1433 if p.scheme.startswith("mssql") else 5432)
    db = p.path.lstrip("/") if p.path else ""
    user = p.username
    pwd = p.password
    q = {k: v[-1] for k, v in parse_qs(p.query, keep_blank_values=True).items()}
    return host, port, db, user, pwd, q


class MSSQLConnector(BaseConnector):
    """pyodbc-based MSSQL connector (read-only enforcement)."""

    def _connect(self):  # pragma: no cover - runtime connection
        import pyodbc  # type: ignore

        host, port, db, user, pwd, q = _parse_url_common(self.url)
        driver = q.get("driver", "ODBC Driver 18 for SQL Server")
        trust = q.get("TrustServerCertificate", "yes")
        encrypt = q.get("Encrypt", "yes")
        parts = [
            f"DRIVER={{{driver}}}",
            f"SERVER={host},{port}",
            f"DATABASE={db}",
        ]
        if user:
            parts.append(f"UID={user}")
        if pwd:
            parts.append(f"PWD={pwd}")
        parts.append(f"Encrypt={encrypt}")
        parts.append(f"TrustServerCertificate={trust}")
        # Optional extra ODBC attributes via query params (e.g., Authentication)
        for k, v in q.items():
            if k.lower() in {"driver", "trustservercertificate", "encrypt"}:
                continue
            if k.lower() in {"connect_timeout", "connection timeout", "timeout"}:
                parts.append(f"Connection Timeout={v}")
            else:
                parts.append(f"{k}={v}")

        conn_str = ";".join(parts)
        conn = pyodbc.connect(conn_str, autocommit=True)
        return conn

    @classmethod
    def from_url(cls, url: str) -> "MSSQLConnector":
        return cls(url=url)

    # pyodbc supports per-cursor timeout in seconds
    def _before_query(self, cur, timeout_s: Optional[int]):  # pragma: no cover - runtime
        if timeout_s is None:
            return None
        old = getattr(cur, "timeout", None)
        try:
            cur.timeout = int(timeout_s)
        except Exception:
            pass
        return old

    def _after_query(self, cur, token):  # pragma: no cover - runtime
        if token is not None:
            try:
                cur.timeout = token
            except Exception:
                pass


class PostgresConnector(BaseConnector):
    """psycopg2-based PostgreSQL connector (read-only enforcement)."""

    def _connect(self):  # pragma: no cover - runtime connection
        import psycopg2  # type: ignore

        host, port, db, user, pwd, q = _parse_url_common(self.url)
        dsn_kv = {
            "host": host,
            "port": port,
            "dbname": db,
        }
        if user:
            dsn_kv["user"] = user
        if pwd:
            dsn_kv["password"] = pwd
        if "sslmode" in q:
            dsn_kv["sslmode"] = q["sslmode"]
        if "connect_timeout" in q:
            dsn_kv["connect_timeout"] = q["connect_timeout"]
        dsn = " ".join(f"{k}={v}" for k, v in dsn_kv.items())
        conn = psycopg2.connect(dsn)
        conn.autocommit = True
        return conn

    @classmethod
    def from_url(cls, url: str) -> "PostgresConnector":
        return cls(url=url)

    # Set/reset statement_timeout in milliseconds for the session
    def _before_query(self, cur, timeout_s: Optional[int]):  # pragma: no cover - runtime
        if timeout_s is None:
            return None
        try:
            ms = max(1, int(timeout_s) * 1000)
            cur.execute(f"SET statement_timeout = {ms}")
            return ms
        except Exception:
            return None

    def _after_query(self, cur, token):  # pragma: no cover - runtime
        if token is not None:
            try:
                cur.execute("SET statement_timeout = 0")
            except Exception:
                pass
