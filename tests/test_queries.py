"""Every query result is checked against an independent calculation done in plain Python."""

from collections import defaultdict
from pathlib import Path

import pytest

from sqlproject import db
from sqlproject.runner import (
    QUERY_DIR,
    ROOT,
    load_queries,
    markdown_table,
    parse_query,
    render_report,
    run_query,
)

TOTAL_REVENUE = 2328.60


@pytest.fixture(scope="module")
def conn():
    return db.connect()


@pytest.fixture(scope="module")
def queries():
    return {q.number: q for q in load_queries()}


def rows(conn, queries, n):
    return run_query(conn, queries[n]).rows


def all_rows(conn, sql):
    return conn.execute(sql).fetchall()


def test_ten_numbered_queries_each_with_a_question(queries):
    assert sorted(queries) == list(range(1, 11))
    assert all(q.question.endswith("?") and q.sql.upper().startswith(("SELECT", "WITH")) for q in queries.values())


def test_total_revenue_reconciles_between_invoice_and_invoice_lines(conn):
    by_invoice = conn.execute("SELECT ROUND(SUM(Total), 2) FROM Invoice").fetchone()[0]
    by_line = conn.execute("SELECT ROUND(SUM(UnitPrice * Quantity), 2) FROM InvoiceLine").fetchone()[0]
    assert by_invoice == by_line == TOTAL_REVENUE


def test_q1_revenue_by_country_matches_python(conn, queries):
    totals: dict[str, list[float]] = defaultdict(list)
    for country, total in all_rows(conn, "SELECT BillingCountry, Total FROM Invoice"):
        totals[country].append(total)
    expected = sorted(((c, len(v), round(sum(v), 2)) for c, v in totals.items()), key=lambda r: (-r[2], r[0]))[:10]
    assert [(r[0], r[1], r[2]) for r in rows(conn, queries, 1)] == expected


def test_q2_top_customers_match_python(conn, queries):
    spend: dict[int, float] = defaultdict(float)
    for cid, total in all_rows(conn, "SELECT CustomerId, Total FROM Invoice"):
        spend[cid] += total
    expected = sorted(spend.items(), key=lambda kv: (-round(kv[1], 2), kv[0]))[:10]
    got = [(r[0], r[4]) for r in rows(conn, queries, 2)]
    assert got == [(cid, round(v, 2)) for cid, v in expected]


def test_q3_genre_revenue_matches_python_and_covers_all_revenue(conn, queries):
    genre_of = dict(all_rows(conn, "SELECT TrackId, GenreId FROM Track"))
    names = dict(all_rows(conn, "SELECT GenreId, Name FROM Genre"))
    revenue: dict[str, float] = defaultdict(float)
    for track_id, price, qty in all_rows(conn, "SELECT TrackId, UnitPrice, Quantity FROM InvoiceLine"):
        revenue[names.get(genre_of[track_id], "Unknown")] += price * qty
    assert sum(revenue.values()) == pytest.approx(TOTAL_REVENUE)  # no revenue is lost to the joins
    top = sorted(revenue.items(), key=lambda kv: (-round(kv[1], 2), kv[0]))[:10]
    assert [(r[0], r[2]) for r in rows(conn, queries, 3)] == [(g, round(v, 2)) for g, v in top]


def test_q4_artist_revenue_matches_python(conn, queries):
    album_artist = dict(all_rows(conn, "SELECT AlbumId, ArtistId FROM Album"))
    track_album = dict(all_rows(conn, "SELECT TrackId, AlbumId FROM Track"))
    artist_name = dict(all_rows(conn, "SELECT ArtistId, Name FROM Artist"))
    revenue: dict[str, float] = defaultdict(float)
    for track_id, price, qty in all_rows(conn, "SELECT TrackId, UnitPrice, Quantity FROM InvoiceLine"):
        revenue[artist_name[album_artist[track_album[track_id]]]] += price * qty
    assert sum(revenue.values()) == pytest.approx(TOTAL_REVENUE)
    top = sorted(revenue.items(), key=lambda kv: (-round(kv[1], 2), kv[0]))[:10]
    assert [(r[0], r[2]) for r in rows(conn, queries, 4)] == [(a, round(v, 2)) for a, v in top]


