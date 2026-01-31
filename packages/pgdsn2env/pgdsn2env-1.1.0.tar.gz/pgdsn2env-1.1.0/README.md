# pgdsn2env

[![CD](https://github.com/kafai-lam/pgdsn2env/actions/workflows/cd.yml/badge.svg)](https://github.com/kafai-lam/pgdsn2env/actions/workflows/cd.yml)
[![PyPI Version](https://img.shields.io/pypi/v/pgdsn2env)](https://pypi.org/project/pgdsn2env/)
[![Python Versions](https://img.shields.io/badge/python-3.10%20%7C%203.11%20%7C%203.12%20%7C%203.13%20%7C%203.14-blue)](https://www.python.org/)

Parse PostgreSQL DSN strings into `PG*` environment variables and emit shell-friendly outputs.

## Install

```bash
uv add pgdsn2env
# or
pip install pgdsn2env
```

## CLI usage

```bash
# Basic
❯ pgdsn2env "postgresql://user@location:5432/test"
export PGDATABASE=test
export PGHOST=location
export PGPORT=5432
export PGUSER=user

# With Keyword/Value Connection Strings, in JSON format
❯  pgdsn2env "host=localhost port=5432 dbname=mydb user=postgres password=secret" --format json
{"PGDATABASE": "mydb", "PGHOST": "localhost", "PGPASSWORD": "secret", "PGPORT": "5432", "PGUSER": "postgres"}

# Invoked as Python module, with advanced params
❯ python -m pgdsn2env --format dotenv "postgresql://postgres:secret@localhost:5432/mydb?sslmode=require&application_name=myapp"
PGAPPNAME=myapp
PGDATABASE=mydb
PGHOST=localhost
PGPASSWORD=secret
PGPORT=5432
PGSSLMODE=require
PGUSER=postgres
```

## Python usage

```python
from pgdsn2env import pg_dsn_to_env

pg_env = pg_dsn_to_env("postgresql://user@location:5432/test")
print(pg_env) # {'PGHOST': 'location', 'PGPORT': '5432', 'PGDATABASE': 'test', 'PGUSER': 'user'}
```

## Recipes

Set `PG*` environment variables in your current shell:

```bash
source <(pgdsn2env "$DATABASE_URL")
```

Then verify the variables are set:

```bash
echo $PGHOST $PGPORT $PGDATABASE $PGUSER
```

## Notes

- Accept both keyword-value pair and URI style PostgreSQL connection strings
- Only parameters present in the DSN are emitted.
- Values are shell-quoted in CLI output.
