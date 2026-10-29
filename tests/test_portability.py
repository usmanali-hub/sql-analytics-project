"""The queries use standard SQL, so DuckDB and PostgreSQL must return the same rows as SQLite.

SQLite quietly accepts a SELECT column that is not in GROUP BY and is relaxed about types; stricter
engines are not. Running the same files elsewhere caught three real problems: non-grouped columns,
``strftime`` (SQLite/DuckDB only) and ``ROUND(x, 2)`` on a floating-point column, which PostgreSQL
rejects. Money columns are therefore created as NUMERIC there, as a real migration would.
Both extra engines are optional locally (the tests skip) and installed in CI.
"""

import importlib
import os
import sqlite3

import pytest

from sqlproject import db
from sqlproject.runner import load_queries


def optional_engine(name: str):
    """Skip locally if an engine is missing, but fail in CI so a broken install cannot hide a skip."""
    if os.environ.get("CI"):
        return importlib.import_module(name)
    return pytest.importorskip(name)


duckdb = optional_engine("duckdb")


def _duck_type(declared: str) -> str:
    d = declared.upper()
    if "DATE" in d:
        return "TIMESTAMP"
    if d.startswith(("NUM", "DEC", "REAL", "FLOAT")):
        return "DOUBLE"
    if "CHAR" in d or "TEXT" in d or d == "":
        return "VARCHAR"
    return "BIGINT"


@pytest.fixture(scope="module")
def engines():
    lite = db.connect()
    duck = duckdb.connect()
    tables = [r[0] for r in lite.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'")]
    for t in tables:
        cols = lite.execute(f'PRAGMA table_info("{t}")').fetchall()
        ddl = ", ".join(f'"{c[1]}" {_duck_type(c[2])}' for c in cols)
        duck.execute(f'CREATE TABLE "{t}" ({ddl})')
        rows = lite.execute(f'SELECT * FROM "{t}"').fetchall()
        if rows:
            duck.executemany(f'INSERT INTO "{t}" VALUES ({",".join("?" * len(cols))})', [tuple(r) for r in rows])
    return lite, duck


def _norm(rows):
    return [tuple(round(x, 2) if isinstance(x, float) else x for x in r) for r in rows]


@pytest.mark.parametrize("query", load_queries(), ids=lambda q: f"{q.number:02d}")
def test_query_returns_same_rows_on_duckdb(engines, query):
    lite, duck = engines
    assert isinstance(lite, sqlite3.Connection)
    assert _norm(duck.execute(query.sql).fetchall()) == _norm(tuple(r) for r in lite.execute(query.sql).fetchall())


@pytest.fixture(scope="module")
def postgres(engines):
    pgserver = optional_engine("pixeltable_pgserver")
    psycopg2 = optional_engine("psycopg2")
    import tempfile

    server = pgserver.get_server(tempfile.mkdtemp())
    conn = psycopg2.connect(server.get_uri())
    conn.autocommit = True
    cur = conn.cursor()
    lite, _ = engines
    tables = [r[0] for r in lite.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'")]
    for t in tables:
        cols = lite.execute(f'PRAGMA table_info("{t}")').fetchall()
        # unquoted lower-case names: PostgreSQL folds the CamelCase identifiers used in the queries
        cur.execute(f"CREATE TABLE {t} ({', '.join(f'{c[1]} {_pg_type(c[2])}' for c in cols)})")
        rows = [tuple(r) for r in lite.execute(f'SELECT * FROM "{t}"')]
        if rows:
            cur.executemany(f"INSERT INTO {t} VALUES ({', '.join(['%s'] * len(cols))})", rows)
    yield cur
    conn.close()
    server.cleanup()


def _pg_type(declared: str) -> str:
    d = declared.upper()
    if "DATE" in d:
        return "TIMESTAMP"
    if d.startswith(("NUM", "DEC")):
        return "NUMERIC"
    if d.startswith(("REAL", "FLOAT")):
        return "DOUBLE PRECISION"
    if "CHAR" in d or "TEXT" in d or d == "":
        return "TEXT"
    return "BIGINT"


@pytest.mark.parametrize("query", load_queries(), ids=lambda q: f"{q.number:02d}")
def test_query_returns_same_rows_on_postgresql(engines, postgres, query):
    lite, _ = engines
    postgres.execute(query.sql.rstrip().rstrip(";"))
    got = _norm(tuple(float(x) if type(x).__name__ == "Decimal" else x for x in r) for r in postgres.fetchall())
    assert got == _norm(tuple(r) for r in lite.execute(query.sql).fetchall())
