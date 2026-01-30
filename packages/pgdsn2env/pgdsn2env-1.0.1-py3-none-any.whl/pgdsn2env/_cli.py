"""Command-line interface for PostgreSQL DSN to environment variable conversion."""

from argparse import ArgumentParser

from ._core import format_pg_env, pg_dsn_to_env


def cli() -> None:
    """Parse a DSN from argv and print export lines for shell usage."""
    parser = ArgumentParser(
        description="Parse a PostgreSQL DSN string and output environment variables.",
    )
    parser.add_argument("dsn", type=str, help="The PostgreSQL DSN string to parse")
    parser.add_argument(
        "-f",
        "--format",
        choices=("export", "dotenv", "json"),
        default="export",
        help="Output format for the environment mappings.",
    )
    args = parser.parse_args()
    dsn: str = args.dsn

    pg_env = pg_dsn_to_env(dsn)
    output = format_pg_env(
        pg_env,
        output_format=args.format,
    )
    if output:
        print(output)
