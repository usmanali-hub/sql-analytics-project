"""CTE and window-function queries (11-15), each checked against a plain-Python recomputation.

Money is compared in integer cents on the Python side so that float rounding cannot create or
hide ties between customers or genres.
"""

from collections import defaultdict

import pytest

from sqlproject import db
from sqlproject.runner import load_queries, run_query


@pytest.fixture(scope="module")
def conn():
    return db.connect()


@pytest.fixture(scope="module")
def queries():
    return {q.number: q for q in load_queries()}


def rows(conn, queries, n):
    return run_query(conn, queries[n]).rows


def cents(x: float) -> int:
    return round(x * 100)


def customer_spend_cents(conn):
    spend: dict[int, int] = defaultdict(int)
    for cid, total in conn.execute("SELECT CustomerId, Total FROM Invoice"):
        spend[cid] += cents(total)
    return spend


def test_q11_spend_quartiles_match_python(conn, queries):
    spend = customer_spend_cents(conn)
    ordered = sorted(spend.items(), key=lambda kv: (-kv[1], kv[0]))
    n = len(ordered)  # 59 customers: NTILE gives the remainder to the first groups
    sizes = [n // 4 + (1 if i < n % 4 else 0) for i in range(4)]
    expected, start = [], 0
    total = sum(spend.values())
    for q, size in enumerate(sizes, 1):
        chunk = [v for _, v in ordered[start : start + size]]
        start += size
        expected.append((q, size, sum(chunk) / 100, round(100 * sum(chunk) / total, 1)))
    assert rows(conn, queries, 11) == expected


def test_q11_quartiles_cover_every_customer_and_all_revenue(conn, queries):
    got = rows(conn, queries, 11)
    assert sum(r[1] for r in got) == 59
    assert sum(r[2] for r in got) == pytest.approx(2328.60)
    assert sum(r[3] for r in got) == pytest.approx(100, abs=0.2)  # four independently rounded percentages
    assert [r[2] for r in got] == sorted((r[2] for r in got), reverse=True)  # quartile 1 spends most


def test_q12_running_total_and_change_match_python(conn, queries):
    monthly: dict[str, int] = defaultdict(int)
    for date, total in conn.execute("SELECT InvoiceDate, Total FROM Invoice"):
        monthly[str(date)[:7]] += cents(total)
    expected, running, previous = [], 0, None
    for month in sorted(monthly):
        running += monthly[month]
        change = None if previous is None else (monthly[month] - previous) / 100
        expected.append((month, monthly[month] / 100, running / 100, change))
        previous = monthly[month]
    got = rows(conn, queries, 12)
    assert [(r[0], r[1], r[2]) for r in got] == [(e[0], e[1], e[2]) for e in expected]
    assert [r[3] for r in got] == pytest.approx([e[3] for e in expected]) or [r[3] for r in got] == [e[3] for e in expected]
    assert got[0][3] is None  # first month has no predecessor
    assert got[-1][2] == pytest.approx(2328.60)  # running total ends at total revenue


def test_q13_top_two_artists_in_top_five_genres_match_python(conn, queries):
    sql = """SELECT g.GenreId, g.Name, ar.Name, il.UnitPrice, il.Quantity
             FROM InvoiceLine il JOIN Track t ON t.TrackId = il.TrackId
             JOIN Genre g ON g.GenreId = t.GenreId
             JOIN Album al ON al.AlbumId = t.AlbumId
             JOIN Artist ar ON ar.ArtistId = al.ArtistId"""
    by_pair: dict[tuple[int, str, str], int] = defaultdict(int)
    genre_total: dict[int, int] = defaultdict(int)
    for gid, genre, artist, price, qty in conn.execute(sql):
        c = cents(price * qty)
        by_pair[(gid, genre, artist)] += c
        genre_total[gid] += c
    top5 = sorted(genre_total, key=lambda g: (-genre_total[g], g))[:5]
    expected = []
    for gid in top5:
        mine = sorted(((a, v) for (g, _, a), v in by_pair.items() if g == gid), key=lambda kv: (-kv[1], kv[0]))[:2]
        genre = next(name for (g, name, _) in by_pair if g == gid)
        expected += [(genre, i, a, v / 100) for i, (a, v) in enumerate(mine, 1)]
    assert rows(conn, queries, 13) == sorted(expected, key=lambda r: (r[0], r[1]))


def test_q14_top_customer_per_country_keeps_ties(conn, queries):
    spend = customer_spend_cents(conn)
    per_country: dict[str, list[tuple[str, int]]] = defaultdict(list)
    for cid, name, country in conn.execute("SELECT CustomerId, FirstName || ' ' || LastName, Country FROM Customer"):
        per_country[country].append((name, spend[cid]))
    expected = set()
    for country, people in per_country.items():
        if len(people) > 1:
            best = max(v for _, v in people)
            expected |= {(country, name, best / 100, len(people)) for name, v in people if v == best}
    got = rows(conn, queries, 14)
    assert set(got) == expected
    assert len(got) == len(expected)
    counts = [r[3] for r in got]
    assert counts == sorted(counts, reverse=True)
    uk = [r for r in got if r[0] == "United Kingdom"]
    assert len(uk) == 3  # a three-way tie: RANK keeps all, ROW_NUMBER would silently drop two


def test_q15_pareto_matches_python_and_reaches_eighty_percent(conn, queries):
    revenue: dict[str, int] = defaultdict(int)
    sql = "SELECT g.Name, il.UnitPrice, il.Quantity FROM InvoiceLine il JOIN Track t ON t.TrackId = il.TrackId JOIN Genre g ON g.GenreId = t.GenreId"
    for genre, price, qty in conn.execute(sql):
        revenue[genre] += cents(price * qty)
    total = sum(revenue.values())
    expected, running = [], 0
    for genre, v in sorted(revenue.items(), key=lambda kv: (-kv[1], kv[0])):
        running += v
        expected.append((genre, v / 100, round(100 * running / total, 1)))
    got = rows(conn, queries, 15)
    assert got == expected
    assert got[-1][2] == 100.0
    assert [r[2] for r in got] == sorted(r[2] for r in got)  # cumulative share never decreases
    assert next(i for i, r in enumerate(got, 1) if r[2] >= 80) == 6  # six genres cover 80% of revenue
