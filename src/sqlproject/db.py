"""Connect to SQLite and describe a database by introspection (no hand-maintained schema)."""

from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from pathlib import Path

DEFAULT_DB = Path(__file__).resolve().parents[2] / "data" / "Chinook.sqlite"


def connect(path: str | Path = DEFAULT_DB, read_only: bool = True) -> sqlite3.Connection:
    """Open a database. Read-only by default so analysis can never modify the source data."""
    if not Path(path).exists():
        raise FileNotFoundError(path)
    uri = f"file:{Path(path).resolve()}?mode={'ro' if read_only else 'rw'}"
    conn = sqlite3.connect(uri, uri=True)
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


@dataclass(frozen=True)
class Column:
    name: str
    type: str
    not_null: bool
    primary_key: bool


@dataclass(frozen=True)
class ForeignKey:
    table: str
    column: str
    ref_table: str
    ref_column: str
    nullable: bool


def table_names(conn: sqlite3.Connection) -> list[str]:
    rows = conn.execute(
        "SELECT name FROM sqlite_master WHERE type = 'table' AND name NOT LIKE 'sqlite_%' ORDER BY name"
    )
    return [r[0] for r in rows]


def columns(conn: sqlite3.Connection, table: str) -> list[Column]:
    # Table names cannot be bound as parameters, so only accept names that exist in the database.
    if table not in table_names(conn):
        raise ValueError(f"unknown table: {table!r}")
    return [
        Column(name=r[1], type=r[2], not_null=bool(r[3]), primary_key=bool(r[5]))
        for r in conn.execute(f'PRAGMA table_info("{table}")')
    ]


def foreign_keys(conn: sqlite3.Connection) -> list[ForeignKey]:
    out: list[ForeignKey] = []
    for table in table_names(conn):
        not_null = {c.name: c.not_null for c in columns(conn, table)}
        for row in conn.execute(f'PRAGMA foreign_key_list("{table}")'):
            out.append(ForeignKey(table, row[3], row[2], row[4], nullable=not not_null[row[3]]))
    return out


def row_counts(conn: sqlite3.Connection) -> dict[str, int]:
    return {t: conn.execute(f'SELECT COUNT(*) FROM "{t}"').fetchone()[0] for t in table_names(conn)}


def null_counts(conn: sqlite3.Connection, table: str) -> dict[str, int]:
    return {
        c.name: conn.execute(f'SELECT COUNT(*) FROM "{table}" WHERE "{c.name}" IS NULL').fetchone()[0]
        for c in columns(conn, table)
    }


def integrity_problems(conn: sqlite3.Connection) -> list[str]:
    """Empty list means the file is structurally sound and every foreign key resolves."""
    problems = [r[0] for r in conn.execute("PRAGMA integrity_check") if r[0] != "ok"]
    problems += [f"foreign key violation in {r[0]} (row {r[1]})" for r in conn.execute("PRAGMA foreign_key_check")]
    return problems
