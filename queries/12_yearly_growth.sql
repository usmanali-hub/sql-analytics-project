-- question: How does revenue change year over year, and what is the running total?
-- notes: Yearly rather than monthly buckets on purpose: monthly revenue in this database is almost flat, so a month-on-month change would be a column of zeros. SUM() OVER an ordered frame gives the running total; LAG() fetches the previous year in the same row so the percentage change needs no self-join. The first year has no predecessor, so its change is NULL rather than an invented zero. The year is the first four characters of the timestamp text, which works the same in SQLite, DuckDB and PostgreSQL.
WITH yearly AS (
    SELECT SUBSTR(CAST(InvoiceDate AS VARCHAR), 1, 4) AS year,
           COUNT(*)                                    AS invoices,
           SUM(Total)                                  AS revenue
    FROM Invoice
    GROUP BY SUBSTR(CAST(InvoiceDate AS VARCHAR), 1, 4)
)
SELECT year,
       invoices,
       ROUND(revenue, 2)                                                          AS revenue,
       ROUND(SUM(revenue) OVER (ORDER BY year), 2)                                AS cumulative_revenue,
       ROUND(100.0 * (revenue - LAG(revenue) OVER (ORDER BY year))
             / LAG(revenue) OVER (ORDER BY year), 1)                              AS pct_change_vs_previous_year
FROM yearly
ORDER BY year;
