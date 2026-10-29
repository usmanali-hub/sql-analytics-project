-- question: What is cumulative revenue by month, and how does each month compare with the one before?
-- notes: Builds on the monthly buckets from question 5. SUM() OVER an ordered frame gives the running total; LAG() fetches the previous month in the same row so the change needs no self-join. The first month has no predecessor, so its change is NULL rather than a made-up zero. Gaps in the calendar are not filled, so LAG compares with the previous month that has invoices.
WITH monthly AS (
    SELECT strftime('%Y-%m', InvoiceDate) AS month,
           SUM(Total)                     AS revenue
    FROM Invoice
    GROUP BY strftime('%Y-%m', InvoiceDate)
)
SELECT month,
       ROUND(revenue, 2)                                        AS revenue,
       ROUND(SUM(revenue) OVER (ORDER BY month), 2)             AS cumulative_revenue,
       ROUND(revenue - LAG(revenue) OVER (ORDER BY month), 2)   AS change_vs_previous
FROM monthly
ORDER BY month;
