"""Parse PostgreSQL DSNs into environment variable mappings and a CLI export helper."""

import json
import shlex
from urllib.parse import parse_qsl, unquote, urlparse

from ._const import CONNECTION_PARAMETER_MAPPING


def _looks_like_uri_dsn(dsn: str) -> bool:
    return dsn.startswith(("postgresql://", "postgres://"))


def _parse_uri_dsn(dsn: str) -> dict[str, str]:
    parsed = urlparse(dsn)
    params: dict[str, str] = {}

    if parsed.username is not None:
        params["user"] = unquote(parsed.username)
    if parsed.password is not None:
        params["password"] = unquote(parsed.password)
    if parsed.hostname:
        params["host"] = parsed.hostname
    if parsed.port is not None:
        params["port"] = str(parsed.port)
    if parsed.path and parsed.path != "/":
        params["dbname"] = unquote(parsed.path.lstrip("/"))

    for key, value in parse_qsl(parsed.query, keep_blank_values=True):
        if key:
            params[key] = value

    return params


def _parse_kv_dsn(dsn: str) -> dict[str, str]:
    params: dict[str, str] = {}
    tokens = shlex.split(dsn, comments=False, posix=True)
    for token in tokens:
        if "=" not in token:
            continue
        key, value = token.split("=", 1)
        if key:
            params[key] = value
    return params


def parse_dsn(dsn: str) -> dict[str, str]:
    """Parse a DSN string using a built-in, dependency-free parser."""
    if _looks_like_uri_dsn(dsn):
        return _parse_uri_dsn(dsn)
    return _parse_kv_dsn(dsn)


def pg_dsn_to_env(
    dsn: str,
    env_mapper: dict[str, str] | None = None,
) -> dict[str, str]:
    """Convert a PostgreSQL DSN string into a PG* environment variable dict."""
    params = parse_dsn(dsn)
    mapping = env_mapper if env_mapper is not None else CONNECTION_PARAMETER_MAPPING
    return {
        env_name: str(params[param_key])
        for param_key, env_name in mapping.items()
        if params.get(param_key)
    }


def dotenv_quote(value: str) -> str:
    """Quote a value for use in a .env file, escaping special characters."""
    if value == "":
        return '""'
    needs_quotes = any(ch in value for ch in (" ", "\t", "\n", "\r", '"', "\\"))
    if not needs_quotes:
        return value
    escaped = (
        value.replace("\\", "\\\\")
        .replace('"', '\\"')
        .replace("\n", "\\n")
        .replace("\r", "\\r")
    )
    return f'"{escaped}"'


def format_pg_env(
    pg_env: dict[str, str],
    output_format: str = "export",
) -> str:
    """Format PG* env mappings for CLI output."""
    if output_format == "json":
        return json.dumps(pg_env, sort_keys=True)
    if output_format == "export":
        return "\n".join(
            f"export {key}={shlex.quote(pg_env[key])}" for key in sorted(pg_env)
        )
    if output_format == "dotenv":
        return "\n".join(f"{key}={dotenv_quote(pg_env[key])}" for key in sorted(pg_env))
    raise ValueError(f"Unknown output format: {output_format}")
