-- question: How concentrated is revenue across customers, split into spend quartiles?
-- notes: A CTE totals spend per customer, NTILE(4) ranks customers into quartiles (1 = biggest spenders), and the outer query sums each quartile. 59 customers do not divide evenly by 4, so the first quartiles hold 15 customers and the last two hold 14.
WITH customer_spend AS (
    SELECT CustomerId, SUM(Total) AS spend
    FROM Invoice
    GROUP BY CustomerId
),
ranked AS (
    SELECT CustomerId, spend,
           NTILE(4) OVER (ORDER BY spend DESC, CustomerId) AS quartile
    FROM customer_spend
)
SELECT quartile,
       COUNT(*)                                          AS customers,
       ROUND(SUM(spend), 2)                              AS revenue,
       ROUND(100.0 * SUM(spend) / (SELECT SUM(spend) FROM customer_spend), 1) AS pct_of_revenue
FROM ranked
GROUP BY quartile
ORDER BY quartile;
