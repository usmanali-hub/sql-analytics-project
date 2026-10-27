import sqlite3

import pytest

from sqlproject import db
from sqlproject.diagram import mermaid_er, profile_markdown, schema_markdown


@pytest.fixture(scope="module")
def conn():
    return db.connect()


def test_known_row_counts(conn):
    counts = db.row_counts(conn)
    assert counts["Customer"] == 59 and counts["Invoice"] == 412
    assert counts["InvoiceLine"] == 2240 and counts["Track"] == 3503
    assert len(counts) == 11


def test_database_is_structurally_sound(conn):
    assert db.integrity_problems(conn) == []


def test_connection_is_read_only(conn):
    with pytest.raises(sqlite3.OperationalError):
        conn.execute("DELETE FROM Customer")


def test_missing_file_raises(tmp_path):
    with pytest.raises(FileNotFoundError):
        db.connect(tmp_path / "nope.sqlite")


def test_columns_reject_unknown_table(conn):
    with pytest.raises(ValueError):
        db.columns(conn, "Customer; DROP TABLE Customer")
    names = [c.name for c in db.columns(conn, "Invoice")]
    assert names[:2] == ["InvoiceId", "CustomerId"]
    assert [c.name for c in db.columns(conn, "Invoice") if c.primary_key] == ["InvoiceId"]


def test_foreign_keys_and_nullability(conn):
    fks = {(f.table, f.column): f for f in db.foreign_keys(conn)}
    assert len(fks) == 11
    assert fks[("Invoice", "CustomerId")].ref_table == "Customer" and not fks[("Invoice", "CustomerId")].nullable
    assert fks[("Track", "AlbumId")].nullable and fks[("Employee", "ReportsTo")].nullable


def test_null_counts_match_a_direct_query(conn):
    assert db.null_counts(conn, "Track")["Composer"] == 977
    assert db.null_counts(conn, "Customer")["CustomerId"] == 0


def test_mermaid_contains_every_table_and_foreign_key(conn):
    diagram = mermaid_er(conn)
    assert diagram.startswith("erDiagram")
    for table in db.table_names(conn):
        assert f"    {table} {{" in diagram
    for fk in db.foreign_keys(conn):
        assert f'{fk.ref_table} {"|o" if fk.nullable else "||"}--o{{ {fk.table} : "{fk.column}"' in diagram


def test_generated_docs_in_the_repo_are_up_to_date(conn):
    from pathlib import Path

    docs = Path(__file__).resolve().parents[1] / "docs"
    assert (docs / "schema.md").read_text(encoding="utf-8") == schema_markdown(conn)
    assert (docs / "data_profile.md").read_text(encoding="utf-8") == profile_markdown(conn)


def test_in_memory_database_introspection():
    conn = sqlite3.connect(":memory:")
    conn.executescript(
        "CREATE TABLE a (id INTEGER PRIMARY KEY, name TEXT NOT NULL);"
        "CREATE TABLE b (id INTEGER PRIMARY KEY, a_id INTEGER REFERENCES a(id));"
        "INSERT INTO a VALUES (1, 'x'); INSERT INTO b VALUES (1, 1);"
    )
    assert db.table_names(conn) == ["a", "b"]
    assert [(f.table, f.ref_table, f.nullable) for f in db.foreign_keys(conn)] == [("b", "a", True)]
    assert db.integrity_problems(conn) == []
    conn.execute("PRAGMA foreign_keys = OFF")
    conn.execute("INSERT INTO b VALUES (2, 99)")  # orphan row
    assert any("foreign key" in p for p in db.integrity_problems(conn))
