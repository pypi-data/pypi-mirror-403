from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List, Optional

import click

from ..config.runtime import load_yaml_config, normalize_validate_objects, VALIDATE_OBJECTS
from .base import cli
from .utils import _build_connection_url

try:
    import yaml  # type: ignore
except Exception:  # pragma: no cover - handled at runtime
    yaml = None


@cli.command("wizard")
@click.option(
    "--out",
    "out_path",
    default="validator.yaml",
    help="Path to write the generated validator.yaml",
)
def wizard(out_path: str) -> None:
    """Interactive setup to generate a validator.yaml for future runs.

    Prefers reusing existing source/target URLs from validator.yaml when present.
    """
    click.echo("Welcome to Syncy wizard — let's set up your config.\n")

    existing_cfg = load_yaml_config(out_path if Path(out_path).exists() else None)

    def existing_url(kind: str) -> Optional[str]:
        section = existing_cfg.get(kind) if isinstance(existing_cfg, dict) else None
        if isinstance(section, dict):
            url = section.get("url")
            if isinstance(url, str) and url.strip():
                return url.strip()
        return None

    def ask_url(kind: str, default_scheme: str, current: Optional[str]) -> str:
        if current:
            if click.confirm(
                f"Use existing {kind} URL from {out_path}?",
                default=True,
            ):
                return current
        click.echo(
            f"For {kind}, you can paste an existing connection URL or build one interactively."
        )
        if click.confirm("Do you already have the connection URL?", default=True):
            return click.prompt(
                f"Enter {kind} connection URL (e.g., mssql://... or postgresql://...)",
                type=str,
            )
        return _build_connection_url(kind, default_scheme)

    src_url = ask_url("source", "mssql", existing_url("source"))
    tgt_url = ask_url("target", "postgresql", existing_url("target"))

    include_default = existing_cfg.get("include_schemas") if isinstance(existing_cfg, dict) else None
    exclude_default = existing_cfg.get("exclude_schemas") if isinstance(existing_cfg, dict) else None
    if isinstance(include_default, list):
        include_default = ",".join(str(s) for s in include_default)
    if isinstance(exclude_default, list):
        exclude_default = ",".join(str(s) for s in exclude_default)

    include_raw = click.prompt(
        "Include schemas (comma-separated)",
        default=include_default or "demo",
        type=str,
    )
    exclude_raw = click.prompt(
        "Exclude schemas (comma-separated)",
        default=exclude_default or "",
        type=str,
    )
    include_schemas = [s.strip() for s in include_raw.split(",") if s.strip()]
    exclude_schemas = [s.strip() for s in exclude_raw.split(",") if s.strip()]

    rules_default = ""
    if isinstance(existing_cfg, dict):
        rules_val = existing_cfg.get("rules")
        if isinstance(rules_val, str):
            rules_default = rules_val
    rules_path = click.prompt(
        "Rules YAML path (leave blank for built-in)",
        default=rules_default,
        type=str,
    ).strip()

    validate_default = list(VALIDATE_OBJECTS)
    if isinstance(existing_cfg, dict):
        raw_validate = existing_cfg.get("validate")
        if raw_validate is None:
            raw_validate = existing_cfg.get("validate_objects")
        if raw_validate is not None:
            normalized, _unknown = normalize_validate_objects(raw_validate)
            if normalized:
                validate_default = normalized
    validate_raw = click.prompt(
        "Objects to validate (comma-separated)",
        default=",".join(validate_default),
        type=str,
    )
    validate_list, validate_unknown = normalize_validate_objects(validate_raw)
    if validate_unknown:
        click.echo(
            "Warning: unknown object types ignored: " + ", ".join(validate_unknown),
            err=True,
        )
    if not validate_list:
        click.echo("No valid objects selected; defaulting to all.", err=True)
        validate_list = list(VALIDATE_OBJECTS)

    fail_on_major = click.confirm(
        "Fail the run if any findings are present?", default=True
    )
    min_coverage = click.prompt(
        "Minimum coverage percentage to pass thresholds", default=70.0, type=float
    )

    cfg: Dict[str, Any] = {
        "source": {"url": src_url},
        "target": {"url": tgt_url},
        "include_schemas": include_schemas,
        "exclude_schemas": exclude_schemas,
        "validate": validate_list,
    }
    if rules_path:
        cfg["rules"] = rules_path

    try:
        if yaml is None:
            lines = [
                "source:",
                f"  url: {src_url}",
                "target:",
                f"  url: {tgt_url}",
                f"include_schemas: [{', '.join(include_schemas)}]",
                f"exclude_schemas: [{', '.join(exclude_schemas)}]",
            ]
            if rules_path:
                lines.append(f"rules: {rules_path}")
            lines.append(f"validate: [{', '.join(validate_list)}]")
            content = "\n".join(lines) + "\n"
        else:
            content = yaml.safe_dump(cfg, sort_keys=False)
        with open(out_path, "w", encoding="utf-8") as f:
            f.write(content)
    except Exception as exc:
        raise click.ClickException(f"Failed to write {out_path}: {exc}")

    click.echo(f"\nWrote configuration to: {out_path}")
    cmd_parts: List[str] = [
        "syncy validate",
        f"--config {out_path}",
        f"--min-coverage {min_coverage}",
        "--fail-on-major" if fail_on_major else "--no-fail-on-major",
    ]
    if include_schemas:
        cmd_parts.append(f"--include-schemas {','.join(include_schemas)}")
    if exclude_schemas:
        cmd_parts.append(f"--exclude-schemas {','.join(exclude_schemas)}")
    if validate_list and set(validate_list) != set(VALIDATE_OBJECTS):
        cmd_parts.append(f"--objects {','.join(validate_list)}")
    if rules_path:
        cmd_parts.append(f"--rules {rules_path}")
    cmd = " ".join(cmd_parts)

    click.echo("Next steps:")
    click.echo(f"- Run: {cmd}")

    if click.confirm("Run validation now with this config?", default=False):
        try:
            import subprocess

            subprocess.run(cmd, shell=True, check=False)
        except Exception as exc:  # pragma: no cover
            click.echo(f"Could not run automatically: {exc}")


__all__ = ["wizard"]
