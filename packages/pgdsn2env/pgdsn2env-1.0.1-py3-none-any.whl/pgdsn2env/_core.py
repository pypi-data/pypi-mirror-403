"""Parse PostgreSQL DSNs into environment variable mappings and a CLI export helper."""

import json
import shlex
from collections.abc import Callable

from ._const import CONNECTION_PARAMETER_MAPPING


def _get_dsn_parser() -> Callable[[str], dict] | None:  # pragma: no cover
    """Get the available DSN parser, trying psycopg3 first, then psycopg2."""
    try:
        from psycopg.conninfo import conninfo_to_dict  # noqa: PLC0415 # type: ignore

        return conninfo_to_dict
    except ImportError:
        try:
            from psycopg2.extensions import parse_dsn  # noqa: PLC0415 # type: ignore

            return parse_dsn
        except ImportError:
            return None


def pg_dsn_to_env(
    dsn: str,
    dsn_parser: Callable[[str], dict] | None = None,
    env_mapper: dict[str, str] | None = None,
) -> dict[str, str]:
    """Convert a PostgreSQL DSN string into a PG* environment variable dict."""
    parser = dsn_parser or _get_dsn_parser()
    if not parser:
        raise ValueError(
            "Postgresql DSN parser was missing."
            "Install either psycopg3 or psycopg2 to enable fallback_dsn_parser",
        )
    params = parser(dsn)
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
