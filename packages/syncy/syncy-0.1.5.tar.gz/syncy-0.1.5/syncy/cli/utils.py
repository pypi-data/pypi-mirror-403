from __future__ import annotations

from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Dict, Optional
from urllib.parse import quote_plus

import click


DEFAULT_REPORTS_DIR = "reports"
LOCAL_TZ = timezone(timedelta(hours=8))
DEFAULT_BEHAVIOUR_LIMIT = 5
DEFAULT_BEHAVIOUR_TIMEOUT_S = 30


def _timestamp() -> str:
    return datetime.now(LOCAL_TZ).strftime("%Y%m%d_%H%M%S%z")


def _prompt_connection_engine(kind: str, default_scheme: str) -> str:
    choice = click.prompt(
        f"Choose {kind} engine",
        type=click.Choice(["mssql", "postgresql"], case_sensitive=False),
        default=default_scheme,
    )
    return choice.lower()


def _prompt_optional_params(scheme: str) -> Dict[str, str]:
    params: Dict[str, str] = {}
    if scheme == "mssql":
        driver = click.prompt(
            "ODBC driver",
            default="ODBC Driver 18 for SQL Server",
        )
        encrypt = "yes" if click.confirm("Encrypt connection?", default=True) else "no"
        trust = (
            "yes"
            if click.confirm("Trust server certificate?", default=True)
            else "no"
        )
        params["driver"] = driver
        params["Encrypt"] = encrypt
        params["TrustServerCertificate"] = trust
    else:
        sslmode = click.prompt(
            "SSL mode (leave blank to skip)",
            default="",
            show_default=False,
        ).strip()
        if sslmode:
            params["sslmode"] = sslmode

    extra = click.prompt(
        "Additional query params (key=value&key2=value2, blank to skip)",
        default="",
        show_default=False,
    ).strip()
    if extra:
        for chunk in extra.split("&"):
            if "=" not in chunk:
                continue
            key, value = chunk.split("=", 1)
            key = key.strip()
            value = value.strip()
            if key:
                params[key] = value
    return params


def _build_connection_url(kind: str, default_scheme: str) -> str:
    while True:
        scheme = _prompt_connection_engine(kind, default_scheme)
        default_port = 1433 if scheme == "mssql" else 5432
        default_db = "master" if scheme == "mssql" else "postgres"
        host = click.prompt("Host", default="localhost").strip()
        port = click.prompt("Port", default=default_port, type=int)
        database = click.prompt("Database name", default=default_db).strip()
        username = click.prompt(
            "Username (leave blank for none)",
            default="",
            show_default=False,
        ).strip()
        password = click.prompt(
            "Password (leave blank for none)",
            default="",
            show_default=False,
            hide_input=True,
        )
        params = _prompt_optional_params(scheme)

        auth = ""
        if username:
            auth = quote_plus(username)
            if password:
                auth = f"{auth}:{quote_plus(password)}"
            auth = f"{auth}@"
        elif password:
            auth = f":{quote_plus(password)}@"

        host_part = host
        if port:
            host_part = f"{host}:{port}"

        path = f"/{database}" if database else ""
        query = "&".join(
            f"{quote_plus(str(k))}={quote_plus(str(v))}" for k, v in params.items()
        )
        url = f"{scheme}://{auth}{host_part}{path}"
        if query:
            url = f"{url}?{query}"

        click.echo(f"\nConstructed {kind} URL:\n{url}\n")
        if click.confirm("Use this URL?", default=True):
            return url
        click.echo("Let's try building it again.\n")


def _make_output_dir(base_out: Optional[str]) -> Path:
    base = Path(base_out) if base_out else Path(DEFAULT_REPORTS_DIR)
    out_dir = base / _timestamp()
    out_dir.mkdir(parents=True, exist_ok=True)
    return out_dir


def _engine_info(conn) -> Dict[str, str]:
    """Return a simple engine and version string for overview."""
    try:
        from ..core.connectors import MSSQLConnector, PostgresConnector

        if isinstance(conn, MSSQLConnector):
            row = conn.fetchone("SELECT @@VERSION")
            return {"engine": "SQL Server", "version": (row[0] if row else "")}
        if isinstance(conn, PostgresConnector):
            row = conn.fetchone("SELECT version()")
            return {"engine": "PostgreSQL", "version": (row[0] if row else "")}
    except Exception:
        pass
    name = conn.__class__.__name__.replace("Connector", "")
    return {"engine": name, "version": ""}


__all__ = [
    "DEFAULT_BEHAVIOUR_LIMIT",
    "DEFAULT_BEHAVIOUR_TIMEOUT_S",
    "DEFAULT_REPORTS_DIR",
    "LOCAL_TZ",
    "_build_connection_url",
    "_engine_info",
    "_make_output_dir",
]