def test_q5_monthly_revenue_sums_to_total_and_is_ordered(conn, queries):
    result = rows(conn, queries, 5)
    assert [r[0] for r in result] == sorted(r[0] for r in result)
    assert round(sum(r[2] for r in result), 2) == TOTAL_REVENUE
    assert sum(r[1] for r in result) == 412


def test_q6_every_rupee_is_attributed_to_exactly_one_rep(conn, queries):
    result = rows(conn, queries, 6)
    assert len(result) == 8  # all employees, including those with no customers
    assert round(sum(r[5] for r in result), 2) == TOTAL_REVENUE
    assert sum(r[3] for r in result) == 59
    assert next(r for r in result if r[1] == "Andrew Adams")[3:] == (0, 0, 0.0)  # kept, with zeros


def test_q7_unsold_tracks_total_matches_set_difference(conn, queries):
    sold = {t for (t,) in all_rows(conn, "SELECT TrackId FROM InvoiceLine")}
    every = {t for (t,) in all_rows(conn, "SELECT TrackId FROM Track")}
    unlimited = queries[7].sql.replace("LIMIT 10", "")
    assert sum(n for _g, n in all_rows(conn, unlimited)) == len(every - sold) == 1519


def test_q8_purchase_frequency_accounts_for_every_customer_and_invoice(conn, queries):
    result = rows(conn, queries, 8)
    assert sum(r[1] for r in result) == 59
    assert sum(r[0] * r[1] for r in result) == 412


def test_q9_playlist_track_counts_match_the_link_table(conn, queries):
    result = rows(conn, queries, 9)
    assert len(result) == 18
    assert sum(r[2] for r in result) == conn.execute("SELECT COUNT(*) FROM PlaylistTrack").fetchone()[0] == 8715


def test_q10_reporting_lines_form_a_single_tree(conn, queries):
    result = rows(conn, queries, 10)
    assert [r for r in result if r[2].startswith("(none")] == [(1, "Andrew Adams", "(none: top of the tree)", 2)]
    assert sum(r[3] for r in result) == 7  # everyone except the top has exactly one manager


def test_committed_results_and_report_are_up_to_date(conn, queries):
    for n, q in queries.items():
        csv_path = ROOT / "results" / f"{n:02d}_{q.name}.csv"
        assert csv_path.exists(), csv_path
        header = csv_path.read_text(encoding="utf-8").splitlines()[0]
        assert header == ",".join(run_query(conn, q).columns)
    report = (ROOT / "docs" / "business_questions.md").read_text(encoding="utf-8")
    assert report == render_report(conn, list(queries.values()))


def test_parse_query_validation(tmp_path):
    bad_name = tmp_path / "revenue.sql"
    bad_name.write_text("-- question: x?\nSELECT 1;")
    with pytest.raises(ValueError, match="file names"):
        parse_query(bad_name)
    no_question = tmp_path / "01_x.sql"
    no_question.write_text("SELECT 1;")
    with pytest.raises(ValueError, match="question"):
        parse_query(no_question)
    ok = tmp_path / "02_ok.sql"
    ok.write_text("-- question: What?\n-- notes: n\nSELECT 1 AS one;")
    q = parse_query(ok)
    assert (q.number, q.name, q.question, q.notes, q.sql) == (2, "ok", "What?", "n", "SELECT 1 AS one;")


def test_duplicate_numbers_rejected(tmp_path):
    for name in ("01_a.sql", "01_b.sql"):
        (tmp_path / name).write_text("-- question: q?\nSELECT 1;")
    with pytest.raises(ValueError, match="duplicate"):
        load_queries(tmp_path)


def test_markdown_table_escapes_pipes_and_truncates():
    from sqlproject.runner import Result

    table = markdown_table(Result(["a"], [("x|y",)] + [(i,) for i in range(20)]), max_rows=3)
    assert "x\\|y" in table and "21 rows in total" in table


def test_query_dir_exists():
    assert Path(QUERY_DIR).is_dir()
