# sql-analytics-project

![CI](https://github.com/usmanali-hub/sql-analytics-project/actions/workflows/ci.yml/badge.svg)

SQL analytics on the [Chinook](https://github.com/lerocha/chinook-database) sample database, a
digital music store with 11 tables, 59 customers, 412 invoices and about 3,500 tracks. The repo
starts with the groundwork that every analysis depends on: loading the data safely, understanding
its schema, and profiling its quality. Business questions in plain SQL build on top of it.

## Setup

```bash
pip install pytest          # only for the tests; the tooling uses the standard library
PYTHONPATH=src python -m sqlproject check    # integrity check: file is sound, every foreign key resolves
PYTHONPATH=src python -m sqlproject docs     # regenerate docs/schema.md and docs/data_profile.md
PYTHONPATH=src pytest
```

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

Fifteen questions, ten with joins and aggregations and five with CTEs and window functions, one `.sql` file each in [`queries/`](queries/),
with results in [`results/`](results/) and a readable write-up in
[`docs/business_questions.md`](docs/business_questions.md):

| # | Question | SQL techniques |
|---|---|---|
| 1 | Which countries generate the most revenue? | GROUP BY, SUM, AVG |
| 2 | Who are the top 10 customers? | INNER JOIN, GROUP BY |
| 3 | Which genres earn the most? | 3-table join, LEFT JOIN, COALESCE |
| 4 | Which artists bring in the most revenue? | 4-table join chain |
| 5 | How does revenue move month by month? | strftime date bucketing |
| 6 | How much revenue does each support rep's customer base generate? | LEFT JOINs that keep reps with no customers |
| 7 | How many tracks have never been bought, by genre? | Anti-join (LEFT JOIN ... IS NULL) |
| 8 | How many customers placed 1, 2, 3... invoices? | Aggregate of an aggregate |
| 9 | How big is each playlist? | Link-table join, unit conversion |
| 10 | Who reports to whom? | Self-join |
| 11 | How concentrated is revenue across customer spend quartiles? | CTE, NTILE |
| 12 | What is cumulative revenue by month, and the change on the month before? | Running SUM() OVER, LAG |
| 13 | Who are the top 2 artists in each of the five biggest genres? | Chained CTEs, ROW_NUMBER with PARTITION BY |
| 14 | Who is the top spender in each country with several customers? | RANK (keeps ties), COUNT() OVER |
| 15 | How many genres does it take to reach 80% of revenue? | Cumulative share, explicit ROWS frame |

Some of what the results show (all from `results/`):

- The USA is the top market with 91 of 412 invoices and $523.06 of $2,328.60 in revenue (22.5%); Canada is second at $303.96.
- Rock is the top genre at $826.65, about 35.5% of revenue; Iron Maiden is the top artist at $138.60.
- 1,519 of 3,503 tracks (43%) have never been bought.
- Purchasing is almost uniform: 58 of 59 customers placed exactly 7 invoices and one placed 6. That points to generated sample data, so patterns like "repeat buyers" cannot be drawn from it.
- Two playlists are both named "Music" (ids 1 and 8) with identical sizes, a duplicate worth cleaning in a real system.
- Customer spend is only mildly concentrated: the top quartile of customers brings in 28.1% of revenue and the bottom quartile 22.6%. Again, sample data.
- Revenue is almost flat month to month (about $37.62 for most of the 60 months), so the growth query shows steady totals, not a trend.
- Revenue is concentrated by genre, though: six of 24 genres reach 80% of revenue, and Rock alone is 35.5%.
- Three UK customers tie for top spender at $37.62; `RANK()` returns all three, where `ROW_NUMBER()` would have dropped two arbitrarily.

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

The queries stick to standard SQL apart from `strftime` in query 5. `tests/test_portability.py` loads the same tables into DuckDB and requires every query to return the same rows as SQLite. That check found a real problem: four queries selected columns that were not in `GROUP BY`, which SQLite tolerates but stricter engines (PostgreSQL, DuckDB) reject. They now group by every selected column, with identical results.

Not covered: query 5's month bucketing uses `strftime`, which DuckDB happens to share; PostgreSQL and MySQL would need `to_char` and `DATE_FORMAT`. Neither was run here.

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

## Next

CTEs and window functions for ranking and running totals, a query-plan comparison with and without an index, and parameterized queries from Python.
