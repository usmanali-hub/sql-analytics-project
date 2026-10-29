"""The queries use standard SQL, so a second engine (DuckDB) must return identical rows.

SQLite quietly accepts a SELECT column that is not in GROUP BY; stricter engines reject it. Running
the same files on DuckDB catches that class of mistake and proves the results are not an SQLite quirk.
"""

import sqlite3

import pytest

from sqlproject import db
from sqlproject.runner import load_queries

duckdb = pytest.importorskip("duckdb")


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
