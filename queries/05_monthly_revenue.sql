-- question: How does revenue move month by month?
-- notes: The first seven characters of the timestamp text ("2021-01") form a year-month bucket; SUBSTR over a CAST is used instead of strftime because it behaves the same in SQLite, DuckDB and PostgreSQL. Months without invoices do not appear (there is no calendar table), so gaps must be read as zero.
SELECT SUBSTR(CAST(InvoiceDate AS VARCHAR), 1, 7) AS month,
       COUNT(*)                       AS invoices,
       ROUND(SUM(Total), 2)           AS revenue
FROM Invoice
GROUP BY month
ORDER BY month;
