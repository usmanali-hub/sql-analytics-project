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

## Code

| Module | Purpose |
|---|---|
| `sqlproject.db` | Read-only connection, introspection of tables, columns and foreign keys, row and NULL counts, integrity check |
| `sqlproject.diagram` | Mermaid ER diagram and data-profile Markdown generated from that introspection |

Design notes:

- **Read-only by default.** `connect()` opens the file with `mode=ro`, so an analysis query can never change the source data (a test tries to `DELETE` and expects failure).
- **Table names are validated against the database** before being placed in SQL, because identifiers cannot be bound as parameters.
- **Generated docs are tested.** One test fails if `docs/` is out of date with the database.

## Next

Joins and aggregations answering business questions (revenue by country, best customers, top artists),
then CTEs and window functions, with each query in its own `.sql` file and its result recorded.
