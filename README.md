# sql-analytics-project

![CI](https://github.com/usmanali-hub/sql-analytics-project/actions/workflows/ci.yml/badge.svg)

SQL analytics on the [Chinook](https://github.com/lerocha/chinook-database) sample database, a
digital music store with 11 tables, 59 customers, 412 invoices and about 3,500 tracks. It covers
the whole path: loading the data read-only, documenting the schema and data quality, answering 15
business questions from joins through window functions, and proving the answers right with tests
that recompute them independently and run the same SQL on three database engines.

## Setup

```bash
pip install pytest          # the tooling itself uses only the standard library
PYTHONPATH=src python -m sqlproject check    # integrity check: file is sound, every foreign key resolves
PYTHONPATH=src python -m sqlproject docs     # regenerate docs/schema.md and docs/data_profile.md
PYTHONPATH=src python -m sqlproject report   # rerun all queries, rewrite results/ and docs/business_questions.md
PYTHONPATH=src pytest
```

The cross-engine tests need DuckDB and PostgreSQL, so `pip install -e ".[dev]"` installs everything
(without them those tests skip locally; in CI they are required).

The database ships in `data/Chinook.sqlite` (MIT licensed, see [`data/NOTICE.md`](data/NOTICE.md)).

## Schema

[Full diagram and column list](docs/schema.md) (Mermaid, rendered by GitHub), generated from the
database itself rather than drawn by hand, so it cannot drift from the data:

![Schema](docs/schema.svg)

`||--o{` means every child row has exactly one parent; `|o--o{` means the parent is optional. For
example `Track.AlbumId` is nullable, while `Invoice.CustomerId` is not.

## Data profile

[`docs/data_profile.md`](docs/data_profile.md) lists row counts and which columns contain NULLs.
Things worth knowing before writing queries:

- `Customer.Company` is NULL for 49 of 59 customers, so a join or filter on it silently drops most rows.
- `Invoice.BillingState` is NULL for 202 of 412 invoices (countries without states), so grouping by state needs `COALESCE`.
- `Track.Composer` is NULL for 977 of 3,503 tracks.
- `Employee.ReportsTo` has exactly one NULL: the top of the reporting tree.

## Business questions

Fifteen questions, one `.sql` file each in [`queries/`](queries/), with results in
[`results/`](results/) and a readable write-up in [`docs/business_questions.md`](docs/business_questions.md).

### What the data says

- **Revenue is concentrated by genre.** Six of 24 genres reach 80% of revenue and Rock alone is 35.5% ($826.65 of $2,328.60). Iron Maiden is the top artist at $138.60. (queries 3, 4, 15)
- **The USA is the top market**: 91 of 412 invoices and $523.06 (22.5%); Canada is second at $303.96. (1)
- **43% of the catalogue never sold**: 1,519 of 3,503 tracks. (7)
- **Yearly revenue is steady, not growing**: between $449 and $481 each year, with 2025 down 5.6% on 80 invoices instead of 83. (12)
- **Ties are real and matter.** Three UK customers tie for top spender at $37.62; `RANK()` returns all three where `ROW_NUMBER()` would have dropped two arbitrarily. (14)
- **Data quality notes**: two playlists are both named "Music" (ids 1 and 8) with identical sizes, a duplicate worth cleaning in a real system. (9)

Limits of the data: it is generated sample data. 58 of 59 customers placed exactly 7 invoices, monthly
revenue is almost flat (about $37.62 for most of the 60 months), and customer spend is only mildly
concentrated (top quartile 28.1% of revenue, bottom quartile 22.6%). Questions about repeat buyers,
seasonality or customer segments therefore show the technique, not a business insight.

### One query in full

Question 15, how many genres does it take to reach 80% of revenue (a running share with an explicit window frame):

```sql
WITH genre_revenue AS (
    SELECT g.Name AS genre, SUM(il.UnitPrice * il.Quantity) AS revenue
    FROM InvoiceLine AS il
    JOIN Track AS t ON t.TrackId = il.TrackId
    JOIN Genre AS g ON g.GenreId = t.GenreId
    GROUP BY g.GenreId, g.Name
)
SELECT genre,
       ROUND(revenue, 2) AS revenue,
       ROUND(100.0 * SUM(revenue) OVER (ORDER BY revenue DESC, genre
                                        ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW)
             / SUM(revenue) OVER (), 1) AS cumulative_pct
FROM genre_revenue
ORDER BY revenue DESC, genre;
```

| genre | revenue | cumulative_pct |
|---|---|---|
| Rock | 826.65 | 35.5 |
| Latin | 382.14 | 51.9 |
| Metal | 261.36 | 63.1 |
| Alternative & Punk | 241.56 | 73.5 |
| TV Shows | 93.53 | 77.5 |
| Jazz | 79.2 | 80.9 |

(first six of 24 rows; full output in [`results/15_genre_pareto.csv`](results/15_genre_pareto.csv))

### The queries

| # | Question | SQL techniques |
|---|---|---|
| 1 | Which countries generate the most revenue? | GROUP BY, SUM, AVG |
| 2 | Who are the top 10 customers? | INNER JOIN, GROUP BY |
| 3 | Which genres earn the most? | 3-table join, LEFT JOIN, COALESCE |
| 4 | Which artists bring in the most revenue? | 4-table join chain |
| 5 | How does revenue move month by month? | Date bucketing with SUBSTR over CAST |
| 6 | How much revenue does each support rep's customer base generate? | LEFT JOINs that keep reps with no customers |
| 7 | How many tracks have never been bought, by genre? | Anti-join (LEFT JOIN ... IS NULL) |
| 8 | How many customers placed 1, 2, 3... invoices? | Aggregate of an aggregate |
| 9 | How big is each playlist? | Link-table join, unit conversion |
| 10 | Who reports to whom? | Self-join |
| 11 | How concentrated is revenue across customer spend quartiles? | CTE, NTILE |
| 12 | How does revenue change year over year, with a running total? | Running SUM() OVER, LAG |
| 13 | Who are the top 2 artists in each of the five biggest genres? | Chained CTEs, ROW_NUMBER with PARTITION BY |
| 14 | Who is the top spender in each country with several customers? | RANK (keeps ties), COUNT() OVER |
| 15 | How many genres does it take to reach 80% of revenue? | Cumulative share, explicit ROWS frame |

### How the results are checked

SQL that runs is not necessarily SQL that is right. `tests/test_queries.py` recomputes every answer
in plain Python (dictionaries and loops over the raw tables) and compares. It also reconciles
totals: revenue from `Invoice.Total` equals revenue rebuilt from `InvoiceLine` ($2,328.60), and the
join-heavy questions (genres, artists, reps, months) each sum back to that same total, which proves
the joins lose no rows. Queries 11-15 are tested in `tests/test_advanced_queries.py` the same way, with money compared in integer cents. Another test fails if the committed `results/` or `docs/` are out of date.

```bash
PYTHONPATH=src python -m sqlproject report   # rerun all queries, rewrite results/ and docs/business_questions.md
```

## Portability

All 15 queries are checked on three engines: SQLite, DuckDB and PostgreSQL 16 (run in CI through
`pixeltable-pgserver`, a bundled PostgreSQL). `tests/test_portability.py` loads the same tables into
each and requires identical rows. Running them elsewhere found three real problems, all fixed:

- Four queries selected columns that were not in `GROUP BY`. SQLite tolerates that; the others reject it.
- `strftime` exists only in SQLite and DuckDB. Months and years are now `SUBSTR(CAST(InvoiceDate AS VARCHAR), 1, 7)`.
- PostgreSQL rejects `ROUND(x, 2)` on a floating-point column, so money columns are `NUMERIC` there, as in a real migration (Chinook declares them that way).

Not covered: MySQL and SQL Server. `CAST(... AS VARCHAR)` is not valid MySQL, so query 5 and 12 would need `CHAR`. Neither engine was run.

## Code

| Module | Purpose |
|---|---|
| `sqlproject.db` | Read-only connection, introspection of tables, columns and foreign keys, row and NULL counts, integrity check |
| `sqlproject.diagram` | Mermaid ER diagram and data-profile Markdown generated from that introspection |
| `sqlproject.runner` | Loads `queries/*.sql`, runs them read-only, writes CSV results and the Markdown report |

Design notes:

- **Read-only by default.** `connect()` opens the file with `mode=ro`, so an analysis query can never change the source data (a test tries to `DELETE` and expects failure).
- **Table names are validated against the database** before being placed in SQL, because identifiers cannot be bound as parameters.
- **Generated docs are tested.** One test fails if `docs/` is out of date with the database.

## Related

Smaller SQL experiments live in [ai-engineering-notes](https://github.com/usmanali-hub/ai-engineering-notes): window functions, index vs no index with `EXPLAIN QUERY PLAN`, recursive CTEs and parameterized queries from Python.
