-- question: Which countries generate the most revenue?
-- notes: Single-table aggregation on Invoice. Average invoice value shows whether a country wins on volume or on basket size.
SELECT BillingCountry AS country,
       COUNT(*)                     AS invoices,
       ROUND(SUM(Total), 2)         AS revenue,
       ROUND(AVG(Total), 2)         AS avg_invoice
FROM Invoice
GROUP BY BillingCountry
ORDER BY revenue DESC, country
LIMIT 10;
